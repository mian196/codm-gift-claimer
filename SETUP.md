# 🛠️ GitHub Actions Setup & Security Guide

This guide will show you how to securely set up the **CODM Daily Free Gift Claimer** to run automatically in the cloud every day at **5:00 AM** using **GitHub Actions**.

---

## 🔒 Step 1: Secure Your Player UIDs in GitHub

To prevent anyone else from seeing your Call of Duty: Mobile Player UIDs, you should **never** commit them to your repository. Instead, store them as a **GitHub Repository Secret**.

1. Go to your repository on GitHub.
2. Navigate to **Settings** ⚙️ -> **Secrets and variables** -> **Actions**.
3. Click the **New repository secret** button.
4. Set the **Name** of the secret to precisely:
   ```env
   CODM_PROFILES
   ```
5. Set the **Value** of the secret to a JSON array containing your profiles (with names and UIDs):
   ```json
   [
     {
       "name": "Muzammal",
       "uid": "6922341873420271617"
     }
   ]
   ```
   *Note: You can add multiple profiles inside the JSON array if you want to claim for multiple accounts!*
6. Click **Add secret**. Your credentials are now encrypted and completely secure!

---

## 🤖 Step 2: Create the GitHub Actions Workflow

To tell GitHub to run the claimer script automatically every day at 5:00 AM, create a workflow file.

1. In the root of your repository, create a directory structure: `.github/workflows/`
2. Create a file inside that directory named `claim_rewards.yml`:
   ```yaml
   name: CODM Daily Gift Claimer

   on:
     schedule:
       # Runs every day at 5:00 AM UTC (adjust the hour to fit your local time)
       - cron: '0 5 * * *'
     workflow_dispatch:
       # Allows you to manually trigger the claim flow from the GitHub Actions tab

   jobs:
     claim:
       runs-on: ubuntu-latest

       steps:
       - name: Check out repository code
         uses: actions/checkout@v4

       - name: Set up Python
         uses: actions/setup-python@v5
         with:
           python-version: '3.11'

       - name: Install dependencies
         run: |
           python -m pip install --upgrade pip
           pip install playwright pytest pytest-mock anyio
           python -m playwright install chromium
           npx playwright install-deps chromium

       - name: Execute claimer script
         env:
           # Pass your secure profiles from GitHub Secrets as an environment variable
           CODM_PROFILES: ${{ secrets.CODM_PROFILES }}
         run: python claimer.py
   ```

---

## ⏰ Step 3: Understanding the Cron Schedule (UTC vs Local)

GitHub Actions runs schedules on **Coordinated Universal Time (UTC)**. 

If you want the workflow to run at **5:00 AM in your local timezone**, you need to convert it to UTC. Here are some examples:

| Target Local Time | Timezone | UTC Cron Expression |
| :--- | :--- | :--- |
| **5:00 AM** | Pakistan Standard Time (PKT, UTC+5) | `0 0 * * *` (midnight UTC) |
| **5:00 AM** | Greenwich Mean Time (GMT, UTC+0) | `0 5 * * *` (5:00 AM UTC) |
| **5:00 AM** | Eastern Standard Time (EST, UTC-5) | `0 10 * * *` (10:00 AM UTC) |
| **5:00 AM** | Pacific Standard Time (PST, UTC-8) | `0 13 * * *` (1:00 PM UTC) |

> [!NOTE]
> GitHub Actions schedules can sometimes be delayed by a few minutes depending on server load on GitHub's end. This is normal and expected.

---

## 🚀 Step 4: Manually Trigger the Workflow (Verification)

To verify that everything is configured correctly without waiting for 5:00 AM:

1. Go to your repository on GitHub.
2. Click the **Actions** tab at the top.
3. In the left sidebar, click **CODM Daily Gift Claimer**.
4. Click the **Run workflow** dropdown button on the right side and click **Run workflow**.
5. Once the job completes, click into the logs to verify that the script successfully logged in and claimed the gift!
