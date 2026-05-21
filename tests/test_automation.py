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
def test_claim_profile_success(mock_delay):
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

@patch("claimer.human_delay")
def test_claim_profile_login_failure(mock_delay):
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
