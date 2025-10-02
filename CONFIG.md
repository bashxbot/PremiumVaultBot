# Premium Vault Bot - Configuration Guide

## Quick Start

### 1. Get Your Telegram Bot Token
- Open Telegram and search for @BotFather
- Send `/newbot` and follow the instructions
- Copy the bot token provided

### 2. Find Your Telegram User ID
To become an admin, you need your Telegram user ID:
- Open Telegram and search for @userinfobot
- Send `/start` to get your user ID
- Copy the number (e.g., 123456789)

### 3. Configure the Bot

**Option A: Using Environment Variables (Recommended)**
```bash
export BOT_TOKEN="your_bot_token_here"
export ADMIN_IDS="your_user_id_here"
```

**Option B: First User Auto-Admin (For Testing)**
If you don't set ADMIN_IDS, the first user who starts the bot will automatically become an admin.

### 4. Run the Bot
```bash
cd bot && python main.py
```

## Configuration Options

### BOT_TOKEN
Your Telegram bot token from BotFather.
- **Required**: Yes
- **Default**: Hardcoded token (not recommended for production)
- **Example**: `8039142646:AAFpnOAX197pxqMqWjw99o-o25oD0SA1BC8`

### ADMIN_IDS
Comma-separated list of Telegram user IDs who can access admin features.
- **Required**: No (but recommended)
- **Default**: Empty (first user becomes admin)
- **Example**: `123456789,987654321`

## Admin Features

Once you're an admin, you can:
- 🔑 **Generate Keys**: Create redemption keys for platforms
- 📊 **Bot Stats**: View usage statistics
- 📋 **List All Keys**: See all generated keys by platform
- 🗑️ **Clear Expired Keys**: Remove expired keys from database
- 🎁 **Start Giveaway**: Launch timed giveaways with winners
- 🛑 **Stop Giveaway**: End active giveaways
- ❌ **Revoke Key**: Remove specific keys
- 📢 **Broadcast**: Send messages to all users
- 🚫 **Ban User**: Block users from the bot

## User Features

Regular users can:
- ✅ **Join Required Channels**: Must join all channels to access the bot
- 🎁 **Redeem Keys**: Enter redemption codes to get premium accounts
- 📊 **My Stats**: View personal redemption history
- 🎁 **Join Giveaways**: Participate in active giveaways

## File Structure

```
project/
├── bot/
│   ├── main.py       # Main bot file
│   ├── admin.py      # Admin functions
│   └── users.py      # User functions
├── credentials/
│   ├── netflix.json      # Netflix accounts
│   ├── crunchyroll.json  # Crunchyroll accounts
│   ├── spotify.json      # Spotify accounts
│   └── wwe.json          # WWE accounts
├── data/                 # Generated at runtime
│   ├── keys.json        # Generated keys
│   ├── users.json       # User database
│   ├── banned.json      # Banned users
│   └── giveaway.json    # Giveaway data
└── .env.example          # Example environment file
```

## Adding Credentials

Edit the JSON files in the `credentials/` directory to add premium accounts:

```json
[
  {
    "email": "account@example.com",
    "password": "password123",
    "status": "active"
  }
]
```

## Required Channels

Users must join these channels before using the bot:
- @PremiumVaultFigs
- @accountvaultportal
- @PremiumVaultBackup
- @PremiumVault

## Security Notes

1. **Never commit your bot token** to version control
2. **Use environment variables** for sensitive data
3. **Rotate credentials** regularly
4. **Monitor admin access** and keep ADMIN_IDS up to date
5. **Keep the credentials/** directory secure

## Troubleshooting

**Bot doesn't respond:**
- Check if the bot is running
- Verify the bot token is correct
- Check console logs for errors

**Can't access admin features:**
- Verify your user ID is in ADMIN_IDS
- Restart the bot after changing ADMIN_IDS
- Check if you're using the correct Telegram account

**Key redemption fails:**
- Ensure credentials are available in the platform JSON file
- Check that the key is active and not expired
- Verify user has joined all required channels
