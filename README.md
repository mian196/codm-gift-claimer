# 🎮 Call of Duty: Mobile Daily Free Gift Claimer

[![Store Compatibility](https://img.shields.io/badge/Store-CODM%20Official-gold?style=for-the-badge&logo=activision)](https://store.callofdutymobile.com/)
[![Playwright Powered](https://img.shields.io/badge/Engine-Playwright-green?style=for-the-badge&logo=playwright)](https://playwright.dev/)
[![Windows Native](https://img.shields.io/badge/OS-Windows-blue?style=for-the-badge&logo=windows)](https://microsoft.com/windows)
[![Discord Notifications](https://img.shields.io/badge/Notifications-Discord-blueviolet?style=for-the-badge&logo=discord)](https://discord.com/)

An elegant, automated Python script designed to automatically claim the **Daily Free Gift** on the official [Call of Duty: Mobile Web Store](https://store.callofdutymobile.com/). 

Designed to run locally on Windows, this tool automatically executes in the background upon login and is optimized for zero resource consumption.

---

## 🌟 Key Features

* **⚡ Smart Daily State Check:** Only runs a browser once a day. If launched multiple times, it exits instantly in under a millisecond to save CPU and RAM.
* **🛡️ Private & Secure:** Your player UIDs and Discord configurations are kept fully local inside your `config/` directory.
* **💬 Discord Status Webhook Alerts:** Connect standard webhooks to receive rich status alerts showing successful claims or details of failures.
* **🔧 One-Click Setup:** Provisioning script automatically configures Python virtual environments, browser binaries, and startup tasks.

---

## 📂 Project Structure

```
├── config/              # Local player profiles and Discord settings
├── logs/                # Local runtime logs and error screenshots
├── claimer.py           # Core automated claiming script
├── setup.bat            # One-click Windows native provisioner & installer
├── start.bat            # Silent background launcher
├── requirements.txt     # Python project dependencies
└── README.md            # Project documentation index
```

---

## 🚀 Easy 3-Step Setup

### Step 1: Run Setup
Double-click **`setup.bat`** (or run it in a terminal). The script will automatically:
- Check for and install Python if missing.
- Set up a clean virtual Python environment (`.venv`).
- Install dependencies and fetch Playwright browser binaries.
- Register a startup shortcut so the script runs when you log into Windows.

### Step 2: Configure Player Profiles
Open **`config/profiles.json`** and enter your player nickname and player UID:
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
