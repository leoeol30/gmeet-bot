import asyncio
import os
import subprocess
import click
import datetime
import requests
import json
from time import sleep
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def make_request(url, headers, method="GET", data=None, files=None):
    # Make a GET or POST request to the API and return JSON response
    try:
        if method == "POST":
            response = requests.post(url, headers=headers, json=data, files=files)
        else:
            response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise

async def run_command_async(command):
    """ Run a shell command asynchronously """
    process = await asyncio.create_subprocess_shell(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return await process.communicate()

async def google_sign_in(email, password, driver):
    """ Handle Google account sign-in process """
    try:
        logger.info("Starting Google sign-in process")
        driver.get("https://accounts.google.com")
        await asyncio.sleep(1)

        # Enter email
        email_field = driver.find_element(By.NAME, "identifier")
        email_field.send_keys(email)
        driver.save_screenshot("screenshots/email.png")
        await asyncio.sleep(2)

        # Click next and handle password
        driver.find_element(By.ID, "identifierNext").click()
        await asyncio.sleep(3)
        driver.save_screenshot("screenshots/password.png")

        # Enter password
        password_field = driver.find_element(By.NAME, "Passwd")
        password_field.click()
        password_field.send_keys(password + Keys.RETURN)
        await asyncio.sleep(5)
        driver.save_screenshot("screenshots/signed_in.png")
        logger.info("Successfully signed in to Google")
    except NoSuchElementException as e:
        logger.error(f"Failed to sign in: {str(e)}")
        raise

async def setup_audio_drivers():
    """Configure virtual audio drivers for recording"""
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

async def join_meet():
    """Main function to handle the Google Meet recording process"""
    meet_link = os.getenv("GMEET_LINK", "https://meet.google.com/dau-pztc-yad")
    logger.info(f"Starting recorder for {meet_link}")

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

    # Validate credentials
    if not email or not password:
        logger.error("No email or password specified")
        return
    if not gladia_api_key:
        logger.error("No Gladia API key specified")
        logger.info("Create one for free at https://app.gladia.io/")
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
        driver.save_screenshot("screenshots/initial.png")
        await handle_media_controls(driver)
        await join_meeting(driver)

        # Start recording
        duration = int(os.getenv("DURATION_IN_MINUTES", 15)) * 60
        await record_meeting(duration)

        # Handle transcription
        await handle_transcription(gladia_api_key)

    finally:
        driver.quit()

async def handle_media_controls(driver):
    """Handle microphone and camera controls"""
    try:
        # Disable microphone
        #driver.find_element(By.XPATH, "//span[contains(text(), 'Continue without microphone')]").click()
        #await asyncio.sleep(2)
        driver.find_element(By.XPATH, "//div[@aria-label='Turn off microphone']").click()
        driver.save_screenshot("screenshots/disable_microphone.png")
        logger.info("Microphone disabled")
    except NoSuchElementException:
        logger.info("No microphone to disable")

    try:
        # Disable camera
        driver.find_element(By.XPATH, "//div[@aria-label='Turn off camera']")
        driver.save_screenshot("screenshots/disable_camera.png")
        logger.info("Camera disabled")
    except NoSuchElementException:
        logger.info("No camera to disable")

async def join_meeting(driver):
    """Attempt to join the meeting"""
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

async def record_meeting(duration):
    """Record the meeting using ffmpeg"""
    logger.info("Starting recording")
    record_command = (
        f"ffmpeg -y -video_size 1920x1080 -framerate 30 -f x11grab -i :99 "
        f"-f pulse -i MicOutput.monitor -t {duration} -c:v libx264 -pix_fmt yuv420p "
        f"-c:a aac -strict experimental recordings/output.mp4"
    )
    await run_command_async(record_command)
    logger.info("Recording completed")

async def handle_transcription(gladia_api_key):
    """Handle the transcription process using Gladia API"""
    file_path = "recordings/output.mp4"
    if not os.path.exists(file_path):
        logger.error("Recording file not found")
        return

    # Prepare API request
    headers = {
        "x-gladia-key": gladia_api_key,
        "accept": "application/json",
    }

    # Upload file
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    files = [("audio", (file_path, file_content, "video/mp4"))]
    logger.info("Uploading file to Gladia...")
    upload_response = make_request(
        "https://api.gladia.io/v2/upload/", headers, "POST", files=files
    )
    
    # Request transcription
    audio_url = upload_response.get("audio_url")
    headers["Content-Type"] = "application/json"
    data = {
        "audio_url": audio_url,
        "diarization": str(os.getenv("DIARIZATION", "")).lower() in ["true", "t", "1", "yes", "y", "oui", "o"]
    }
    
    post_response = make_request(
        "https://api.gladia.io/v2/transcription/", headers, "POST", data=data
    )
    
    # Poll for results
    result_url = post_response.get("result_url")
    if result_url:
        await poll_transcription_results(result_url, headers)

async def poll_transcription_results(result_url, headers):
    # Keep checking until transcription is done
    while True:
        poll_response = make_request(result_url, headers)
        status = poll_response.get("status")

        if status == "done":
            # Get the full transcript
            transcript = poll_response.get("result", {}).get("transcription", {}).get("full_transcript", "")
            logger.info("Transcription completed")
            logger.info(f"\nTranscript:\n{transcript}\n")
            
            # Save complete response to file
            with open("transcriptions/transcript.json", "w") as f:
                json.dump(poll_response, f, indent=2)
            break
            
        elif status == "error":
            logger.error("Transcription failed")
            with open("transcriptions/error.json", "w") as f:
                json.dump(poll_response, f, indent=2)
            break
            
        else:
            logger.info(f"Transcription status: {status}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    click.echo("Starting Google Meet recorder...")
    asyncio.run(join_meet())
    click.echo("Finished recording Google Meet.")
