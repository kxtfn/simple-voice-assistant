import openai 
import sounddevice as sd 
import numpy as np 
import wave 
import os 
import asyncio 
from concurrent.futures import ThreadPoolExecutor 
import pvporcupine 
import pyaudio 
import time 
from gtts import gTTS
from gpiozero import RGBLED 
from scipy.signal import resample 
from rpi_ws281x import PixelStrip, Color 
import subprocess

def measure_time(func):
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print(f"⏱ Function {func.__name__} ended for {end_time - start_time:.2f} seconds") 
        return result
    return wrapper


LED_COUNT = 2
LED_PIN = 13
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 64
LED_INVERT = False
LED_CHANNEL = 1

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                   LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

def set_led_color(color):
    for i in range(LED_COUNT):
        strip.setPixelColor(i, color)
    strip.show()


API_KEY = "TOKEN"
client = openai.OpenAI(api_key=API_KEY)

SAMPLE_RATE = 48000
DURATION = 4
INPUT_FILE = "voice_input.wav"
OUTPUT_FILE = "response_audio.mp3"

executor = ThreadPoolExecutor(max_workers=4) 

@measure_time
async def record_audio_async(filename, duration, sample_rate):
    loop = asyncio.get_event_loop()
    print("🎙 Recording started") 
    set_led_color(Color(255, 0, 0))  
    
    def _record():
        audio_data = sd.rec(int(sample_rate * duration), 
                          samplerate=sample_rate, 
                          channels=1, 
                          dtype=np.int16)
        sd.wait()
        return audio_data
    
    audio_data = await loop.run_in_executor(executor, _record)
    
    def _save():
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())
    
    await loop.run_in_executor(executor, _save)
    print("✅ Recording completed") 
    return filename

@measure_time 
async def play_audio_async(filename):
    set_led_color(Color(0, 255, 0))  
    def _play():
        import time
        print("🔹 Preparing")
        t0 = time.time()

        subprocess.run(['mpg123', filename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        t1 = time.time()
        print(f"🔹 subprocess.run() - {t1 - t0:.2f} s")

    try:
        print("▶️")
        await asyncio.get_event_loop().run_in_executor(executor, _play)
        print("✅")
    except Exception as e:
        print(f"🔇{e}")


@measure_time
async def transcribe_audio_async(filename):
    def _transcribe():
        with open(filename, "rb") as audio_file:
            return client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="uk"
            )
    return await asyncio.get_event_loop().run_in_executor(executor, _transcribe)

@measure_time
async def get_gpt_response_async(text):
    def _generate():
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": text}]
        )
        return response.choices[0].message.content
    
    return await asyncio.get_event_loop().run_in_executor(executor, _generate)

@measure_time
async def generate_speech_async(text):
    def _generate():
        tts = gTTS(text=text, lang='uk')
        tts.save("voice.mp3")  
        return "voice.mp3"

    output_file = await asyncio.get_event_loop().run_in_executor(executor, _generate)
    await play_audio_async(output_file)

@measure_time
async def listen_for_wakeword_async():
    print("🟢 Waiting wake word...")  
    set_led_color(Color(0, 0, 255))  
    def _listen():
        porcupine = pvporcupine.create(
            access_key="TOKEN",
            keyword_paths=[r"/home/raspberrypi/assistant/wakeup.ppn"]
        )

        DEVICE_SAMPLE_RATE = 48000
        frames_per_buffer = int(porcupine.frame_length * (DEVICE_SAMPLE_RATE / 16000))

        pa = pyaudio.PyAudio()

        input_device_index = 1

        stream = pa.open(
            rate=DEVICE_SAMPLE_RATE,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=input_device_index,
            frames_per_buffer=frames_per_buffer
        )

        try:
            while True:
                data = stream.read(frames_per_buffer, exception_on_overflow=False)
                audio_48k = np.frombuffer(data, dtype=np.int16)

                audio_16k = resample(audio_48k, porcupine.frame_length)
                audio_16k = np.round(audio_16k).astype(np.int16)

                keyword_index = porcupine.process(audio_16k)

                if keyword_index >= 0:
                        print("✅ Detected wake word") 
                        break
        finally:
            stream.stop_stream()
            stream.close()
            porcupine.delete()
            pa.terminate()

    await asyncio.get_event_loop().run_in_executor(executor, _listen)

@measure_time
async def main_loop_async():
    while True:
        await listen_for_wakeword_async()
        set_led_color(Color(0, 0, 0)) 
        print('\a') 

        filename = await record_audio_async(INPUT_FILE, DURATION, SAMPLE_RATE)
        
        transcription = await transcribe_audio_async(filename)
        user_text = transcription.text

        print(f"🗨 Запит: {user_text}") 

        gpt_response = await get_gpt_response_async(user_text + " Відповідай українською.")
        print(f"🤖 Відповідь: {gpt_response}") 

        await generate_speech_async(gpt_response)

if __name__ == "__main__":
    asyncio.run(main_loop_async())