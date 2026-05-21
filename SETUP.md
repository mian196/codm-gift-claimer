# 🛠️ GitHub Actions Setup & Security Guide

This guide will show you how to securely set up the **CODM Daily Free Gift Claimer** to run automatically in the cloud every day at **5:00 AM** and send gorgeous, instant alerts to your **Discord** channel.

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
       "name": "YourNickname",
       "uid": "1234567890123456789"
     }
   ]
   ```
   *Note: You can add multiple profiles inside the JSON array if you want to claim for multiple accounts!*
6. Click **Add secret**. Your credentials are now encrypted and completely secure!

---

## 💬 Step 2: Set Up Discord Webhook Notifications (Optional)

Receive instant status notifications in your Discord server whenever a claim attempt is made.

1. In Discord, navigate to the channel where you want to receive logs.
2. Open the channel settings (Edit Channel ⚙️) -> **Integrations** -> **Webhooks**.
3. Click **Create Webhook** (or **New Webhook**).
4. Give it a custom name (e.g., `CODM Claimer`), and copy the **Webhook URL**.
5. Back in your GitHub repository, navigate to **Settings** ⚙️ -> **Secrets and variables** -> **Actions**.
6. Click **New repository secret**.
7. Set the **Name** to:
   ```env
   DISCORD_WEBHOOK_URL
   ```
8. Set the **Value** to your copied Discord Webhook URL.
9. Click **Add secret**.

---

## 🔑 Step 3: Create a Personal Access Token (PAT) — Required for Dynamic Scheduling

> [!IMPORTANT]
> GitHub **blocks the default `GITHUB_TOKEN`** from editing or committing to workflow files (`.github/workflows/`) for security reasons. The Dynamic Cron Scheduler needs a Personal Access Token (PAT) to push randomized schedule updates each day.

### Create the Token

1. Go to your GitHub profile **Settings** (top-right avatar menu).
2. Scroll down and click **Developer settings** in the left sidebar.
3. Go to **Personal access tokens** → **Tokens (classic)**.
4. Click **Generate new token (classic)**.
5. Give it a descriptive name, e.g. `CODM Scheduler Token`.
6. Set an expiration (e.g. **90 days** or **No expiration** for fully automated setup).
7. Under **Select scopes**, check:
   - ✅ `repo` — Full control of private repositories
   - ✅ `workflow` — Update GitHub Action workflows
8. Click **Generate token** and **copy it immediately** (it won't be shown again!).

### Add the Token as a Secret

1. Go to your repository on GitHub.
2. Navigate to **Settings** ⚙️ → **Secrets and variables** → **Actions**.
3. Click **New repository secret**.
4. Set the **Name** to:
   ```env
   PAT_TOKEN
   ```
5. Set the **Value** to your copied Personal Access Token.
6. Click **Add secret**.

---

## 🤖 Step 4: Upgraded Stealth Dual-Workflow Architecture

We have implemented an industry-grade **dynamic scheduler randomizer** using a dual-workflow architecture for ultimate bot-detection evasion:

1. **Daily Planner (`schedule_randomizer.yml`)**: Runs daily at **0:00 UTC** (5:00 AM PKT). It dynamically selects a completely random hour and minute (e.g. 14:37 UTC, 3:12 UTC) for that day, updates the cron trigger in the claiming workflow, and securely pushes the updated configuration back to your repository using your `PAT_TOKEN`.
2. **Rewards Claimer (`claim_rewards.yml`)**: Natively triggered at the dynamically updated random time. The Python script runs immediately upon triggering with no sleep overhead, while all randomized human-like mouse click delays remain active.

> [!NOTE]
> GitHub Actions scheduled runs can sometimes be delayed by a few minutes depending on server load. This is normal behaviour.

---

## ⏰ Step 5: Manually Re-shuffle the Daily Schedule (Optional)

If you want to immediately pick a new random execution time without waiting for the midnight planner:

1. Navigate to the **Actions** tab in your repository.
2. Under the workflows list, click **Dynamic Cron Scheduler**.
3. Click the **Run workflow** dropdown on the right and click **Run workflow**.
4. The workflow picks a new random time, updates `claim_rewards.yml`, and pushes the commit (tagged `[skip ci]` to prevent build loops).

---

## 🚀 Step 6: Manually Trigger the Claimer Workflow (Verification)

To verify that everything is working without waiting for the scheduled time:

1. Go to your repository on GitHub.
2. Click the **Actions** tab at the top.
3. In the left sidebar, click **CODM Daily Gift Claimer**.
4. Click the **Run workflow** dropdown button and click **Run workflow**.
5. Once the job completes, check your Discord channel — you'll receive a rich embed showing the claim status.
