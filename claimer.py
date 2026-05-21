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
from datetime import datetime
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

def load_profiles(config_path="config/profiles.json"):
    """
    Loads user profiles from either the CODM_PROFILES environment variable (JSON array)
    or falls back to the configuration JSON file.
    Each profile should contain 'name' and 'uid'.
    """
    env_profiles = os.environ.get("CODM_PROFILES")
    if env_profiles:
        try:
            profiles = json.loads(env_profiles)
            if isinstance(profiles, list):
                logger.info("Successfully loaded profiles from CODM_PROFILES environment variable.")
                return profiles
            else:
                logger.warning("CODM_PROFILES environment variable is not a JSON array. Falling back to file.")
        except Exception as e:
            logger.warning(f"Failed to parse CODM_PROFILES environment variable: {e}. Falling back to file.")

    if not os.path.exists(config_path):
        logger.warning(f"Warning: Configuration file not found at '{config_path}'. Returning empty list.")
        return []
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            profiles = json.load(f)
            if not isinstance(profiles, list):
                logger.warning(f"Warning: Configuration at '{config_path}' must be a JSON array. Returning empty list.")
                return []
            return profiles
    except json.JSONDecodeError as e:
        logger.warning(f"Warning: Failed to parse malformed JSON at '{config_path}': {e}. Returning empty list.")
        return []
    except Exception as e:
        logger.warning(f"Warning: Unexpected error reading '{config_path}': {e}. Returning empty list.")
        return []

def load_claims(state_path="state/claims.json"):
    """
    Loads historical claim attempt records from the state JSON file.
    Returns a JSON array of claim records.
    """
    if not os.path.exists(state_path):
        return []
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            claims = json.load(f)
            if not isinstance(claims, list):
                logger.warning(f"Warning: State at '{state_path}' must be a JSON array. Returning empty list.")
                return []
            return claims
    except json.JSONDecodeError as e:
        logger.warning(f"Warning: Failed to parse malformed JSON at '{state_path}': {e}. Returning empty list.")
        return []
    except Exception as e:
        logger.warning(f"Warning: Unexpected error reading '{state_path}': {e}. Returning empty list.")
        return []

def save_claim(uid, name, status, state_path="state/claims.json"):
    """
    Appends a claim execution record to state/claims.json.
    """
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    claims = load_claims(state_path)
    claims.append({
        "uid": uid,
        "name": name,
        "timestamp": datetime.now().isoformat(),
        "status": status
    })
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(claims, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Warning: Failed to write state to '{state_path}': {e}")

def is_already_claimed_today(uid, state_path="state/claims.json"):
    """
    Checks if a profile has already been claimed successfully on the current local calendar day.
    """
    claims = load_claims(state_path)
    date_str = datetime.now().strftime("%Y-%m-%d")
    for claim in claims:
        if claim.get("uid") == uid and claim.get("status") == "success":
            try:
                claim_date = claim.get("timestamp", "").split("T")[0]
                if claim_date == date_str:
                    return True
            except Exception:
                continue
    return False

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

def capture_claim_screenshot(page, uid, status):
    """
    Captures a full-page screenshot and saves it under logs/screenshots/[status]/
    with the name: [status]_[uid]_[YYYY-MM-DD].png.
    """
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        folder = f"logs/screenshots/{status}"
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, f"{status}_{uid}_{date_str}.png")
        logger.info(f"Capturing full-page screenshot: {filepath}")
        page.screenshot(path=filepath, full_page=True)
    except Exception as e:
        logger.error(f"Failed to capture claim screenshot for UID {uid}: {e}")

def cleanup_old_screenshots(days_threshold=30):
    """
    Recursively sweeps logs/screenshots/ and removes any .png files
    that have not been modified in over days_threshold days.
    """
    base_dir = os.path.join("logs", "screenshots")
    if not os.path.exists(base_dir):
        return
        
    now = time.time()
    cutoff = now - (days_threshold * 86400)
    purged_count = 0
    
    logger.info(f"Running rolling screenshot cleanup sweep (older than {days_threshold} days)...")
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".png"):
                filepath = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(filepath)
                    if mtime < cutoff:
                        os.remove(filepath)
                        logger.info(f"Purged old screenshot: {filepath}")
                        purged_count += 1
                except Exception as e:
                    logger.error(f"Error purging screenshot '{filepath}': {e}")
                    
    if purged_count > 0:
        logger.info(f"Purged {purged_count} old screenshots.")
    else:
        logger.info("No old screenshots to purge.")

def claim_profile(page, profile, visible=False):
    """
    Performs the full navigation, authentication, nickname verification, 
    and gift claiming flow for a single player profile.
    """
    name = profile.get("name", "Unknown Player")
    uid = profile.get("uid")
    if not uid:
        logger.warning(f"Skipping profile '{name}' because UID is missing.")
        return False
        
    logger.info(f"--- Processing Profile: {name} (UID: {uid}) ---")
    
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
            logger.info(f"Verified: {name} is displayed on the page.")
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
            logger.warning(f"Warning: Nickname '{name}' or active session not explicitly detected yet. Proceeding to claim, as validation may occur during the claim step.")

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
                    # Ignore the main page's 'CLAIM GIFT' buttons to avoid clicking them again as false positive
                    if "CLAIM GIFT" in btn_text.upper():
                        continue
                    confirm_btn = candidate_btn
                    logger.info(f"Found confirmation button using strategy {idx + 1}: '{btn_text}'")
                    break
            except Exception:
                continue
                
        if confirm_btn:
            try:
                if name.lower() in page.content().lower():
                    logger.info(f"Double confirmed: Player name '{name}' detected in page content.")
            except Exception:
                pass
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
                
        if success_detected:
            logger.info(f"Successfully claimed Daily Free Gift for {name} ({uid})!")
            capture_claim_screenshot(page, uid, "success")
            
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
            logger.warning(f"Warning: No explicit success confirmation popup detected for {name}. Assuming it may have already been claimed or claimed silently.")
            capture_claim_screenshot(page, uid, "success")
            return True
            
    except Exception as e:
        logger.error(f"Error claiming gift for profile '{name}': {e}")
        capture_claim_screenshot(page, uid, "fail")
        return False

def show_toast_notification(success_count: int, failed_count: int, skipped_count: int):
    """
    Triggers a native Windows Toast Notification displaying daily claim results
    via a PowerShell subprocess. Safely returns immediately on non-Windows platforms.
    """
    if sys.platform != "win32":
        return

    title = "CODM Daily Gift Claimer"
    
    if success_count == 0 and failed_count == 0 and skipped_count > 0:
        message = f"All {skipped_count} profile(s) already successfully claimed today!"
        icon = "Information"
    elif success_count > 0 and failed_count == 0:
        message = f"Successfully claimed free rewards for all {success_count} profile(s) today!"
        icon = "Information"
    elif success_count > 0 and failed_count > 0:
        message = f"Claiming complete. Success: {success_count}, Failed: {failed_count}."
        icon = "Warning"
    elif success_count == 0 and failed_count > 0:
        message = f"Failed to claim daily rewards for any profile today (Failed: {failed_count})."
        icon = "Error"
    else:
        message = "No profiles were processed today."
        icon = "Information"
        
    powershell_code = f"""
    [void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms')
    $notification = New-Object System.Windows.Forms.NotifyIcon
    $notification.Icon = [System.Drawing.SystemIcons]::Information
    $notification.BalloonTipIcon = '{icon}'
    $notification.BalloonTipTitle = '{title}'
    $notification.BalloonTipText = '{message}'
    $notification.Visible = $true
    $notification.ShowBalloonTip(5000)
    Start-Sleep -Seconds 1
    $notification.Dispose()
    """
    try:
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", powershell_code], capture_output=True)
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="Call of Duty: Mobile Store Daily Free Gift Claimer")
    parser.add_argument(
        "--visible", "-v", 
        action="store_true", 
        help="Run browser headfully (visible window) for debugging."
    )
    parser.add_argument(
        "--config", "-c", 
        default="config/profiles.json", 
        help="Path to the JSON profiles configuration file. Default: config/profiles.json"
    )
    args = parser.parse_args()
    
    # 1. Setup Logging and screen cleanup
    setup_logging()
    cleanup_old_screenshots()
    
    # 2. Start internet connectivity check with backoff retry
    if not wait_for_internet():
        logger.error("Internet connectivity check failed. Exiting.")
        sys.exit(1)
        
    profiles = load_profiles(args.config)
    if not profiles:
        logger.info("No profiles loaded. Exiting.")
        sys.exit(0)
        
    logger.info(f"Loaded {len(profiles)} profiles from '{args.config}'.")
    
    # Auto-ensure Playwright browser binaries
    ensure_playwright_installed()
    
    # 3. Iterate profiles and claim those not yet claimed today
    browser_started = False
    p_inst, browser, context, page = None, None, None, None
    success_count = 0
    skipped_count = 0
    failed_count = 0
    
    try:
        for profile in profiles:
            uid = profile.get("uid")
            name = profile.get("name", "Unknown Player")
            if not uid:
                logger.warning(f"Skipping profile '{name}' because UID is missing.")
                continue
                
            if is_already_claimed_today(uid):
                logger.info(f"Skipping {name} (UID: {uid}): Already claimed today.")
                skipped_count += 1
                continue
                
            # Initialize browser on demand
            if not browser_started:
                p_inst, browser, context, page = init_browser(visible=args.visible)
                browser_started = True
                
            success = claim_profile(page, profile, visible=args.visible)
            status = "success" if success else "failed"
            save_claim(uid, name, status)
            
            if success:
                success_count += 1
            else:
                failed_count += 1
                
            human_delay(3.0, 6.0)
    finally:
        if browser_started:
            logger.info("Cleaning up and closing browser...")
            context.close()
            browser.close()
            p_inst.stop()
            
    logger.info(f"Execution finished. Successfully claimed for {success_count}/{len(profiles) - skipped_count} attempted profiles. (Skipped {skipped_count} already claimed today)")
    
    # Trigger native Windows Toast Notification
    show_toast_notification(success_count, failed_count, skipped_count)

if __name__ == "__main__":
    main()
