# 🤖 Google Meet Bot with Gladia Transcription

<div align="center">
<em>An automated solution for capturing and transcribing Google Meet sessions using Gladia's powerful transcription APIs</em>
</div>

## 📝 Overview

This project demonstrates an automated bot that joins Google Meet sessions and leverages Gladia's transcription capabilities. It supports two distinct transcription approaches:

- **Real-time Transcription**: Live capture and transcription during the meeting
- **Post-meeting Processing**: Full recording with speaker diarization after the meeting concludes

> ⚠️ **Important**: This implementation serves as a technical demonstration and proof of concept. It is not recommended for production environments without additional development and security considerations.

## 🌟 Features

- Automated Google Meet session joining
- Dual transcription modes with different use cases
- Integration with Gladia's V2 Transcription APIs
- Virtual audio capture system
- Support for speaker diarization (in prerecorded mode)
- Flexible recording duration control
- Optional screenshot capture

## 🛠️ Build Instructions

Choose your build configuration based on your transcription needs:

```bash
# For real-time transcription capabilities
docker build -t gmeet-live -f Dockerfile.live .

# For post-meeting transcription with speaker diarization
docker build -t gmeet-prerecorded -f Dockerfile.prerecorded .
```

## 🚀 Usage Examples

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
    gmeet-prerecorded
```

## 📁 Directory Structure

The bot creates and manages several directories:
- `/app/recordings`: Stores meeting audio recordings
- `/app/screenshots`: Contains captured meeting screenshots
- `/app/transcriptions`: Holds the generated transcription files

## 🔍 Use Cases

- **Real-time Mode**: Ideal for live captioning, immediate transcription needs.
- **Prerecorded Mode**: Better for accurate speaker identification, high-quality transcription, and detailed post-meeting analysis

---
Created by Léo Idir, based on [gladia-samples Google Meet Bot](https://github.com/gladiaio/gladia-samples/tree/main/integrations-examples/gmeet-bot)
