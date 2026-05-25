# 🎮 Call of Duty: Mobile Daily Free Gift Claimer

[![Store Compatibility](https://img.shields.io/badge/Store-CODM%20Official-gold?style=for-the-badge&logo=activision)](https://store.callofdutymobile.com/)
[![Playwright Powered](https://img.shields.io/badge/Engine-Playwright-green?style=for-the-badge&logo=playwright)](https://playwright.dev/)
[![GitHub Actions Automated](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue?style=for-the-badge&logo=github-actions)](https://github.com/features/actions)
[![Discord Webhook Integrable](https://img.shields.io/badge/Notifications-Discord-blueviolet?style=for-the-badge&logo=discord)](https://discord.com/)

An elegant, automated, and highly secure Python script designed to automatically claim the **Daily Free Gift** on the official [Call of Duty: Mobile Web Store](https://store.callofdutymobile.com/). Optimized for **zero-touch cloud scheduling using GitHub Actions** with instant Discord status notifications.

---

## 🌟 Key Features

* **⚡ Zero-Touch Cloud Automation:** Automatically runs daily on GitHub Actions at a random time after 5:00 AM PKT.
* **🛡️ Secure GitHub Actions Integration:** Keep your Player UIDs completely hidden from the public eye. Uses encrypted GitHub Repository Secrets to load profiles dynamically.
* **💬 Discord Status Webhook Alerts:** Get instant, gorgeous rich embed alerts directly in your Discord channel showing successful claims or details of failures.
* **🚀 Optional Login Flow:** Gracefully handles store interfaces without requiring distinct login buttons by using fallback standard keyboard actions (e.g., automated `Enter` submit validation).
* **📦 Zero Local Bloat:** Does not save massive screenshot images or clutter your repository with local state/JSON logs.

---

## 📂 Project Structure

```
├── .github/workflows/   # GitHub Actions automated workflows
├── tests/               # 100% green unit and integration test suite
├── claimer.py           # Core automated claiming script
├── requirements.txt     # Python project dependencies
├── README.md            # Premium repository index
└── SETUP.md             # Complete step-by-step setup guide
```

---

## 🤖 How to Automate on GitHub Actions

You don't need to run this locally! You can run this completely free in the cloud using **GitHub Actions**.

> [!TIP]
> Your Player UIDs and Discord Webhook token are stored securely as private repository secrets so that no one else can see them, even if your repository is public.

👉 **Follow the step-by-step [SETUP.md](SETUP.md) guide to configure your GitHub Actions workflow in under 3 minutes!**

---

## 🧪 Testing

The codebase comes equipped with a comprehensive 19-case test suite covering all modules:
```bash
python -m pytest
```

---

## ⚖️ License & Disclaimer

This project is for educational and automation utility purposes. It is not affiliated with, authorized, or endorsed by Activision. Use responsibly.
