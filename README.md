# 🎮 Call of Duty: Mobile Daily Free Gift Claimer

[![Codashop & CODM Store Compatible](https://img.shields.io/badge/Store-CODM%20Official-gold?style=for-the-badge&logo=activision)](https://store.callofdutymobile.com/)
[![Playwright Powered](https://img.shields.io/badge/Engine-Playwright-green?style=for-the-badge&logo=playwright)](https://playwright.dev/)
[![GitHub Actions Automated](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue?style=for-the-badge&logo=github-actions)](https://github.com/features/actions)

An elegant, automated, and secure Python script designed to automatically claim the **Daily Free Gift** on the official [Call of Duty: Mobile Web Store](https://store.callofdutymobile.com/). Designed for local daily execution or zero-touch cloud scheduling using **GitHub Actions**.

---

## 🌟 Key Features

* **⚡ Zero-Touch Automation:** Automatically navigates, submits UIDs, handles dynamic page states, and claims rewards without manual intervention.
* **🛡️ Secure GitHub Actions Integration:** Keep your Player UIDs completely hidden from the public eye. Uses GitHub Repository Secrets to load profiles dynamically in the cloud.
* **🚀 Optional Login Flow:** Gracefully handles store interfaces without requiring distinct login buttons by using fallback standard keyboard actions (e.g., automated `Enter` submit validation).
* **📸 Screenshot Archiving & Unified Logs:** Captures full-page screenshots on successes and failures and maintains rolling logs.
* **📦 Light Dependencies:** Retains an exceptionally small footprint with zero external packaging overhead. 

---

## 📂 Project Structure

```
├── .github/workflows/   # GitHub Actions automated workflows
├── config/              # Local configurations (ignored in git)
│   └── profiles.json    # Local player profiles
├── logs/                # Rolling logs and claim screenshot archives
├── state/               # Local daily claim state tracking
├── tests/               # 100% green unit and integration test suite
├── claimer.py           # Core automated claiming script
└── SETUP.md             # Complete step-by-step setup guide
```

---

## 🚀 Quick Local Run

To run the claimer on your local machine:

1. **Install dependencies:**
   ```bash
   pip install playwright
   python -m playwright install chromium
   ```

2. **Configure your profiles:**
   Create a `config/profiles.json` file:
   ```json
   [
     { "name": "YourNickname", "uid": "1234567890123456789" }
   ]
   ```

3. **Run the script:**
   ```bash
   python claimer.py
   ```
   Add the `--visible` or `-v` flag to view the automated browser window.

---

## 🤖 GitHub Actions Automation (5:00 AM Daily)

You don't need to run this locally! You can run this completely free in the cloud using **GitHub Actions**. 

> [!TIP]
> Your Player UIDs can be stored securely as private repository secrets so that no one else can see them, even if your repository is public.

👉 **Follow the step-by-step [SETUP.md](file:///D:/Github-Tools/CODM-FREEGIFT/SETUP.md) guide to configure your GitHub Actions workflow in under 3 minutes!**

---

## 🧪 Testing

The codebase comes equipped with a comprehensive 30-case test suite covering all modules:
```bash
python -m pytest
```

---

## ⚖️ License & Disclaimer

This project is for educational and automation utility purposes. It is not affiliated with, authorized, or endorsed by Activision or Coda Payments. Use responsibly.
