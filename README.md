# 🎮 Call of Duty: Mobile Daily Free Gift Claimer (Windows Edition)

[![Store Compatibility](https://img.shields.io/badge/Store-CODM%20Official-gold?style=for-the-badge&logo=activision)](https://store.callofdutymobile.com/)
[![Playwright Powered](https://img.shields.io/badge/Engine-Playwright-green?style=for-the-badge&logo=playwright)](https://playwright.dev/)
[![Windows Native](https://img.shields.io/badge/OS-Windows-blue?style=for-the-badge&logo=windows)](https://microsoft.com/windows)
[![Discord Notifications](https://img.shields.io/badge/Notifications-Discord-blueviolet?style=for-the-badge&logo=discord)](https://discord.com/)

An elegant, automated, and highly secure Python script designed to automatically claim the **Daily Free Gift** on the official [Call of Duty: Mobile Web Store](https://store.callofdutymobile.com/). 

Bypasses cloud provider blocks (like Cloudflare data center IP restrictions on GitHub Actions/Azure) by running natively on your Windows PC. Configured to run automatically in the background when you log in, completely optimized to use **zero resources**.

---

## 🌟 Key Features

* **⚡ Sub-Millisecond State Check:** Spawns a browser only *once* a day. If executed multiple times a day (e.g., if you turn on/reboot your PC 20 times), it instantly exits in **under 1ms** with **0% CPU** and **0MB RAM** impact.
* **🛡️ Fully Local & Private:** No cloud runners, no sharing of Player UIDs or Discord webhooks. Everything is stored locally in your `config/` directory.
* **💬 Discord Status Webhook Alerts:** Optional integration to get gorgeous rich embed alerts directly in your Discord channel showing successful claims or failures.
* **🔧 Zero-Touch Provisioning:** Setup is done in 1 click! A helper `setup.bat` script installs Python, creates virtual environments, pulls browser binaries, and configures startup events automatically.

---

## 📂 Project Structure

```
├── config/              # Local player profiles and Discord settings
├── logs/                # Local runtime logs and error screenshots
├── claimer.py           # Core automated claiming script
├── setup.bat            # One-click Windows native provisioner & installer
├── start.bat            # Silent background launcher
├── requirements.txt     # Python project dependencies
└── README.md            # Premium repository index
```

---

## 🚀 Easy 3-Step Setup

### Step 1: Run Setup
Double-click **`setup.bat`** (or run it in a terminal). The script will:
- Check if Python is installed (and install it via `winget` if missing).
- Set up a clean virtual Python environment (`.venv`).
- Install all requirements and fetch the Playwright Chromium browser binary.
- Automatically register a user-level startup shortcut so it runs when you log into Windows (requires no Admin/UAC prompts!).

### Step 2: Configure Player Profiles
Open **`config/profiles.json`** and enter your Call of Duty: Mobile name and player UID:
```json
[
  { "name": "YourNickname", "uid": "Your21DigitUIDHere" }
]
```

### Step 3: Configure Settings (Optional)
If you want Discord status webhook alerts, open **`config/settings.json`** and add your webhook URL:
```json
{
  "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/your_token_here"
}
```

*That's it! You are done.* It will now silently check and claim your rewards completely in the background every single day when your PC starts up.

---

## 🧪 Testing

You can run a manual execution at any time by double-clicking **`start.bat`**.

To run unit and integration tests:
```bash
python -m pytest
```

---

## ⚖️ License & Disclaimer

This project is for educational and automation utility purposes. It is not affiliated with, authorized, or endorsed by Activision. Use responsibly.
