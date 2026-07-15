import pytest
from unittest.mock import MagicMock, patch
import claimer

def test_ensure_playwright_installed_success():
    with patch("claimer.sync_playwright") as mock_sync_playwright:
        mock_p = MagicMock()
        mock_browser = MagicMock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_p
        mock_p.chromium.launch.return_value = mock_browser
        
        claimer.ensure_playwright_installed()
        
        mock_p.chromium.launch.assert_called_once_with(headless=True)
        mock_browser.close.assert_called_once()

def test_ensure_playwright_installed_failure_and_install():
    with patch("claimer.sync_playwright") as mock_sync_playwright, \
         patch("claimer.subprocess.run") as mock_run:
        
        mock_sync_playwright.return_value.__enter__.side_effect = Exception("Launch failed")
        claimer.ensure_playwright_installed()
        
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
        
        mock_p.chromium.launch.assert_called_once_with(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
            ]
        )
        mock_browser.new_context.assert_called_once()
        kwargs = mock_browser.new_context.call_args[1]
        assert "Mozilla/5.0" in kwargs["user_agent"]
        assert kwargs["viewport"] == {"width": 1280, "height": 720}
        assert kwargs["bypass_csp"] is True
        
        mock_page.add_init_script.assert_called_once()
        assert p_inst == mock_p
        assert browser == mock_browser
        assert context == mock_context
        assert page == mock_page

@patch("claimer.human_delay")
@patch("claimer.send_discord_notification")
def test_claim_profile_success(mock_discord, mock_delay, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/mock")
    mock_page = MagicMock()
    mock_uid_locator = MagicMock()
    mock_login_locator = MagicMock()
    
    mock_uid_locator.is_visible.return_value = True
    mock_uid_locator.first = mock_uid_locator
    mock_login_locator.is_visible.return_value = True
    mock_login_locator.first = mock_login_locator
    
    mock_page.get_by_placeholder.side_effect = lambda placeholder: (
        mock_uid_locator if placeholder == "Enter Player ID" else MagicMock()
    )
    mock_page.get_by_role.side_effect = lambda role, name: (
        mock_login_locator if role == "button" and name == "Login" else MagicMock()
    )
    
    # Mocking the card and claiming elements
    mock_card = MagicMock()
    mock_card.inner_text.return_value = "Unclaimed"
    
    mock_title_loc = MagicMock()
    mock_title_loc.is_visible.return_value = True
    mock_title_loc.first = mock_title_loc
    mock_title_loc.text_content.return_value = "DAILY GIFT"
    
    mock_claim_btn = MagicMock()
    mock_claim_btn.is_visible.return_value = True
    mock_claim_btn.first = mock_claim_btn
    
    mock_confirm_btn = MagicMock()
    mock_confirm_btn.is_visible.return_value = True
    mock_confirm_btn.first = mock_confirm_btn
    mock_confirm_btn.text_content.return_value = "CLAIM GIFT"
    
    mock_default_locator = MagicMock()
    mock_default_locator.is_visible.return_value = False
    mock_default_locator.first = mock_default_locator
    
    def card_locator_side_effect(selector):
        if ".sku-info-section__titles__title" in selector:
            return mock_title_loc
        if "text=CLAIM GIFT" in selector:
            return mock_claim_btn
        return mock_default_locator
    mock_card.locator.side_effect = card_locator_side_effect
    
    mock_freebie_locator = MagicMock()
    mock_freebie_locator.all.return_value = [mock_card]
    
    mock_dialog_success_locator = MagicMock()
    mock_dialog_success_locator.first.is_visible.return_value = True
    
    def page_locator_side_effect(selector):
        if ".sku-card--freebie" in selector:
            return mock_freebie_locator
        if "text=Claimed" in selector or "text=Success" in selector:
            return mock_dialog_success_locator
        if "CLAIM GIFT" in selector:
            return mock_confirm_btn
        return mock_default_locator
        
    mock_page.locator.side_effect = page_locator_side_effect
    
    profile = {"name": "Test Player", "uid": "1122334455"}
    success = claimer.claim_profile(mock_page, profile)
    
    assert success is True
    mock_page.goto.assert_called_with("https://store.callofdutymobile.com/", wait_until="domcontentloaded", timeout=30000)
    mock_uid_locator.click.assert_called_once()
    mock_uid_locator.fill.assert_called_with("")
    assert mock_uid_locator.type.call_count == len("1122334455")
    
    mock_page.wait_for_selector.assert_any_call("text=Test Player", timeout=5000)
    mock_claim_btn.click.assert_called_once()
    mock_discord.assert_called_once_with("https://discord.com/api/webhooks/mock", "Test Player", "1122334455", "success", error_msg="Successfully claimed free gift 'DAILY GIFT'!")

@patch("claimer.human_delay")
@patch("claimer.send_discord_notification")
def test_claim_profile_success_with_cp_popup_close(mock_discord, mock_delay, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/mock")
    mock_page = MagicMock()
    mock_uid_locator = MagicMock()
    mock_login_locator = MagicMock()
    
    mock_uid_locator.is_visible.return_value = True
    mock_login_locator.is_visible.return_value = True
    
    mock_page.get_by_placeholder.side_effect = lambda placeholder: (
        mock_uid_locator if placeholder == "Enter Player ID" else MagicMock()
    )
    
    mock_close_locator = MagicMock()
    mock_close_locator.first = mock_close_locator
    mock_close_locator.first.is_visible.return_value = True
    
    def get_by_role_side_effect(role, name):
        if role == "button" and name == "Login":
            return mock_login_locator
        elif role == "button" and name == "Continue Browsing":
            return mock_close_locator
        return MagicMock()
        
    mock_page.get_by_role.side_effect = get_by_role_side_effect
    
    # Mocking the card and claiming elements
    mock_card = MagicMock()
    mock_card.inner_text.return_value = "Unclaimed"
    
    mock_title_loc = MagicMock()
    mock_title_loc.is_visible.return_value = True
    mock_title_loc.first = mock_title_loc
    mock_title_loc.text_content.return_value = "DAILY GIFT"
    
    mock_claim_btn = MagicMock()
    mock_claim_btn.is_visible.return_value = True
    mock_claim_btn.first = mock_claim_btn
    
    mock_confirm_btn = MagicMock()
    mock_confirm_btn.is_visible.return_value = True
    mock_confirm_btn.first = mock_confirm_btn
    mock_confirm_btn.text_content.return_value = "CLAIM GIFT"
    
    mock_default_locator = MagicMock()
    mock_default_locator.is_visible.return_value = False
    mock_default_locator.first = mock_default_locator
    
    def card_locator_side_effect(selector):
        if ".sku-info-section__titles__title" in selector:
            return mock_title_loc
        if "text=CLAIM GIFT" in selector:
            return mock_claim_btn
        return mock_default_locator
    mock_card.locator.side_effect = card_locator_side_effect
    
    mock_freebie_locator = MagicMock()
    mock_freebie_locator.all.return_value = [mock_card]
    
    mock_dialog_success_locator = MagicMock()
    mock_dialog_success_locator.first.is_visible.return_value = True
    
    def page_locator_side_effect(selector):
        if ".sku-card--freebie" in selector:
            return mock_freebie_locator
        if "text=Claimed" in selector or "text=Success" in selector:
            return mock_dialog_success_locator
        if "CLAIM GIFT" in selector:
            return mock_confirm_btn
        return mock_default_locator
        
    mock_page.locator.side_effect = page_locator_side_effect
    
    profile = {"name": "Test Player", "uid": "1122334455"}
    success = claimer.claim_profile(mock_page, profile)
    
    assert success is True
    mock_close_locator.first.click.assert_called_once()
    mock_discord.assert_called_once_with("https://discord.com/api/webhooks/mock", "Test Player", "1122334455", "success", error_msg="Successfully claimed free gift 'DAILY GIFT'!")

@patch("claimer.human_delay")
@patch("claimer.send_discord_notification")
def test_claim_profile_login_failure(mock_discord, mock_delay, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/mock")
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
    
    mock_page.wait_for_selector.side_effect = Exception("Nickname timeout")
    
    # Simulate not finding any daily free gift cards
    mock_freebie_locator = MagicMock()
    mock_freebie_locator.all.return_value = []
    
    def page_locator_side_effect(selector):
        if ".sku-card--freebie" in selector:
            return mock_freebie_locator
        return MagicMock()
    mock_page.locator.side_effect = page_locator_side_effect
    
    profile = {"name": "Test Player", "uid": "1122334455"}
    success = claimer.claim_profile(mock_page, profile)
    
    assert success is False
    mock_discord.assert_called_once_with(
        "https://discord.com/api/webhooks/mock", 
        "Test Player", 
        "1122334455", 
        "failed", 
        error_msg="Failed to locate any Daily Free Gift card elements (.sku-card--freebie) on the page."
    )

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
def test_main_internet_failure(mock_setup_logging, mock_exit, mock_wait_for_internet):
    mock_wait_for_internet.return_value = False
    mock_exit.side_effect = SystemExit(1)
    
    with patch("claimer.argparse.ArgumentParser.parse_args") as mock_args, \
         patch("os.path.exists", return_value=False):
        mock_args.return_value = MagicMock(visible=False)
        with pytest.raises(SystemExit) as excinfo:
            claimer.main()
    
    assert excinfo.value.code == 1
    mock_setup_logging.assert_called_once()
    mock_wait_for_internet.assert_called_once()
    mock_exit.assert_called_once_with(1)

@patch("claimer.wait_for_internet")
@patch("claimer.load_profiles")
@patch("claimer.init_browser")
@patch("claimer.claim_profile")
@patch("claimer.ensure_playwright_installed")
@patch("claimer.human_delay")
@patch("claimer.setup_logging")
def test_main_claiming(
    mock_setup_logging, mock_delay, mock_ensure_installed, mock_claim_profile, 
    mock_init_browser, mock_load_profiles, mock_wait_internet
):
    mock_wait_internet.return_value = True
    mock_load_profiles.return_value = [
        {"name": "Player1", "uid": "111"},
        {"name": "Player2", "uid": "222"}
    ]
    
    mock_p = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    mock_init_browser.return_value = (mock_p, mock_browser, mock_context, mock_page)
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_claim_profile.return_value = True
    
    with patch("claimer.argparse.ArgumentParser.parse_args") as mock_args, \
         patch("os.path.exists", return_value=False):
        mock_args.return_value = MagicMock(visible=False)
        claimer.main()
        
    mock_setup_logging.assert_called_once()
    mock_wait_internet.assert_called_once()
    mock_init_browser.assert_called_once_with(visible=False)
    assert mock_claim_profile.call_count == 2
    mock_claim_profile.assert_any_call(mock_page, {"name": "Player1", "uid": "111"}, visible=False)
    mock_claim_profile.assert_any_call(mock_page, {"name": "Player2", "uid": "222"}, visible=False)
    assert mock_context.close.call_count >= 1
    mock_browser.close.assert_called_once()
    mock_p.stop.assert_called_once()

def test_setup_logging(tmp_path):
    log_file = tmp_path / "claimer.log"
    with patch("claimer.logger") as mock_logger:
        mock_logger.handlers = []
        claimer.setup_logging(log_path=str(log_file))
        mock_logger.setLevel.assert_called_once_with(claimer.logging.INFO)
        assert mock_logger.addHandler.call_count == 2

@patch("claimer.urllib.request.urlopen")
@patch("claimer.urllib.request.Request")
def test_send_discord_notification_success(mock_request, mock_urlopen):
    mock_response = MagicMock()
    mock_response.status = 204
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    claimer.send_discord_notification("https://discord.com/api/webhooks/mock", "Player1", "123", "success")
    mock_request.assert_called_once()
    mock_urlopen.assert_called_once()

@patch("claimer.urllib.request.urlopen")
@patch("claimer.logger")
def test_send_discord_notification_failure(mock_logger, mock_urlopen):
    mock_urlopen.side_effect = Exception("HTTP Error")
    claimer.send_discord_notification("https://discord.com/api/webhooks/mock", "Player1", "123", "success")
    mock_logger.error.assert_called_once()
