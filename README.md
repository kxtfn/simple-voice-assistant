# 🧠 Voice Assistant for Raspberry Pi Zero 2 W

A lightweight voice assistant tailored specifically for Ukrainian users and built for the Raspberry Pi Zero 2 W. It listens for a wake word, records voice input, transcribes Ukrainian speech, generates context-aware responses using GPT, and replies with synthesized voice. RGB LEDs visually indicate the assistant’s current state.
## How It Works
1. The assistant listens for the wake-word using Porcupine.
2. When triggered, it records audio input.
3. It transcribes the recording with Whisper (language='uk').
4. The transcript is passed to GPT for a response.
5. The response is synthesized via gTTS and played back.
6. LEDs change color to indicate current status (waiting, listening, replying).

## 🔌 Electrical Schematic

The voice assistant circuit is built around the Raspberry Pi Zero 2 W and includes:

### Components:
- **Microphone (soldered directly to the backside of board, connecting to the USB test pads)**
- **PCM5102A** DAC for high-quality audio output
- **PAM8403** stereo amplifier
- **Speaker**
- **2x WS2812 RGB LEDs** for status indication
- **External 5V power** for stable LED and amplifier operation
![Alt text](https://i.ibb.co/Kj319F7G/image.png)

## Features

- Wake-word detection using **Porcupine**
- Audio recording via **sounddevice**
- Speech recognition with **OpenAI Whisper**
- GPT-based text response via **OpenAI API**
- Text-to-speech using **gTTS**
- RGB LED control (WS2812 / NeoPixels)

## Requirements

- Raspberry Pi Zero 2 W
- Internet connection
- Python 3.10+

## Installation

### 1. Flash the system

Use **Raspberry Pi Imager** to flash **Raspberry Pi OS Lite**  
During setup, enable SSH and configure Wi-Fi.

### 2. After first boot

Run the following commands:

```bash
sudo apt install -y python3-pip python3-dev build-essential portaudio19-dev \
libffi-dev libasound2-dev libnss3 libatlas-base-dev libopenblas-dev liblapack-dev ffmpeg

sudo apt update --fix-missing
pip install pyaudio --fix-missing
pip install -r requirements.txt --fix-missing
 
If youre using HiFiBerry DAC:
sudo nano /boot/firmware/config.txt
dtoverlay=hifiberry-dac
```

### 3 Autostart the assistant

Make the script executable:
```chmod +x assistant/assistant.py```

Create a systemd service:
```sudo nano /etc/systemd/system/assistant.service```

Paste this configuration:
```
[Unit]
Description=Voice Assistant Autostart (runs as root)
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/raspberrypi/assistant/assistant.py
WorkingDirectory=/home/raspberrypi/assistant
StandardOutput=inherit
StandardError=inherit
Restart=always

[Install]
WantedBy=multi-user.target
```
Enable the service:
```
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable assistant.service
sudo systemctl start assistant.service
```

### 🧱 Enclosure (3D-Printed Case)

The custom case for the assistant was designed in **Fusion 360** and 3D-printed using a **Creality K1C** printer.  
Slicing and preparation were done using specialized software tailored for the K1C.

The 3D model is available in the repository:
- `model.f3d` – Fusion 360 source file

![Alt text](https://i.ibb.co/0bTkgzD/3d.png)

### Notes
- Insert your OpenAI and pvpocrupine API keys inside assistant.py.
- Ensure the wakeup.ppn file corresponds to your chosen wake-word (in-project file contains the word "Wake-up".
- Check your microphone index (input_device_index = 1 by default).
- Use mpg123 for audio playback (required).
