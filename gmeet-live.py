import asyncio
import os
import subprocess
import click
import datetime
import json
from time import sleep
import logging
import websockets
from websockets.exceptions import ConnectionClosedOK
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
import requests
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Audio Configuration for Gladia
SAMPLE_RATE = 16000

STREAMING_CONFIGURATION = {
   # === Audio Basics ===
   "encoding": "wav/pcm",     # Raw audio in WAV format
   "sample_rate": SAMPLE_RATE,  # How many audio snapshots per second
   "bit_depth": 16,          # Audio quality - 16 is standard for speech
   "channels": 1,            # One audio channel (mono) to keep it simple
   
   "endpointing": 0.3,       # Waits for 0.3s of silence before saying "that's the end of that sentence"
   "maximum_duration_without_endpointing": 30,  # Splits things up if someone talks for 30s straight
   
   "language_config": {
       "languages": ["en", "fr", "es", "ar"],  # English, French, Spanish, and Arabic
       "code_switching": True    # Can handle people switching languages mid-conversation
   },
   
    # === Audio Cleanup ===
   "pre_processing": {
       "audio_enhancer": True,           # Cleans up the audio, gets rid of background noise
       "speech_threshold": 0.95          # Sensitivity of voice detection for background noise (default value 0.46, that you can change)
   },
   
   # === Smart Features ===
   "realtime_processing": {
       "words_accurate_timestamps": True,  # Knows exactly when each word was said
       "custom_vocabulary": True,          # Helps catch special words
       "custom_vocabulary_config": {
           "vocabulary": [                 
               "Gladia",                   
               "Léo Idir",                
               "ASR"                      
           ]
       },
       "named_entity_recognition": True,  # Spots names, places, organizations
       "sentiment_analysis": True        # Figures out if someone sounds happy/angry/etc
   },
   
    # === Summary ===
    "post_processing": {
        "summarization": True,
        "summarization_config": {"type": "bullet_points"}, # Available options: general, bullet_points, concise
        "chapterization": True
    },
   # === Updates We Want ===
   # What info we want to get back while it's running
   "messages_config": {
       "receive_partial_transcripts": True,      # Get text as soon as someone speaks
       "receive_final_transcripts": True,        # Get the final, double-checked version
       "receive_speech_events": True,            # Know when someone starts/stops talking
       "receive_pre_processing_events": True,    # Know when it's cleaning up the audio
       "receive_realtime_processing_events": True,  # Updates about detecting names/sentiment
       "receive_post_processing_events": True,   # Know when it's doing final touchups
       "receive_acknowledgments": True,          # Confirm it got our audio okay
       "receive_lifecycle_events": True,         # General status updates
       "receive_errors": True                    # Let us know if something goes wrong
   }
}

def init_live_session(api_key: str):
    # Initialize a live transcription session with Gladia
    logger.info(f"Our streaming configuration is: {STREAMING_CONFIGURATION}")
    response = requests.post(
        "https://api.gladia.io/v2/live",
        headers={"X-Gladia-Key": api_key},
        json=STREAMING_CONFIGURATION,
        timeout=3
    )
    if not response.ok:
        logger.error(f"Failed to initialize live session: {response.text}")
        raise Exception("Failed to initialize live session")
    return response.json()

async def run_command_async(command):
    # Run a shell command asynchronously
    process = await asyncio.create_subprocess_shell(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return await process.communicate()

async def google_sign_in(email, password, driver):
    # Handle Google account sign-in process
    try:
        logger.info("Starting Google sign-in process")
        driver.get("https://accounts.google.com")
        await asyncio.sleep(1)

        email_field = driver.find_element(By.NAME, "identifier")
        email_field.send_keys(email)
        await asyncio.sleep(2)

        driver.find_element(By.ID, "identifierNext").click()
        await asyncio.sleep(3)

        password_field = driver.find_element(By.NAME, "Passwd")
        password_field.click()
        password_field.send_keys(password + Keys.RETURN)
        await asyncio.sleep(5)
        logger.info("Successfully signed in to Google")
    except NoSuchElementException as e:
        logger.error(f"Failed to sign in: {str(e)}")
        raise

async def setup_audio_drivers():
    # Configure virtual audio drivers for recording
    logger.info("Setting up virtual audio drivers")
    commands = [
        "sudo rm -rf /var/run/pulse /var/lib/pulse /root/.config/pulse",
        "sudo pulseaudio -D --verbose --exit-idle-time=-1 --system --disallow-exit >> /dev/null 2>&1",
        'sudo pactl load-module module-null-sink sink_name=DummyOutput sink_properties=device.description="Virtual_Dummy_Output"',
        'sudo pactl load-module module-null-sink sink_name=MicOutput sink_properties=device.description="Virtual_Microphone_Output"',
        "sudo pactl load-module module-virtual-source source_name=VirtualMic",
        "sudo pactl set-default-sink MicOutput",
        "sudo pactl set-default-source MicOutput.monitor"
    ]
    
    for cmd in commands:
        await run_command_async(cmd)

async def handle_media_controls(driver):
    #Simple function to turn off both microphone and camera.
    try:
        initial_buttons = [
            "//span[contains(text(), 'Continue without microphone')]",
            "//span[contains(text(), 'Continue without camera')]"
        ]
        
        for button in initial_buttons:
            try:
                driver.find_element(By.XPATH, button).click()
                await asyncio.sleep(1)
            except:
                continue
    except Exception as e:
        logger.info(f"No initial popups found: {e}")

    # Then handle microphone
    try:
        microphone_off = driver.find_element(By.XPATH, "//div[@aria-label='Turn off microphone']")
        microphone_off.click()
        driver.save_screenshot("screenshots/disable_microphone.png")
        logger.info("Microphone turned off")
    except:
        logger.info("Microphone already off or not found")

    await asyncio.sleep(1)  # Short pause between actions

    # Then handle camera
    try:
        camera_off = driver.find_element(By.XPATH, "//div[@aria-label='Turn off camera']")
        camera_off.click()
        driver.save_screenshot("screenshots/disable_camera.png")
        logger.info("Camera turned off")
    except:
        logger.info("Camera already off or not found")
        
async def join_meeting(driver):
    #Attempt to join the meeting
    max_time = datetime.datetime.now() + datetime.timedelta(
        minutes=int(os.getenv("MAX_WAITING_TIME_IN_MINUTES", 5))
    )
    
    while datetime.datetime.now() < max_time:
        try:
            join_button = driver.find_element(By.XPATH, "//span[contains(text(), 'Ask to join')]")
            join_button.click()
            await asyncio.sleep(2)
            driver.save_screenshot("screenshots/joining.png")
            logger.info("Meeting joined")
            return True
        except NoSuchElementException:
            await asyncio.sleep(5)
            logger.info("Waiting to join meeting...")
    
    logger.error("Failed to join meeting within the timeout period")
    return False

async def capture_and_stream_audio(websocket):
    # Capture audio using ffmpeg and stream to Gladia
    logger.info("Starting audio capture")
    
    # FFmpeg command to capture audio and output raw PCM
    ffmpeg_command = (
        f"ffmpeg -y -f pulse -i MicOutput.monitor "
        f"-acodec pcm_s16le -ac 1 -ar {SAMPLE_RATE} "
        f"-f s16le -"  # Output raw PCM to stdout
    )

    process = await asyncio.create_subprocess_shell(
        ffmpeg_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    chunk_size = 3200  # Same as original FRAMES_PER_BUFFER
    try:
        while True:
            # Read chunk of raw audio data
            audio_chunk = await process.stdout.read(chunk_size)
            if not audio_chunk:
                break

            # Encode and send to Gladia
            data = base64.b64encode(audio_chunk).decode("utf-8")
            json_data = json.dumps({"type": "audio_chunk", "data": {"chunk": str(data)}})
            await websocket.send(json_data)
            await asyncio.sleep(0.1)  # Control streaming rate
    except Exception as e:
        logger.error(f"Error in audio capture: {str(e)}")
    finally:
        process.terminate()
        try:
            await process.wait()
        except:
            pass

async def handle_transcription_messages(websocket):
    # Process transcription messages from Gladia
    try:
        async for message in websocket:
            content = json.loads(message)
            
            if content["type"] == "transcript" and content["data"]["is_final"]:
                start_time = content["data"]["utterance"]["start"]
                end_time = content["data"]["utterance"]["end"]
                text = content["data"]["utterance"]["text"].strip()
                logger.info(f"{start_time:.2f}s --> {end_time:.2f}s | {text}")
                
                # Save transcription to file
                with open("transcriptions/live_transcript.txt", "a") as f:
                    f.write(f"{start_time:.2f}s --> {end_time:.2f}s | {text}\n")
            
            # Check for both possible final transcript message types
            elif content["type"] in ["final_transcript", "post_processing_result"]:
                logger.info(f"Received final transcript of type: {content['type']}")
                
                # Save complete transcript JSON
                with open("transcriptions/final_transcript.json", "w") as f:
                    json.dump(content, f, indent=2)
                
                # Save full transcript text
                if "transcription" in content and "full_transcript" in content["transcription"]:
                    logger.info("Saving full transcript")
                    with open("transcriptions/full_transcript.txt", "w") as f:
                        f.write(content["transcription"]["full_transcript"])
                
                # Save summary if available
                if "summarization" in content and content["summarization"].get("results"):
                    logger.info("Saving summary")
                    with open("transcriptions/summary.txt", "w") as f:
                        f.write(content["summarization"]["results"])
                
                # Save chapters if available
                if "chapters" in content and content["chapters"].get("results"):
                    logger.info("Saving chapters")
                    with open("transcriptions/chapters.json", "w") as f:
                        json.dump(content["chapters"]["results"], f, indent=2)
                
                return  
    except Exception as e:
        logger.error(f"Error processing transcription: {str(e)}")

async def join_meet():
    # Main function to handle the Google Meet recording process
    meet_link = os.getenv("GMEET_LINK", "https://meet.google.com/dau-pztc-yad")
    logger.info(f"Starting recorder for {meet_link}")

    # Create transcriptions directory if it doesn't exist
    os.makedirs("transcriptions", exist_ok=True)
    
    # Clean up screenshots directory
    if os.path.exists("screenshots"):
        for f in os.listdir("screenshots"):
            os.remove(f"screenshots/{f}")
    else:
        os.mkdir("screenshots")
        
    # Setup audio drivers
    await setup_audio_drivers()

    # Configure Chrome options
    options = uc.ChromeOptions()
    chrome_args = [
        "--use-fake-ui-for-media-stream",
        "--window-size=1920x1080",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-application-cache",
        "--disable-dev-shm-usage"
    ]
    for arg in chrome_args:
        options.add_argument(arg)

    # Initialize Chrome driver
    driver = uc.Chrome(service_log_path="chromedriver.log", use_subprocess=False, options=options)
    driver.set_window_size(1920, 1080)

    # Get credentials
    email = os.getenv("GMAIL_USER_EMAIL", "")
    password = os.getenv("GMAIL_USER_PASSWORD", "")
    gladia_api_key = os.getenv("GLADIA_API_KEY", "")

    if not all([email, password, gladia_api_key]):
        logger.error("Missing required credentials")
        return

    try:
        # Sign in and join meet
        await google_sign_in(email, password, driver)
        driver.get(meet_link)

        # Grant necessary permissions
        driver.execute_cdp_cmd(
            "Browser.grantPermissions",
            {
                "origin": meet_link,
                "permissions": [
                    "geolocation",
                    "audioCapture",
                    "displayCapture",
                    "videoCapture",
                    "videoCapturePanTiltZoom",
                ]
            }
        )

        # Handle initial setup and media controls
        await handle_media_controls(driver)
        if not await join_meeting(driver):
            return

        # Initialize live transcription session
        session = init_live_session(gladia_api_key)
        
        # Start live transcription
        async with websockets.connect(session["url"]) as websocket:
            logger.info("Starting live transcription")
            
            # Create tasks for audio streaming and transcription handling
            audio_task = asyncio.create_task(capture_and_stream_audio(websocket))
            transcription_task = asyncio.create_task(handle_transcription_messages(websocket))
            
            # Wait for the specified duration
            duration = int(os.getenv("DURATION_IN_MINUTES", 15)) * 60
            await asyncio.sleep(duration)
            
            # Stop audio capture first
            logger.info("Stopping audio capture...")
            audio_task.cancel()
            
            # Send stop signal to Gladia
            await websocket.send(json.dumps({"type": "stop_recording"}))
            
            # Wait for final transcript (add timeout to prevent infinite wait)
            try:
                logger.info("Waiting for final transcript...")
                await asyncio.wait_for(transcription_task, timeout=120)  # 120 second timeout
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for final transcript")
            finally:
                transcription_task.cancel()
    except Exception as e:
        logger.error(f"Error during meeting: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    click.echo("Starting Google Meet recorder with live transcription...")
    asyncio.run(join_meet())
    click.echo("Finished recording Google Meet.")