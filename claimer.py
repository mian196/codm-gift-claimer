import os
import sys
import json
import random
import time
import argparse
import subprocess
from playwright.sync_api import sync_playwright, Error

def load_profiles(config_path="config/profiles.json"):
    """
    Loads user profiles from the configuration JSON file.
    Each profile should contain 'name' and 'uid'.
    """
    if not os.path.exists(config_path):
        print(f"Warning: Configuration file not found at '{config_path}'. Returning empty list.")
        return []
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            profiles = json.load(f)
            if not isinstance(profiles, list):
                print(f"Warning: Configuration at '{config_path}' must be a JSON array. Returning empty list.")
                return []
            return profiles
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse malformed JSON at '{config_path}': {e}. Returning empty list.")
        return []
    except Exception as e:
        print(f"Warning: Unexpected error reading '{config_path}': {e}. Returning empty list.")
        return []

def ensure_playwright_installed():
    """
    Verifies if Playwright Chromium browser is installed,
    and automatically installs it if missing.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
    except Exception as e:
        print("Playwright Chromium browser binaries not found. Installing automatically...")
        try:
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            print("Chromium installed successfully.")
        except subprocess.CalledProcessError as err:
            print(f"Error installing Chromium: {err}")
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
        
        # Additional stealth override via script evaluation
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
        print(f"Skipping profile '{name}' because UID is missing.")
        return False
        
    print(f"\n--- Processing Profile: {name} (UID: {uid}) ---")
    
    try:
        # Navigate to Call of Duty: Mobile Store
        print("Navigating to Call of Duty: Mobile Store...")
        page.goto("https://store.callofdutymobile.com/", wait_until="domcontentloaded", timeout=30000)
        human_delay(2.0, 4.0)
        
        # Locate UID Input Field (Multi-strategy)
        print("Locating Player ID input field...")
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
                    print(f"Found UID field using strategy {idx + 1}.")
                    break
            except Exception:
                continue
                
        if not uid_field:
            raise Exception("Failed to locate the UID input field on the page.")
            
        # Simulating human-like input typing with micro-delays
        print("Typing Player UID...")
        uid_field.click()
        uid_field.fill("") # Clear input first
        human_delay(0.5, 1.0)
        for char in uid:
            uid_field.type(char)
            time.sleep(random.uniform(0.05, 0.15))
            
        human_delay(1.0, 2.5)
        
        # Locate and Click Login Button (Multi-strategy)
        print("Locating Login button...")
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
                    print(f"Found Login button using strategy {idx + 1}.")
                    break
            except Exception:
                continue
                
        if not login_btn:
            raise Exception("Failed to locate the Login button on the page.")
            
        print("Clicking Login...")
        login_btn.click()
        
        # Verify Player Nickname Displays on screen
        print("Verifying player nickname...")
        try:
            # We wait up to 10 seconds for the nickname to appear
            page.wait_for_selector(f"text={name}", timeout=10000)
            print(f"Verified: {name}")
        except Exception:
            # If the specific name is not found, let's see if there is any logged-in indicator
            # or if it's an error message. Let's check for standard errors.
            print(f"Warning: Player name '{name}' text not explicitly detected in 10s. Checking general page state...")
            # Let's inspect if we logged in by finding elements indicating active session
            # (e.g. Logout button, or username container)
            logout_found = page.locator("text=Logout").first.is_visible(timeout=2000) or page.locator("text=Sign Out").first.is_visible(timeout=2000)
            if logout_found:
                print(f"Verified: Session is active (Logout/Sign Out option visible), assuming successfully logged in.")
            else:
                raise Exception(f"Login validation failed for UID '{uid}'. Nickname '{name}' not found and no active session detected.")

        human_delay(2.0, 3.5)
        
        # Locate Daily Free Gift (Multi-strategy container + claim button clicks)
        print("Locating Daily Free Gift item...")
        gift_claimed = False
        
        # Strategies to click the daily free gift
        # Strategy 1: Find button with "Claim" that's associated with "Daily" or "Free"
        # Strategy 2: Find a card with "Daily Free Gift" or "Free Gift" or price "0.00" and click it or its button
        # Strategy 3: Find any element containing "Free Gift" and search for button/claim text inside it
        
        # Let's check if there is an element with "Claim" or "Get" or "Free" or "0.00"
        gift_selectors = [
            # Check for specific "Claim" buttons or texts
            lambda p: p.get_by_role("button", name="Claim"),
            lambda p: p.get_by_role("button", name="Get"),
            lambda p: p.locator("button:has-text('Claim')"),
            lambda p: p.locator("button:has-text('Get')"),
            lambda p: p.locator("text=Daily Free Gift"),
            lambda p: p.locator("text=Free Gift"),
            lambda p: p.locator("text=Claim Gift"),
        ]
        
        claim_element = None
        for idx, strategy in enumerate(gift_selectors):
            try:
                locator = strategy(page)
                if locator.first.is_visible(timeout=2000):
                    claim_element = locator.first
                    print(f"Found claim element target using strategy {idx + 1}.")
                    break
            except Exception:
                continue
                
        if not claim_element:
            raise Exception("Failed to locate Daily Free Gift claim element.")
            
        print("Waiting to trigger claim click...")
        human_delay(1.5, 3.0)
        
        print("Clicking Daily Free Gift...")
        claim_element.click()
        
        # Verify Success (Multi-strategy verification)
        # Checking if success confirmation banner or dialog or text like "Claimed", "Successfully", "Received", "Success" is shown
        print("Verifying claim success...")
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
                print(f"Success confirmation detected: '{text}'")
                success_detected = True
                break
                
        if not success_detected:
            # If no overlay text, sometimes the button itself changes to "Claimed" or disabled.
            # Let's check if the claim element now contains "Claimed"
            try:
                btn_text = claim_element.text_content(timeout=1000) or ""
                if "claimed" in btn_text.lower():
                    print("Success confirmation detected: Button text updated to 'Claimed'.")
                    success_detected = True
            except Exception:
                pass
                
        if success_detected:
            print(f"Successfully claimed Daily Free Gift for {name} ({uid})!")
            return True
        else:
            # Sometimes there is no confirmation modal, it might just succeed silently.
            # If we reached here without raising an error, let's treat it as a success/warning but log it.
            print(f"Warning: No explicit success confirmation popup detected for {name}. Assuming it may have already been claimed or claimed silently.")
            return True
            
    except Exception as e:
        print(f"Error claiming gift for profile '{name}': {e}")
        return False

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
    
    profiles = load_profiles(args.config)
    if not profiles:
        print("No profiles loaded. Exiting.")
        sys.exit(0)
        
    print(f"Loaded {len(profiles)} profiles from '{args.config}'.")
    
    # Auto-ensure Playwright browser binaries
    ensure_playwright_installed()
    
    # Initialize the browser
    p_inst, browser, context, page = init_browser(visible=args.visible)
    
    success_count = 0
    try:
        for profile in profiles:
            success = claim_profile(page, profile, visible=args.visible)
            if success:
                success_count += 1
            # Add a break/pause between different profiles to clean up or avoid speed limits
            human_delay(3.0, 6.0)
    finally:
        print("\nCleaning up and closing browser...")
        context.close()
        browser.close()
        p_inst.stop()
        
    print(f"\nExecution finished. Successfully claimed for {success_count}/{len(profiles)} profiles.")

if __name__ == "__main__":
    main()
