# Deployment Guide for Premium Vault Bot on Render

This guide will help you deploy your Telegram bot with the web-based admin panel to Render.

## Prerequisites

1. A [Render account](https://dashboard.render.com/register) (free tier available)
2. Your project code pushed to a GitHub repository
3. Your Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

## Step-by-Step Deployment

### Option 1: Using render.yaml (Recommended - Easiest)

1. **Push your code to GitHub**
   - Make sure all files including `render.yaml` are committed and pushed

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click **"New +"** → **"Blueprint"**
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file

3. **Set Environment Variables**
   - After connecting, you'll be prompted to set environment variables
   - **Required:** 
     - `BOT_TOKEN` - Your Telegram bot token from BotFather
     - `ADMIN_USERNAME` - Your desired admin panel username
     - `ADMIN_PASSWORD` - A strong password for the admin panel
   - **Auto-generated:** 
     - `FLASK_SECRET_KEY` will be auto-generated (you can leave it)

4. **Deploy**
   - Click **"Apply"** to start the deployment
   - Wait for the build to complete (this may take 5-10 minutes)

5. **Access Your Admin Panel**
   - Once deployed, your app will be live at: `https://premium-vault-bot.onrender.com`
   - The admin panel will be accessible at the root URL

---

### Option 2: Manual Setup (More Control)

1. **Push your code to GitHub**
   - Commit and push all changes

2. **Create a New Web Service**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click **"New +"** → **"Web Service"**
   - Connect your GitHub repository
   - Select the repository containing your bot

3. **Configure Build Settings**
   
   **Name:** `premium-vault-bot` (or your preferred name)
   
   **Environment:** `Python 3`
   
   **Region:** Choose closest to your users
   
   **Branch:** `main` (or your default branch)
   
   **Build Command:**
   ```bash
   pip install -r requirements.txt && cd admin-panel && npm install && npm run build && cd ..
   ```
   
   **Start Command:**
   ```bash
   gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120 api_server:app
   ```

4. **Set Environment Variables**
   - In the **Environment** section, add:
   
   | Key | Value |
   |-----|-------|
   | `BOT_TOKEN` | Your Telegram bot token from BotFather |
   | `ADMIN_USERNAME` | Your desired admin panel username (e.g., admin) |
   | `ADMIN_PASSWORD` | A strong password for admin access |
   | `FLASK_SECRET_KEY` | Generate a random string (e.g., use [this tool](https://randomkeygen.com/)) |
   | `PYTHON_VERSION` | `3.10.0` |

5. **Choose Plan**
   - Select **Free** tier for testing (will spin down after inactivity)
   - Or select **Starter** ($7/month) for always-on service

6. **Deploy**
   - Click **"Create Web Service"**
   - Wait for deployment to complete

---

## Post-Deployment Steps

### 1. Access the Admin Panel

- Visit your deployed URL: `https://your-app-name.onrender.com`
- Log in with the `ADMIN_USERNAME` and `ADMIN_PASSWORD` you set in environment variables
- You should see the dashboard with credentials management

### 2. Configure Your Telegram Bot

1. In the admin panel, go to **Settings**
2. Add your Telegram User ID (get it from [@userinfobot](https://t.me/userinfobot))
3. Now your Telegram bot and admin panel are connected!

---

## Important Notes

### About the Free Tier

- **Render's free tier will spin down after 15 minutes of inactivity**
- First request after spin-down may take 30-60 seconds
- For production use, upgrade to the Starter plan ($7/month) for always-on service

### Telegram Bot Behavior

- **The Telegram bot will ONLY work when the web service is running**
- If using free tier, the bot will stop responding after 15 minutes of inactivity
- Consider upgrading to Starter plan for 24/7 bot availability

### Logs and Debugging

- View logs in Render Dashboard → Your Service → Logs tab
- Check for errors during build or runtime
- Common issues:
  - **404 errors**: Make sure the React app built successfully
  - **Build failures**: Check that Node.js and Python versions are correct
  - **Bot not responding**: Verify `BOT_TOKEN` environment variable is set correctly

---

## Troubleshooting

### Build Fails During npm install

**Error:** `npm install` fails in admin-panel

**Solution:** 
- Check that `admin-panel/package.json` exists
- Verify Node.js version compatibility (Render uses Node 18+ by default)

### Admin Panel Shows 404

**Possible causes:**
1. React app didn't build: Check build logs
2. Flask not serving static files: Verify `api_server.py` has the catch-all route
3. Build output directory mismatch: Ensure `admin-panel/dist` exists

**Solutions:**
- Review build logs for errors during `npm run build`
- Verify the build command completed successfully
- Check that `admin-panel/dist/index.html` exists after build

### Telegram Bot Not Responding

**Possible causes:**
1. `BOT_TOKEN` not set or incorrect
2. Service is sleeping (free tier)
3. Bot trying to run but encountering errors

**Solutions:**
- Double-check `BOT_TOKEN` in environment variables
- Check service logs for Python errors
- Upgrade to Starter plan to prevent sleeping
- Test the bot immediately after deployment

### 502 Bad Gateway

**Cause:** Service crashed or didn't start properly

**Solutions:**
- Check logs for Python errors
- Verify all dependencies installed correctly
- Make sure `gunicorn` is in `requirements.txt`

---

## Updating Your Deployment

Render automatically redeploys when you push to your connected GitHub branch:

1. Make changes locally
2. Commit and push to GitHub
3. Render will automatically detect changes and redeploy
4. Monitor the deployment in the Render dashboard

---

## Cost Breakdown

| Plan | Cost | Features |
|------|------|----------|
| **Free** | $0/month | Spins down after 15 min inactivity, 750 hours/month |
| **Starter** | $7/month | Always on, 24/7 availability, no spin down |
| **Standard** | $25/month | More resources, faster performance |

---

## Support

If you encounter issues:
1. Check the [Render documentation](https://render.com/docs)
2. Review your service logs in the Render dashboard
3. Verify all environment variables are set correctly
4. Check that your GitHub repository is up to date

---

## Security Best Practices

1. **Never commit secrets** to your repository
   - `admin_credentials.json` is now in `.gitignore` for security
   - Admin credentials are loaded from environment variables (`ADMIN_USERNAME`, `ADMIN_PASSWORD`)
2. Use Render's environment variables for all sensitive data
3. Generate strong passwords for admin accounts
4. Use unique, strong values for `ADMIN_PASSWORD` (minimum 12 characters recommended)
5. Enable 2FA on your Render account
6. Regularly update your dependencies
7. Never share your `BOT_TOKEN` or `ADMIN_PASSWORD` publicly

---

Your Premium Vault Bot is now ready to serve users 24/7 with a beautiful admin panel!
