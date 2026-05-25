# 🛠️ GitHub Actions Setup & Security Guide

This guide will show you how to securely set up the **CODM Daily Free Gift Claimer** to run automatically in the cloud every day at a random time after **5:00 AM PKT** and send gorgeous, instant alerts to your **Discord** channel.

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

## 🤖 Step 3: No-Commit Random Scheduling

The workflow no longer edits repository files to randomize the schedule, so it does **not** create daily dummy commits.

`claim_rewards.yml` checks once per hour from **5:00 AM to 11:00 PM PKT**. Each day, it calculates one random PKT claim time. Only the matching hourly check continues, waits until the selected minute if needed, and runs the claimer.

> [!NOTE]
> GitHub Actions scheduled runs can sometimes be delayed by a few minutes depending on server load. This is normal behaviour.

---

## 🚀 Step 4: Manually Trigger the Claimer Workflow (Verification)

To verify that everything is working without waiting for the scheduled time:

1. Go to your repository on GitHub.
2. Click the **Actions** tab at the top.
3. In the left sidebar, click **CODM Daily Gift Claimer**.
4. Click the **Run workflow** dropdown button and click **Run workflow**.
5. Once the job completes, check your Discord channel — you'll receive a rich embed showing the claim status.

---

## 🧪 Local Debug Run (Optional)

If the website changes and you need to watch the browser, run the claimer locally in visible mode:

```powershell
$env:CODM_PROFILES='[{"name":"Test Player","uid":"YOUR_PLAYER_UID"}]'
python claimer.py --visible --hold-open 120
```

`--visible` opens the Playwright browser window, and `--hold-open 120` keeps it open for 120 seconds after the claim attempt so you can inspect the final page state.
