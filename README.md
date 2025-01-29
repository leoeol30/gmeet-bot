# 🎥 Gladia Transcription - GMeet Bot

<div align="center">

*A technical implementation demonstrating Gladia's real-time and prerecorded transcription APIs with Google Meet*


</div>

A demonstration showing how to use both Gladia's real-time and prerecorded transcription APIs with Google Meet. The project supports two modes:
- Real-time transcription with live output during the meeting
- Prerecorded transcription with speaker diarization after the meeting

> ⚠️ **Note**: This is a technical demonstration and not intended for production use.

## 🔑 Key Technical Aspects
- Dual transcription modes (real-time and prerecorded)
- Integration with Gladia's V2 APIs
- Virtual audio capture for Google Meet
- Automated session management

## 🚀 Build Options

```bash
# Real-time Transcription Mode
docker build -t gmeet-live -f Dockerfile.live .

# Prerecorded Transcription Mode
docker build -t gmeet-prerecorded -f Dockerfile.prerecorded .
```

## 💻 Implementation Examples

### Real-time Transcription Mode
```bash
docker run -it \
    -e GMEET_LINK="https://meet.google.com/my-gmeet-id" \
    -e GMAIL_USER_EMAIL="myuser1234@gmail.com" \
    -e GMAIL_USER_PASSWORD="my_gmail_password" \
    -e DURATION_IN_MINUTES=1 \
    -e GLADIA_API_KEY="YOUR_GLADIA_API_KEY" \
    -e MAX_WAIT_TIME_IN_MINUTES=2 \
    -v $PWD/recordings:/app/recordings \
    -v $PWD/screenshots:/app/screenshots \
    -v $PWD/transcriptions:/app/transcriptions \
    gmeet-live
```

### Prerecorded Transcription Mode
```bash
docker run -it \
    -e GMEET_LINK="https://meet.google.com/my-gmeet-id" \
    -e GMAIL_USER_EMAIL="myuser1234@gmail.com" \
    -e GMAIL_USER_PASSWORD="my_gmail_password" \
    -e DURATION_IN_MINUTES=1 \
    -e GLADIA_API_KEY="YOUR_GLADIA_API_KEY" \
    -e GLADIA_DIARIZATION=true \
    -e MAX_WAIT_TIME_IN_MINUTES=2 \
    -v $PWD/recordings:/app/recordings \
    -v $PWD/screenshots:/app/screenshots \
    -v $PWD/transcriptions:/app/transcriptions \
    gmeet-prerecorded
```

## 🌟 Features
- Dual transcription modes (real-time and prerecorded)
- Speaker diarization in prerecorded mode
- Multi-language support (English, French, Spanish, Arabic)
- Virtual audio recording using PulseAudio
- Screen capture using Xscreen
- Automated meeting attendance

---

Created to demonstrate both real-time and prerecorded transcription capabilities of [Gladia](https://gladia.io)'s APIs.
