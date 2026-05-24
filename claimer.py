import os
import sys
import json
import random
import time
import argparse
import subprocess
import urllib.request
import urllib.error
import logging
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright, Error

# Initialize named logger
logger = logging.getLogger("claimer")

def setup_logging(log_path="logs/claimer.log"):
    """
    Sets up unified logging to both standard output and logs/claimer.log.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Stream handler for stdout
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        # File handler for log file
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

def check_internet_connection(timeout=5):
    """
    Checks reachability of https://store.callofdutymobile.com/
    by sending a request with a realistic User-Agent.
    Returns True if connection succeeds and status is 200, False otherwise.
    """
    url = "https://store.callofdutymobile.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status == 200
    except Exception:
        return False

def wait_for_internet(max_timeout=60):
    """
    Loops check_internet_connection() with exponential backoff.
    Starts sleeping at 5s, doubles the interval on subsequent attempts, capped at remaining time or max_timeout.
    Returns True if connection is established, False otherwise.
    """
    start_time = time.time()
    sleep_interval = 5
    
    if check_internet_connection():
        return True
        
    while True:
        elapsed = time.time() - start_time
        remaining = max_timeout - elapsed
        if remaining <= 0:
            break
            
        current_sleep = min(sleep_interval, remaining)
        logger.warning(f"Internet offline. Retrying in {current_sleep:.1f} seconds...")
        time.sleep(current_sleep)
        
        if check_internet_connection():
            return True
            
        sleep_interval *= 2
        
    logger.error(f"Failed to establish internet connection to store.callofdutymobile.com within {max_timeout} seconds.")
    return False

def mask_name(name):
    """Masks a player name for logging security (e.g., 'PlayerNickname' -> 'Pl************')."""
    if not name or name == "Unknown Player":
        return name
    if len(name) <= 2:
        return name[0] + "*"
    return name[:2] + "*" * (len(name) - 2)

def mask_uid(uid):
    """Masks a player UID for logging security (e.g., '123456789' -> '123***789')."""
    if not uid:
        return ""
    if len(uid) <= 6:
        return uid[:2] + "*" * (len(uid) - 2)
    return uid[:3] + "*" * (len(uid) - 6) + uid[-3:]

def load_profiles():
    """
    Loads user profiles strictly from the CODM_PROFILES environment variable (JSON array).
    Each profile should contain 'name' and 'uid'.
    """
    env_profiles = os.environ.get("CODM_PROFILES")
    if not env_profiles:
        logger.error("CODM_PROFILES environment variable is missing or empty. Please set it as a GitHub Secret.")
        return []
        
    try:
        profiles = json.loads(env_profiles)
        if isinstance(profiles, list):
            logger.info("Successfully loaded profiles from CODM_PROFILES environment variable.")
            return profiles
        else:
            logger.error("CODM_PROFILES environment variable is not a JSON array. Please verify your secret.")
            return []
    except Exception as e:
        logger.error(f"Failed to parse CODM_PROFILES environment variable JSON: {e}")
        return []

def send_discord_notification(webhook_url, player_name, uid, status, error_msg=None):
    """
    Sends a structured rich embed notification to a Discord Webhook.
    """
    if not webhook_url:
        return
        
    color = 3066993 if status == "success" else 15158332
    title = "🎮 CODM Daily Free Gift Claimed!" if status == "success" else "❌ CODM Daily Free Gift Failure!"
    description = "Successfully claimed the daily free reward on the CODM Official Store!" if status == "success" else "Failed to claim the daily free reward."
    
    embed = {
        "title": title,
        "description": description,
        "color": color,
        "fields": [
            {"name": "Player Name", "value": player_name, "inline": True},
            {"name": "Player UID", "value": f"`{uid}`", "inline": True}
        ],
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "footer": {
            "text": "CODM Daily Gift Claimer | Automated with GitHub Actions"
        }
    }
    
    if error_msg:
        embed["fields"].append({"name": "Error Details", "value": f"```{error_msg}```", "inline": False})
        
    payload = {
        "embeds": [embed]
    }
    
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status not in (200, 204):
                logger.warning(f"Discord Webhook returned status code: {response.status}")
    except Exception as e:
        logger.error(f"Failed to send Discord notification: {e}")

def ensure_playwright_installed():
    """
    Verifies if Playwright Chromium browser is installed,
    and automatically installs it if missing.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
    except Exception:
        logger.info("Playwright Chromium browser binaries not found. Installing automatically...")
        try:
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            logger.info("Chromium installed successfully.")
        except subprocess.CalledProcessError as err:
            logger.error(f"Error installing Chromium: {err}")
            sys.exit(1)

def init_browser(visible=False):
    """
    Initializes a new Playwright Chromium instance with custom stealth configurations.
    Returns (playwright_instance, browser, context, page)
    """
    p = sync_playwright().start()
    try:
        browser = p.chromium.launch(
            headless=not visible,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
            ]
        )
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        context = browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1280, "height": 720},
            device_scale_factor=1,
            bypass_csp=True
        )
        
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return p, browser, context, page
    except Exception as e:
        p.stop()
        raise e

def human_delay(min_sec=1.0, max_sec=3.0):
    """Sleeps for a random duration to simulate human timing."""
    time.sleep(random.uniform(min_sec, max_sec))



def claim_profile(page, profile, visible=False):
    """
    Performs the full navigation, authentication, nickname verification, 
    and gift claiming flow for a single player profile.
    """
    name = profile.get("name", "Unknown Player")
    uid = profile.get("uid")
    if not uid:
        logger.warning(f"Skipping profile '{mask_name(name)}' because UID is missing.")
        return False
        
    logger.info(f"--- Processing Profile: {mask_name(name)} (UID: {mask_uid(uid)}) ---")
    
    try:
        # Navigate to Call of Duty: Mobile Store
        logger.info("Navigating to Call of Duty: Mobile Store...")
        page.goto("https://store.callofdutymobile.com/", wait_until="domcontentloaded", timeout=30000)
        human_delay(2.0, 4.0)
        
        # Locate UID Input Field (Multi-strategy)
        logger.info("Locating Player ID input field...")
        uid_field = None
        uid_selectors = [
            lambda p: p.get_by_placeholder("Enter Player ID"),
            lambda p: p.get_by_placeholder("UID"),
            lambda p: p.locator("input[placeholder*='ID' i]"),
            lambda p: p.locator("input[placeholder*='UID' i]"),
            lambda p: p.locator("input[type='text']").first,
            lambda p: p.locator("input#userid"),
        ]
        
        for idx, strategy in enumerate(uid_selectors):
            try:
                locator = strategy(page)
                if locator.is_visible(timeout=2000):
                    uid_field = locator
                    logger.info(f"Found UID field using strategy {idx + 1}.")
                    break
            except Exception:
                continue
                
        if not uid_field:
            raise Exception("Failed to locate the UID input field on the page.")
            
        # Simulating human-like input typing with micro-delays
        logger.info("Typing Player UID...")
        human_delay(1.0, 2.5) # Stealth delay before clicking UID field
        uid_field.click()
        uid_field.fill("") # Clear input first
        human_delay(0.5, 1.0)
        for char in uid:
            uid_field.type(char)
            time.sleep(random.uniform(0.05, 0.15))
            
        human_delay(1.0, 2.5)
        
        # Locate and Click Login Button (Multi-strategy)
        logger.info("Locating Login button...")
        login_btn = None
        login_selectors = [
            lambda p: p.get_by_role("button", name="Login"),
            lambda p: p.get_by_role("button", name="Submit"),
            lambda p: p.locator("button:has-text('Login')"),
            lambda p: p.locator("button:has-text('Submit')"),
            lambda p: p.locator("button[type='submit']"),
            lambda p: p.locator(".login-btn"),
        ]
        
        for idx, strategy in enumerate(login_selectors):
            try:
                locator = strategy(page)
                if locator.is_visible(timeout=2000):
                    login_btn = locator
                    logger.info(f"Found Login button using strategy {idx + 1}.")
                    break
            except Exception:
                continue
                
        if login_btn:
            human_delay(1.2, 2.8) # Stealth delay before clicking Login button
            logger.info("Clicking Login...")
            login_btn.click()
            human_delay(2.0, 4.0)
        else:
            logger.info("No explicit Login button found on the page. Pressing Enter on UID field to trigger validation...")
            try:
                uid_field.press("Enter")
                human_delay(2.0, 4.0)
            except Exception as press_err:
                logger.warning(f"Could not press Enter on UID field: {press_err}")
        
        # Verify Player Nickname Displays on screen (non-blocking)
        logger.info("Verifying player nickname...")
        verified = False
        try:
            page.wait_for_selector(f"text={name}", timeout=5000)
            logger.info(f"Verified: {mask_name(name)} is displayed on the page.")
            verified = True
        except Exception:
            try:
                logout_found = page.locator("text=Logout").first.is_visible(timeout=1000) or page.locator("text=Sign Out").first.is_visible(timeout=1000)
                if logout_found:
                    logger.info("Verified: Session is active (Logout/Sign Out option visible), assuming successfully logged in.")
                    verified = True
            except Exception:
                pass

        if not verified:
            logger.warning(f"Warning: Nickname '{mask_name(name)}' or active session not explicitly detected yet. Proceeding to claim, as validation may occur during the claim step.")

        human_delay(2.0, 3.5)
        
        # Locate Daily Free Gift
        logger.info("Locating Daily Free Gift item...")
        
        gift_selectors = [
            lambda p: p.locator(".gift-card, .card, div").filter(has_text="DAILY GIFT").locator("text=CLAIM GIFT").first,
            lambda p: p.locator("text=CLAIM GIFT").first,
            lambda p: p.get_by_role("button", name="Claim").first,
            lambda p: p.get_by_role("button", name="Get").first,
            lambda p: p.locator("button:has-text('Claim')").first,
            lambda p: p.locator("button:has-text('Get')").first,
            lambda p: p.locator("text=Daily Free Gift").first,
            lambda p: p.locator("text=Free Gift").first,
            lambda p: p.locator("text=Claim Gift").first,
        ]
        
        claim_element = None
        for idx, strategy in enumerate(gift_selectors):
            try:
                locator = strategy(page)
                if locator.is_visible(timeout=2000):
                    claim_element = locator
                    logger.info(f"Found claim element target using strategy {idx + 1}.")
                    break
            except Exception:
                continue
                
        if not claim_element:
            raise Exception("Failed to locate Daily Free Gift claim element.")
            
        logger.info("Waiting to trigger claim click...")
        human_delay(1.5, 3.0)
        
        logger.info("Clicking Daily Free Gift...")
        claim_element.click()
        human_delay(2.0, 4.0)
        
        # Check for and handle any confirmation popups/dialogs
        logger.info("Checking for confirmation dialogs...")
        confirm_selectors = [
            lambda p: p.locator("[role='dialog'] button:has-text('CLAIM GIFT')"),
            lambda p: p.locator("[class*='modal' i] button:has-text('CLAIM GIFT')"),
            lambda p: p.locator("[class*='popup' i] button:has-text('CLAIM GIFT')"),
            lambda p: p.locator("[class*='dialog' i] button:has-text('CLAIM GIFT')"),
            lambda p: p.locator("div").filter(has_text="You are about to claim your Gift").locator("button:has-text('CLAIM GIFT')"),
            lambda p: p.get_by_role("button", name="Confirm"),
            lambda p: p.get_by_role("button", name="OK"),
            lambda p: p.get_by_role("button", name="Yes"),
            lambda p: p.get_by_role("button", name="Claim"),
            lambda p: p.get_by_role("button", name="Continue"),
            lambda p: p.locator("button:has-text('Confirm')"),
            lambda p: p.locator("button:has-text('OK')"),
            lambda p: p.locator("button:has-text('Claim')"),
            lambda p: p.locator("button:has-text('Continue')"),
            lambda p: p.locator(".modal-confirm-btn"),
            lambda p: p.locator(".confirm-btn"),
        ]
        
        confirm_btn = None
        for idx, strategy in enumerate(confirm_selectors):
            try:
                locator = strategy(page)
                if locator.first.is_visible(timeout=1500):
                    candidate_btn = locator.first
                    btn_text = candidate_btn.text_content() or ""
                    confirm_btn = candidate_btn
                    logger.info(f"Found confirmation button using strategy {idx + 1}: '{btn_text}'")
                    break
            except Exception:
                continue
                
        if confirm_btn:
            try:
                if name.lower() in page.content().lower():
                    logger.info(f"Double confirmed: Player name '{mask_name(name)}' detected in page content.")
            except Exception:
                pass
            human_delay(1.0, 2.5) # Stealth delay before clicking Confirmation button
            logger.info("Clicking confirmation button...")
            confirm_btn.click()
            human_delay(2.0, 4.0)
        
        # Verify Success
        logger.info("Verifying claim success...")
        human_delay(2.0, 4.0)
        
        success_indicators = [
            "Claimed",
            "Successfully claimed",
            "Received",
            "Success",
            "Success!",
            "claimed",
            "received"
        ]
        
        success_detected = False
        for text in success_indicators:
            if page.locator(f"text={text}").first.is_visible(timeout=1000):
                logger.info(f"Success confirmation detected: '{text}'")
                success_detected = True
                break
                
        if not success_detected:
            try:
                btn_text = claim_element.text_content(timeout=1000) or ""
                if "claimed" in btn_text.lower():
                    logger.info("Success confirmation detected: Button text updated to 'Claimed'.")
                    success_detected = True
            except Exception:
                pass
                
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        
        if success_detected:
            logger.info(f"Successfully claimed Daily Free Gift for {mask_name(name)} ({mask_uid(uid)})!")
            if webhook_url:
                send_discord_notification(webhook_url, name, uid, "success")
            
            # Safely dismiss the CP buy popup if visible to avoid accidental purchases
            try:
                close_selectors = [
                    lambda p: p.get_by_role("button", name="Continue Browsing"),
                    lambda p: p.locator("button:has-text('CONTINUE BROWSING')"),
                    lambda p: p.locator("button:has-text('Continue')"),
                    lambda p: p.locator("[class*='modal' i] button:has-text('Continue')"),
                    lambda p: p.locator("[class*='modal' i] button:has-text('✕')"),
                    lambda p: p.locator("[class*='modal' i] button:has-text('X')"),
                    lambda p: p.locator(".modal-close, .close-btn, .close"),
                ]
                for idx, strategy in enumerate(close_selectors):
                    try:
                        locator = strategy(page)
                        if locator.first.is_visible(timeout=1500):
                            human_delay(1.0, 2.5) # Stealth delay before closing popup
                            logger.info(f"Closing CP buy popup using selector strategy {idx + 1}...")
                            locator.first.click()
                            human_delay(1.5, 3.0)
                            break
                    except Exception:
                        continue
            except Exception as close_err:
                logger.warning(f"Could not dismiss success popup: {close_err}")
                
            return True
        else:
            logger.warning(f"Warning: No explicit success confirmation popup detected for {mask_name(name)}. Assuming it may have already been claimed or claimed silently.")
            if webhook_url:
                send_discord_notification(webhook_url, name, uid, "success")
            return True
            
    except Exception as e:
        logger.error(f"Error claiming gift for profile '{mask_name(name)}': {e}")
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        if webhook_url:
            send_discord_notification(webhook_url, name, uid, "failed", error_msg=str(e))
        return False



def main():
    parser = argparse.ArgumentParser(description="Call of Duty: Mobile Store Daily Free Gift Claimer")
    parser.add_argument(
        "--visible", "-v", 
        action="store_true", 
        help="Run browser headfully (visible window) for debugging."
    )
    parser.add_argument(
        "--hold-open",
        type=int,
        default=0,
        help="Keep the browser open for this many seconds before cleanup."
    )
    args = parser.parse_args()
    hold_open = int(getattr(args, "hold_open", 0) or 0)
    
    # 1. Setup Logging
    setup_logging()
    
    # 2. Start internet connectivity check with backoff retry
    if not wait_for_internet():
        logger.error("Internet connectivity check failed. Exiting.")
        sys.exit(1)
        
    profiles = load_profiles()
    if not profiles:
        logger.info("No profiles loaded. Exiting.")
        sys.exit(0)
        
    logger.info(f"Loaded {len(profiles)} profiles.")
    
    # Auto-ensure Playwright browser binaries
    ensure_playwright_installed()
    
    # 3. Iterate profiles and claim
    browser_started = False
    p_inst, browser, context, page = None, None, None, None
    success_count = 0
    failed_count = 0
    
    try:
        for profile in profiles:
            uid = profile.get("uid")
            name = profile.get("name", "Unknown Player")
            if not uid:
                logger.warning(f"Skipping profile '{mask_name(name)}' because UID is missing.")
                continue
                
            # Initialize browser on demand
            if not browser_started:
                p_inst, browser, context, page = init_browser(visible=args.visible)
                browser_started = True
                
            success = claim_profile(page, profile, visible=args.visible)
            
            if success:
                success_count += 1
            else:
                failed_count += 1
                
            human_delay(3.0, 6.0)
    finally:
        if browser_started:
            if hold_open > 0:
                logger.info(f"Holding browser open for {hold_open} seconds...")
                time.sleep(hold_open)
            logger.info("Cleaning up and closing browser...")
            context.close()
            browser.close()
            p_inst.stop()
            
    logger.info(f"Execution finished. Successfully claimed for {success_count}/{len(profiles)} attempted profiles.")

if __name__ == "__main__":
    main()
