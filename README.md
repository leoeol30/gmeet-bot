# GMeet Bot

Record and transcribe Google Meet meetings from a container using virtual sound card (PulseAudio) and screen recording (Xscreen). This project demonstrates recording sessions without a physical sound card using audio loop sink while avoiding detection by the meeting provider (Google Meet).

One of the main challenges addressed is capturing audio without triggering meeting provider security measures. The solution uses virtual devices and audio loop sink.

This project is a proof of concept with limited support and is not meant for production grade usage.

## Build

### Live Transcription Mode
```bash
docker build -t gmeet-live -f Dockerfile.live .
```

### Pre-recorded Mode
```bash
docker build -t gmeet-prerecorded -f Dockerfile.prerecorded .
```

## Usage

### Live Transcription
```bash
docker run -it \
    -e GMEET_LINK=https://meet.google.com/my-gmeet-id \
    -e GMAIL_USER_EMAIL=myuser1234@gmail.com \
    -e GMAIL_USER_PASSWORD=my_gmail_password \
    -e DURATION_IN_MINUTES=1 \ #duration of the meeting to record
    -e GLADIA_API_KEY=YOUR_GLADIA_API_KEY \
    -e MAX_WAIT_TIME_IN_MINUTES=2 \ #max wait time in the lobby
    -v $PWD/recordings:/app/recordings \ # local storage for the recording
    -v $PWD/screenshots:/app/screenshots \ # local storage for intermediate bot screenshots
    -v $PWD/transcriptions:/app/transcriptions \ # local storage for transcriptions
    gmeet-live
```

### Pre-recorded Mode with Diarization
```bash
docker run -it \
    -e GMEET_LINK=https://meet.google.com/my-gmeet-id \
    -e GMAIL_USER_EMAIL=myuser1234@gmail.com \
    -e GMAIL_USER_PASSWORD=my_gmail_password \
    -e DURATION_IN_MINUTES=1 \ #duration of the meeting to record
    -e GLADIA_API_KEY=YOUR_GLADIA_API_KEY \
    -e GLADIA_DIARIZATION=true \
    -e MAX_WAIT_TIME_IN_MINUTES=2 \ #max wait time in the lobby
    -v $PWD/recordings:/app/recordings \ # local storage for the recording
    -v $PWD/screenshots:/app/screenshots \ # local storage for intermediate bot screenshots
    -v $PWD/transcriptions:/app/transcriptions \ # local storage for transcription
    gmeet-prerecorded
```

## Features
- Live transcription with real-time output
- Pre-recorded mode with diarization support
- Multi-language support (English, French, Spanish, Arabic)
- Virtual audio recording using PulseAudio
- Screen capture using Xscreen
- Automated meeting attendance