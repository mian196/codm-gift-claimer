import pytest
from unittest.mock import MagicMock, patch
import claimer

def test_ensure_playwright_installed_success():
    with patch("claimer.sync_playwright") as mock_sync_playwright:
        mock_p = MagicMock()
        mock_browser = MagicMock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_p
        mock_p.chromium.launch.return_value = mock_browser
        
        # Should not raise exception
        claimer.ensure_playwright_installed()
        
        mock_p.chromium.launch.assert_called_once_with(headless=True)
        mock_browser.close.assert_called_once()

def test_ensure_playwright_installed_failure_and_install():
    with patch("claimer.sync_playwright") as mock_sync_playwright, \
         patch("claimer.subprocess.run") as mock_run:
        
        # Force the check launch to fail
        mock_sync_playwright.return_value.__enter__.side_effect = Exception("Launch failed")
        
        claimer.ensure_playwright_installed()
        
        # Check that playwright install was triggered
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "playwright" in args
        assert "install" in args
        assert "chromium" in args

def test_init_browser():
    with patch("claimer.sync_playwright") as mock_sync_playwright:
        mock_p = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        
        mock_sync_playwright.return_value.start.return_value = mock_p
        mock_p.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        p_inst, browser, context, page = claimer.init_browser(visible=True)
        
        # Verify launch arguments
        mock_p.chromium.launch.assert_called_once_with(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
            ]
        )
        
        # Verify context configurations
        mock_browser.new_context.assert_called_once()
        kwargs = mock_browser.new_context.call_args[1]
        assert "Mozilla/5.0" in kwargs["user_agent"]
        assert kwargs["viewport"] == {"width": 1280, "height": 720}
        assert kwargs["bypass_csp"] is True
        
        # Verify custom stealth override and return values
        mock_page.add_init_script.assert_called_once()
        assert p_inst == mock_p
        assert browser == mock_browser
        assert context == mock_context
        assert page == mock_page

@patch("claimer.human_delay")
@patch("claimer.capture_claim_screenshot")
def test_claim_profile_success(mock_screenshot, mock_delay):
    mock_page = MagicMock()
    mock_uid_locator = MagicMock()
    mock_login_locator = MagicMock()
    mock_claim_locator = MagicMock()
    mock_success_locator = MagicMock()
    
    # Setup strategies visibility
    mock_page.get_by_placeholder.side_effect = lambda placeholder: (
        mock_uid_locator if placeholder == "Enter Player ID" else MagicMock()
    )
    mock_page.get_by_role.side_effect = lambda role, name: (
        mock_login_locator if role == "button" and name == "Login" else (
            mock_claim_locator if role == "button" and name == "Claim" else MagicMock()
        )
    )
    
    # Elements visibility mock
    mock_uid_locator.is_visible.return_value = True
    mock_login_locator.is_visible.return_value = True
    mock_claim_locator.first.is_visible.return_value = True
    
    # Success banner search mock
    mock_page.locator.side_effect = lambda selector: (
        mock_success_locator if "text=Claimed" in selector else MagicMock()
    )
    mock_success_locator.first.is_visible.return_value = True
    
    profile = {"name": "Test Player", "uid": "1122334455"}
    success = claimer.claim_profile(mock_page, profile)
    
    assert success is True
    mock_page.goto.assert_called_with("https://store.callofdutymobile.com/", wait_until="domcontentloaded", timeout=30000)
    mock_uid_locator.click.assert_called_once()
    mock_uid_locator.fill.assert_called_with("")
    
    # Types out letters
    assert mock_uid_locator.type.call_count == len("1122334455")
    mock_login_locator.click.assert_called_once()
    
    # Nickname checks
    mock_page.wait_for_selector.assert_any_call("text=Test Player", timeout=10000)
    
    # Claim triggers
    mock_claim_locator.first.click.assert_called_once()
    mock_screenshot.assert_called_once_with(mock_page, "1122334455", "success")

@patch("claimer.human_delay")
@patch("claimer.capture_claim_screenshot")
def test_claim_profile_login_failure(mock_screenshot, mock_delay):
    mock_page = MagicMock()
    mock_uid_locator = MagicMock()
    mock_login_locator = MagicMock()
    
    mock_page.get_by_placeholder.side_effect = lambda placeholder: (
        mock_uid_locator if placeholder == "Enter Player ID" else MagicMock()
    )
    mock_page.get_by_role.side_effect = lambda role, name: (
        mock_login_locator if role == "button" and name == "Login" else MagicMock()
    )
    
    mock_uid_locator.is_visible.return_value = True
    mock_login_locator.is_visible.return_value = True
    
    # Nickname check raises timeout
    mock_page.wait_for_selector.side_effect = Exception("Nickname timeout")
    
    # General logout/signin visibility
    mock_logout_locator = MagicMock()
    mock_logout_locator.first.is_visible.return_value = False
    mock_page.locator.side_effect = lambda selector: mock_logout_locator
    
    profile = {"name": "Test Player", "uid": "1122334455"}
    success = claimer.claim_profile(mock_page, profile)
    
    assert success is False
    mock_screenshot.assert_called_once_with(mock_page, "1122334455", "fail")

def test_load_claims_not_exist(tmp_path):
    state_file = tmp_path / "claims.json"
    assert claimer.load_claims(state_path=str(state_file)) == []

def test_load_claims_invalid(tmp_path):
    state_file = tmp_path / "claims.json"
    state_file.write_text("invalid json", encoding="utf-8")
    assert claimer.load_claims(state_path=str(state_file)) == []

def test_save_and_load_claims(tmp_path):
    state_file = tmp_path / "claims.json"
    claimer.save_claim("123", "Player1", "success", state_path=str(state_file))
    claims = claimer.load_claims(state_path=str(state_file))
    assert len(claims) == 1
    assert claims[0]["uid"] == "123"
    assert claims[0]["name"] == "Player1"
    assert claims[0]["status"] == "success"
    assert "timestamp" in claims[0]

def test_is_already_claimed_today(tmp_path):
    state_file = tmp_path / "claims.json"
    # Empty
    assert claimer.is_already_claimed_today("123", state_path=str(state_file)) is False
    
    # Save a failed claim for today
    claimer.save_claim("123", "Player1", "failed", state_path=str(state_file))
    assert claimer.is_already_claimed_today("123", state_path=str(state_file)) is False
    
    # Save a success claim for a past date
    import json
    from datetime import datetime, timedelta
    past_date = (datetime.now() - timedelta(days=1)).isoformat()
    claims = [{"uid": "123", "name": "Player1", "status": "success", "timestamp": past_date}]
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(claims, f)
    assert claimer.is_already_claimed_today("123", state_path=str(state_file)) is False
    
    # Save a success claim for today
    claimer.save_claim("123", "Player1", "success", state_path=str(state_file))
    assert claimer.is_already_claimed_today("123", state_path=str(state_file)) is True

@patch("claimer.urllib.request.urlopen")
@patch("claimer.urllib.request.Request")
def test_check_internet_connection_success(mock_request, mock_urlopen):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    assert claimer.check_internet_connection() is True
    mock_request.assert_called_once()
    assert mock_request.call_args[0][0] == "https://store.callofdutymobile.com/"

@patch("claimer.urllib.request.urlopen")
def test_check_internet_connection_failure(mock_urlopen):
    mock_urlopen.side_effect = Exception("Connection error")
    assert claimer.check_internet_connection() is False

@patch("claimer.check_internet_connection")
@patch("claimer.time.sleep")
@patch("claimer.time.time")
def test_wait_for_internet_immediate_success(mock_time, mock_sleep, mock_check):
    mock_check.return_value = True
    assert claimer.wait_for_internet() is True
    mock_sleep.assert_not_called()

@patch("claimer.check_internet_connection")
@patch("claimer.time.sleep")
def test_wait_for_internet_retry_success(mock_sleep, mock_check):
    mock_check.side_effect = [False, True]
    assert claimer.wait_for_internet(max_timeout=60) is True
    mock_sleep.assert_called_once_with(5)

@patch("claimer.check_internet_connection")
@patch("claimer.time.sleep")
def test_wait_for_internet_timeout(mock_sleep, mock_check):
    mock_check.return_value = False
    with patch("claimer.time.time") as mock_time:
        mock_time.side_effect = [0, 0, 3.1]
        assert claimer.wait_for_internet(max_timeout=3) is False
        mock_sleep.assert_called_once_with(3)

@patch("claimer.wait_for_internet")
@patch("claimer.sys.exit")
@patch("claimer.setup_logging")
@patch("claimer.cleanup_old_screenshots")
def test_main_internet_failure(mock_cleanup, mock_setup_logging, mock_exit, mock_wait_for_internet):
    mock_wait_for_internet.return_value = False
    mock_exit.side_effect = SystemExit(1)
    
    with patch("claimer.argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = MagicMock(config="config/profiles.json", visible=False)
        with pytest.raises(SystemExit) as excinfo:
            claimer.main()
    
    assert excinfo.value.code == 1
    mock_setup_logging.assert_called_once()
    mock_cleanup.assert_called_once()
    mock_wait_for_internet.assert_called_once()
    mock_exit.assert_called_once_with(1)

@patch("claimer.wait_for_internet")
@patch("claimer.load_profiles")
@patch("claimer.is_already_claimed_today")
@patch("claimer.init_browser")
@patch("claimer.claim_profile")
@patch("claimer.save_claim")
@patch("claimer.ensure_playwright_installed")
@patch("claimer.human_delay")
@patch("claimer.setup_logging")
@patch("claimer.cleanup_old_screenshots")
def test_main_profile_skipping_and_claiming(
    mock_cleanup, mock_setup_logging, mock_delay, mock_ensure_installed, mock_save_claim, mock_claim_profile, 
    mock_init_browser, mock_is_already_claimed, mock_load_profiles, mock_wait_internet
):
    mock_wait_internet.return_value = True
    mock_load_profiles.return_value = [
        {"name": "Player1", "uid": "111"},
        {"name": "Player2", "uid": "222"}
    ]
    mock_is_already_claimed.side_effect = lambda uid: uid == "111"
    
    mock_p = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    mock_init_browser.return_value = (mock_p, mock_browser, mock_context, mock_page)
    mock_claim_profile.return_value = True
    
    with patch("claimer.argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = MagicMock(config="config/profiles.json", visible=False)
        claimer.main()
        
    mock_setup_logging.assert_called_once()
    mock_cleanup.assert_called_once()
    mock_wait_internet.assert_called_once()
    assert mock_is_already_claimed.call_count == 2
    mock_is_already_claimed.assert_any_call("111")
    mock_is_already_claimed.assert_any_call("222")
    mock_init_browser.assert_called_once_with(visible=False)
    mock_claim_profile.assert_called_once_with(mock_page, {"name": "Player2", "uid": "222"}, visible=False)
    mock_save_claim.assert_called_once_with("222", "Player2", "success")
    mock_context.close.assert_called_once()
    mock_browser.close.assert_called_once()
    mock_p.stop.assert_called_once()

@patch("claimer.wait_for_internet")
@patch("claimer.load_profiles")
@patch("claimer.is_already_claimed_today")
@patch("claimer.init_browser")
@patch("claimer.ensure_playwright_installed")
@patch("claimer.setup_logging")
@patch("claimer.cleanup_old_screenshots")
def test_main_all_profiles_skipped(
    mock_cleanup, mock_setup_logging, mock_ensure_installed, mock_init_browser, mock_is_already_claimed, mock_load_profiles, mock_wait_internet
):
    mock_wait_internet.return_value = True
    mock_load_profiles.return_value = [
        {"name": "Player1", "uid": "111"}
    ]
    mock_is_already_claimed.return_value = True
    
    with patch("claimer.argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = MagicMock(config="config/profiles.json", visible=False)
        claimer.main()
        
    mock_setup_logging.assert_called_once()
    mock_cleanup.assert_called_once()
    mock_init_browser.assert_not_called()

def test_setup_logging(tmp_path):
    log_file = tmp_path / "claimer.log"
    with patch("claimer.logger") as mock_logger:
        mock_logger.handlers = []
        claimer.setup_logging(log_path=str(log_file))
        mock_logger.setLevel.assert_called_once_with(claimer.logging.INFO)
        assert mock_logger.addHandler.call_count == 2

def test_capture_claim_screenshot_success():
    mock_page = MagicMock()
    uid = "12345"
    status = "success"
    
    with patch("claimer.os.makedirs") as mock_makedirs, \
         patch("claimer.os.path.join") as mock_join, \
         patch("claimer.logger") as mock_logger:
        
        mock_join.side_effect = lambda *args: "/".join(args)
        claimer.capture_claim_screenshot(mock_page, uid, status)
        
        mock_makedirs.assert_called_once_with("logs/screenshots/success", exist_ok=True)
        mock_page.screenshot.assert_called_once()
        kwargs = mock_page.screenshot.call_args[1]
        assert kwargs["full_page"] is True
        assert "logs/screenshots/success/success_12345_" in kwargs["path"]

def test_capture_claim_screenshot_exception():
    mock_page = MagicMock()
    mock_page.screenshot.side_effect = Exception("Screenshot failed")
    
    with patch("claimer.logger") as mock_logger:
        claimer.capture_claim_screenshot(mock_page, "123", "fail")
        mock_logger.error.assert_called_once()

def test_cleanup_old_screenshots():
    mock_files = [
        ("logs/screenshots/success", [], ["success_1_2026-05-20.png", "success_2_2026-05-20.png"])
    ]
    with patch("claimer.os.path.exists") as mock_exists, \
         patch("claimer.os.walk") as mock_walk, \
         patch("claimer.os.path.getmtime") as mock_mtime, \
         patch("claimer.os.remove") as mock_remove, \
         patch("claimer.logger") as mock_logger:
         
        mock_exists.return_value = True
        mock_walk.return_value = mock_files
        
        with patch("claimer.time.time") as mock_time:
            mock_time.return_value = 2000000000
            mock_mtime.side_effect = [1990000000, 1999000000]
            
            claimer.cleanup_old_screenshots(days_threshold=30)
            
            assert mock_remove.call_count == 1
            called_path = mock_remove.call_args[0][0]
            assert called_path.endswith("success_1_2026-05-20.png")

def test_show_toast_notification_non_windows():
    with patch("claimer.sys.platform", "linux"), \
         patch("claimer.subprocess.run") as mock_run:
        claimer.show_toast_notification(1, 0, 0)
        mock_run.assert_not_called()

def test_show_toast_notification_windows():
    with patch("claimer.sys.platform", "win32"), \
         patch("claimer.subprocess.run") as mock_run:
        claimer.show_toast_notification(2, 1, 0)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "powershell" in args
        assert "-NoProfile" in args
        assert "-ExecutionPolicy" in args
        assert "Bypass" in args
        
        # Check that powershell command matches Warning status
        powershell_cmd = args[-1]
        assert "BalloonTipIcon = 'Warning'" in powershell_cmd
        assert "Success: 2, Failed: 1" in powershell_cmd

def test_show_toast_notification_all_skipped():
    with patch("claimer.sys.platform", "win32"), \
         patch("claimer.subprocess.run") as mock_run:
        claimer.show_toast_notification(0, 0, 3)
        mock_run.assert_called_once()
        powershell_cmd = mock_run.call_args[0][0][-1]
        assert "BalloonTipIcon = 'Information'" in powershell_cmd
        assert "already successfully claimed today" in powershell_cmd


