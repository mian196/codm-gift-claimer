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

## 🤖 Step 3: Understand the GitHub Actions Workflow

We've already configured your workflow file `.github/workflows/claim_rewards.yml` to:
- Automatically trigger every day.
- Fetch the secure `CODM_PROFILES` and `DISCORD_WEBHOOK_URL` values at runtime.
- Run Playwright and execute the python claimer in the cloud.

---

## ⏰ Step 4: Configuring Your Cron Schedule (UTC vs Local)

GitHub Actions runs schedules on **Coordinated Universal Time (UTC)**. 

To edit when the script runs, open `.github/workflows/claim_rewards.yml` and modify the `cron` parameter. Here is how to convert **5:00 AM local time** to UTC for various timezones:

| Target Local Time | Timezone | UTC Cron Expression |
| :--- | :--- | :--- |
| **5:00 AM** | Pakistan Standard Time (PKT, UTC+5) | `- cron: '0 0 * * *'` (midnight UTC) |
| **5:00 AM** | Greenwich Mean Time (GMT, UTC+0) | `- cron: '0 5 * * *'` (5:00 AM UTC) |
| **5:00 AM** | Eastern Standard Time (EST, UTC-5) | `- cron: '0 10 * * *'` (10:00 AM UTC) |
| **5:00 AM** | Pacific Standard Time (PST, UTC-8) | `- cron: '0 13 * * *'` (1:00 PM UTC) |

> [!NOTE]
> GitHub Actions schedules can sometimes be slightly delayed by a few minutes depending on server load on GitHub's side. This is normal and expected.

---

## 🚀 Step 5: Manually Trigger the Workflow (Verification)

To verify that everything is configured correctly without waiting for 5:00 AM:

1. Go to your repository on GitHub.
2. Click the **Actions** tab at the top.
3. In the left sidebar, click **CODM Daily Gift Claimer**.
4. Click the **Run workflow** dropdown button on the right side and click **Run workflow**.
5. Once the job completes, check your Discord channel! You'll receive a gorgeous rich embed showing the claim status.
