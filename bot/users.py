import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError


def get_project_root():
    """Get the project root directory (parent of bot folder)"""
    import os
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Required channels
REQUIRED_CHANNELS = [
    "-1002937378958",  # ACCOUNT VAULT NETWORK - portal
    "-1002758495265",  # PREMIUMS VAULT - main
    "-1003084077701",  # PREMIUM VAULT BACKUP - backup
    "-1003039286362"   # PREMIUM VAULT FIGS - config
]

# Database files
KEYS_FILE = 'data/keys.json'
USERS_FILE = 'data/users.json'
BANNED_FILE = 'data/banned.json'
GIVEAWAY_FILE = 'data/giveaway.json'


def ensure_data_files():
    """Ensure all data files exist"""
    os.makedirs('data', exist_ok=True)

    if not os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, 'w') as f:
            json.dump([], f)

    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)

    if not os.path.exists(BANNED_FILE):
        with open(BANNED_FILE, 'w') as f:
            json.dump([], f)

    if not os.path.exists(GIVEAWAY_FILE):
        with open(GIVEAWAY_FILE, 'w') as f:
            json.dump({"active": False}, f)


def load_json(filename):
    """Load JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        return [] if filename != GIVEAWAY_FILE and filename != USERS_FILE else (
            {} if filename == USERS_FILE else {
                "active": False
            })


def save_json(filename, data):
    """Save JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def is_banned(user_id, username):
    """Check if user is banned"""
    banned = load_json(BANNED_FILE)
    return user_id in banned or f"@{username}" in banned if username else user_id in banned


async def check_channel_membership(update: Update,
                                   context: ContextTypes.DEFAULT_TYPE):
    """Check if user has joined all required channels"""
    user_id = update.effective_user.id
    all_joined = True

    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                all_joined = False
                break
        except TelegramError:
            # If we can't check membership, assume not joined
            all_joined = False
            break

    return all_joined


async def user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user welcome message"""
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username

    ensure_data_files()

    # Check if user is banned
    if is_banned(user_id, username):
        await update.message.reply_text(
            "🚫 <b>Access Denied</b>\n\n"
            "❌ You have been banned from using this bot.",
            parse_mode='HTML')
        return

    # Register user
    users = load_json(USERS_FILE)
    if str(user_id) not in users:
        users[str(user_id)] = {
            "username": username,
            "joined_at": datetime.now().isoformat(),
            "redeemed_keys": []
        }
        save_json(USERS_FILE, users)

    # Import is_admin from admin module
    from admin import is_admin

    # Skip channel check entirely for admins - show main menu directly
    if is_admin(user_id):
        await show_main_menu(update, context)
        return

    # Check channel membership for regular users
    has_joined = await check_channel_membership(update, context)

    if not has_joined:
        channel_buttons = [
            [InlineKeyboardButton("🔗 Join Channel Portal", url="https://t.me/accountvaultportal")],
            [InlineKeyboardButton("🔗 Join Channel Main", url="https://t.me/+RKjw0ypr_e9lZTI0")],
            [InlineKeyboardButton("🔗 Join Channel Backup", url="https://t.me/+yiYViAOknS9lZjlk")],
            [InlineKeyboardButton("🔗 Join Channel Config", url="https://t.me/+gxVbPeU842ZkNmU0")],
            [InlineKeyboardButton("✅ I have joined all, continue", callback_data="user_verify_channels")]
        ]

        reply_markup = InlineKeyboardMarkup(channel_buttons)

        welcome_text = (
            "🚀 <b>Welcome to Premium Vault!</b>\n\n"
            "🎁 To access premium accounts, please join all our channels below.\n\n"
            "✨ It only takes a moment - then enjoy unlimited access!")

        await update.message.reply_text(text=welcome_text,
                                        reply_markup=reply_markup,
                                        parse_mode='HTML')
    else:
        await show_main_menu(update, context)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu to user"""
    user = update.effective_user

    keyboard = [
        [
            InlineKeyboardButton("🎁 Redeem Key",
                                 callback_data="user_redeem_key")
        ], [InlineKeyboardButton("📊 My Stats", callback_data="user_my_stats")],
        [
            InlineKeyboardButton("📢 Channel Portal",
                                 url="https://t.me/accountvaultportal"),
            InlineKeyboardButton("📢 Channel Main",
                                 url="https://t.me/+RKjw0ypr_e9lZTI0")
        ],
        [
            InlineKeyboardButton("📢 Channel Backup",
                                 url="https://t.me/+yiYViAOknS9lZjlk"),
            InlineKeyboardButton("📢 Channel Config",
                                 url="https://t.me/+gxVbPeU842ZkNmU0")
        ], 
        [InlineKeyboardButton("❓ Help", callback_data="user_help")],
        [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/BEASTSEC")]
    ]

    # Check if there's an active giveaway
    giveaway = load_json(GIVEAWAY_FILE)
    if giveaway.get('active'):
        keyboard.insert(1, [
            InlineKeyboardButton("🎁 Join Giveaway",
                                 callback_data="user_join_giveaway")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    main_text = ("🎮 <b>Premium Vault - Main Menu</b> 🎮\n\n"
                 f"👤 <b>User:</b> {user.mention_html()}\n\n"
                 "✨ <b>What would you like to do?</b>\n\n"
                 "🔑 Redeem premium account keys\n"
                 "📊 Check your statistics\n"
                 "🎁 Participate in giveaways\n"
                 "❓ Get help and support\n\n"
                 "👇 Select an option below:")

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=main_text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(text=main_text,
                                        reply_markup=reply_markup,
                                        parse_mode='HTML')


async def handle_user_callback(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
    """Handle user callback queries"""
    query = update.callback_query
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username

    ensure_data_files()

    # Check if user is banned
    if is_banned(user_id, username):
        await query.answer("🚫 You have been banned!", show_alert=True)
        return

    data = query.data

    if data == "user_verify_channels":
        await verify_channels(update, context)

    elif data == "user_main":
        await show_main_menu(update, context)

    elif data == "user_redeem_key":
        await query.answer()
        context.user_data['redeem_step'] = 'key'

        keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text="🎁 <b>Redeem Key</b>\n\n"
            "🔑 Please send your redemption key in the format:\n"
            "<code>PLATFORM-XXXX-XXXX-XXXX</code>\n\n"
            "📝 Example: <code>NETFLIX-A2D8-FA2F-VV82</code>",
            reply_markup=reply_markup,
            parse_mode='HTML')

    elif data == "user_my_stats":
        await show_user_stats(update, context)

    elif data == "user_help":
        await show_help(update, context)

    elif data == "user_join_giveaway":
        await join_giveaway(update, context)

    else:
        await query.answer("❌ Unknown action!", show_alert=True)


async def verify_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify user has joined all channels"""
    query = update.callback_query

    has_joined = await check_channel_membership(update, context)

    if has_joined:
        await query.answer("✅ Verified! Welcome!", show_alert=True)
        await show_main_menu(update, context)
    else:
        await query.answer("❌ Please join all channels first!",
                           show_alert=True)


async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)
    users = load_json(USERS_FILE)

    user_data = users.get(user_id, {})
    redeemed_keys = user_data.get('redeemed_keys', [])

    stats_text = (
        "📊 <b>Your Statistics</b>\n\n"
        f"🎯 <b>Total Keys Redeemed:</b> {len(redeemed_keys)}\n"
        f"📅 <b>Member Since:</b> {user_data.get('joined_at', 'Unknown')[:10]}\n\n"
    )

    if redeemed_keys:
        stats_text += "🔑 <b>Redeemed Keys:</b>\n"
        for key_info in redeemed_keys[-5:]:  # Show last 5 redeemed keys
            platform = key_info.get('platform', 'Unknown')
            redeemed_at = key_info.get('redeemed_at', 'Unknown')[:10]
            stats_text += f"• {platform} - {redeemed_at}\n"

        if len(redeemed_keys) > 5:
            stats_text += f"\n... and {len(redeemed_keys) - 5} more"
    else:
        stats_text += "❌ <i>You haven't redeemed any keys yet!</i>\n\n"
        stats_text += "💡 Use /redeem to redeem your first key!"

    keyboard = [[
        InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=stats_text,
                                  reply_markup=reply_markup,
                                  parse_mode='HTML')


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information"""
    query = update.callback_query
    await query.answer()

    help_text = ("❓ <b>Help & Information</b>\n\n"
                 "🎮 <b>How to use this bot:</b>\n\n"
                 "1️⃣ <b>Join All Channels</b>\n"
                 "   Make sure you're a member of all required channels\n\n"
                 "2️⃣ <b>Redeem Keys</b>\n"
                 "   Use the 'Redeem Key' button to enter your key code\n"
                 "   Format: PLATFORM-XXXX-XXXX-XXXX\n\n"
                 "3️⃣ <b>Get Premium Accounts</b>\n"
                 "   Valid keys will give you premium account credentials\n\n"
                 "4️⃣ <b>Join Giveaways</b>\n"
                 "   Participate in giveaways for free keys!\n\n"
                 "💡 <b>Need more help?</b>\n"
                 "Contact our support team in the channels!\n\n"
                 "🎁 <b>Available Platforms:</b>\n"
                 "🎬 Netflix\n"
                 "🍜 Crunchyroll\n"
                 "🎵 Spotify\n"
                 "🤼 WWE\n"
                 "... and more!")

    keyboard = [[
        InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=help_text,
                                  reply_markup=reply_markup,
                                  parse_mode='HTML')


async def join_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Join active giveaway"""
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)
    giveaway = load_json(GIVEAWAY_FILE)

    if not giveaway.get('active'):
        await query.edit_message_text(
            text="❌ <b>No Active Giveaway</b>\n\n"
            "There's no active giveaway right now.\n\n"
            "Check back later!",
            parse_mode='HTML')
        return

    participants = giveaway.get('participants', [])

    if user_id in participants:
        await query.answer("⚠️ You're already in this giveaway!",
                           show_alert=True)
        return

    participants.append(user_id)
    giveaway['participants'] = participants
    save_json(GIVEAWAY_FILE, giveaway)

    keyboard = [[
        InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"🎁 <b>Giveaway Entry Confirmed!</b>\n\n"
        f"✅ You've successfully joined the giveaway!\n\n"
        f"🏆 <b>Winners:</b> {giveaway.get('winners', 1)}\n"
        f"⏰ <b>Ends:</b> {giveaway.get('end_time', 'Soon')[:19]}\n\n"
        f"🍀 Good luck!",
        reply_markup=reply_markup,
        parse_mode='HTML')


async def handle_user_message(update: Update,
                              context: ContextTypes.DEFAULT_TYPE):
    """Handle user text messages"""
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username

    ensure_data_files()

    # Check if user is banned
    if is_banned(user_id, username):
        await update.message.reply_text(
            "🚫 <b>Access Denied</b>\n\n"
            "❌ You have been banned from using this bot.",
            parse_mode='HTML')
        return

    # Import is_admin from admin module
    from admin import is_admin

    # Skip channel check entirely for admins
    if not is_admin(user_id):
        # Check channel membership for regular users
        has_joined = await check_channel_membership(update, context)
        if not has_joined:
            await update.message.reply_text(
                "⚠️ <b>Access Restricted</b>\n\n"
                "❌ You must join all required channels first!\n\n"
                "Use /start to see the channels and join them.",
                parse_mode='HTML')
            return

    # Handle key redemption
    if context.user_data.get('redeem_step') == 'key':
        await redeem_key(update, context, update.message.text)
        context.user_data.pop('redeem_step', None)


async def redeem_key(update: Update, context: ContextTypes.DEFAULT_TYPE,
                     key_code):
    """Redeem a key"""
    user_id = str(update.effective_user.id)
    key_code = key_code.strip().upper()

    keys = load_json(KEYS_FILE)
    users = load_json(USERS_FILE)

    # Find the key
    key_found = None
    for key in keys:
        if key['key'] == key_code:
            key_found = key
            break

    keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if not key_found:
        await update.message.reply_text(
            "❌ <b>Invalid Key</b>\n\n"
            "The key you entered is not valid.\n\n"
            "Please check and try again!",
            reply_markup=reply_markup,
            parse_mode='HTML')
        return

    # Check if key is already used
    if key_found.get('status') == 'used' or key_found.get('remaining_uses',
                                                          0) <= 0:
        await update.message.reply_text(
            "❌ <b>Key Already Used</b>\n\n"
            "This key has already been redeemed.\n\n"
            "Try another key!",
            reply_markup=reply_markup,
            parse_mode='HTML')
        return

    # Check if key is expired
    if key_found.get('status') == 'expired':
        await update.message.reply_text(
            "⏰ <b>Key Expired</b>\n\n"
            "This key has expired.\n\n"
            "Please use a valid key!",
            reply_markup=reply_markup,
            parse_mode='HTML')
        return

    # Check if user already used this key
    if user_id in key_found.get('used_by', []):
        await update.message.reply_text(
            "⚠️ <b>Already Redeemed</b>\n\n"
            "You've already redeemed this key!\n\n"
            "Try a different key.",
            reply_markup=reply_markup,
            parse_mode='HTML')
        return

    # Get credential from platform file (at project root)
    platform = key_found.get('platform', '').lower()
    project_root = get_project_root()
    credential_file = os.path.join(project_root, 'credentials', f'{platform}.json')

    if not os.path.exists(credential_file):
        await update.message.reply_text(
            "❌ <b>Error</b>\n\n"
            "No credentials available for this platform.\n\n"
            "Please contact support!",
            parse_mode='HTML')
        return

    credentials = load_json(credential_file)
    available_creds = [c for c in credentials if c.get('status') == 'active']

    keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")]]
    reply_markup_error = InlineKeyboardMarkup(keyboard)

    if not available_creds:
        await update.message.reply_text(
            "❌ <b>No Accounts Available</b>\n\n"
            "All accounts for this platform are currently used.\n\n"
            "Please try again later!",
            reply_markup=reply_markup_error,
            parse_mode='HTML')
        return

    # Give credential to user - mark as claimed immediately
    credential = available_creds[0]
    credential['status'] = 'claimed'
    credential['claimed_by'] = user_id
    credential['claimed_at'] = datetime.now().isoformat()

    # Save immediately to prevent double allocation
    save_json(credential_file, credentials)

    # Update key
    key_found['remaining_uses'] = key_found.get('remaining_uses', 1) - 1
    key_found['used_by'].append(user_id)
    key_found['redeemed_at'] = datetime.now().isoformat()

    # Add to redeemed_by list for detailed tracking
    if 'redeemed_by' not in key_found:
        key_found['redeemed_by'] = []

    key_found['redeemed_by'].append({
        'user_id': user_id,
        'username': update.effective_user.username,
        'redeemed_at': datetime.now().isoformat()
    })

    if key_found['remaining_uses'] <= 0:
        key_found['status'] = 'used'

    save_json(KEYS_FILE, keys)

    # Also update platform-specific keys file (at project root)
    platform = key_found.get('platform', '').lower()
    project_root = get_project_root()
    platform_keys_file = os.path.join(project_root, 'keys', f'{platform}.json')
    if os.path.exists(platform_keys_file):
        platform_keys = load_json(platform_keys_file)
        for pk in platform_keys:
            if pk['key'] == key_code:
                pk['remaining_uses'] = key_found['remaining_uses']
                pk['used_by'] = key_found['used_by']
                pk['redeemed_at'] = key_found['redeemed_at']
                pk['redeemed_by'] = key_found['redeemed_by']
                pk['status'] = key_found['status']
                break
        save_json(platform_keys_file, platform_keys)

    # Update user data
    if user_id not in users:
        users[user_id] = {"redeemed_keys": []}

    users[user_id].setdefault('redeemed_keys', []).append({
        "key":
        key_code,
        "platform":
        key_found.get('platform'),
        "redeemed_at":
        datetime.now().isoformat()
    })
    save_json(USERS_FILE, users)

    # Send credential to user
    platform_name = key_found.get('platform', 'Unknown')
    account_text = key_found.get('account_text', 'Premium Account')

    # Prepare success message
    success_text = (
        "🎉 <b>Key Redeemed Successfully!</b> 🎉\n\n"
        f"🎁 <b>Platform:</b> {platform_name}\n"
        f"✨ <b>Account Type:</b> {account_text}\n\n"
        f"📧 <b>Email:</b> <code>{credential['email']}</code>\n"
        f"🔑 <b>Password:</b> <code>{credential['password']}</code>\n\n"
        f"💡 <i>Tap to copy the credentials!</i>\n\n"
        f"⚠️ <b>Important:</b>\n"
        f"• Don't share these credentials\n"
        f"• Change the password if needed\n"
        f"• Enjoy your {platform_name} account!\n\n"
        f"🎮 Thank you for using Premium Vault Bot!")

    keyboard = [[
        InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Get platform logo
    project_root = get_project_root()
    platform_images = {
        'Netflix': 'assets/platform-logos/netflix.jpg',
        'Crunchyroll': 'assets/platform-logos/crunchyroll.jpg',
        'Spotify': 'assets/platform-logos/spotify.jpg',
        'WWE': 'assets/platform-logos/wwe.jpg',
        'ParamountPlus': 'assets/platform-logos/paramountplus.jpg',
        'Dazn': 'assets/platform-logos/dazn.jpg',
        'MolotovTV': 'assets/platform-logos/molotovtv.jpg',
        'DisneyPlus': 'assets/platform-logos/disneyplus.jpg',
        'PSNFA': 'assets/platform-logos/psnfa.jpg',
        'Xbox': 'assets/platform-logos/xbox.jpg'
    }
    logo_path = platform_images.get(platform_name)
    if logo_path:
        logo_path = os.path.join(project_root, logo_path)
    
    # Send with logo if available, otherwise send as text
    if logo_path and os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as logo_file:
                if update.message:
                    await update.message.reply_photo(
                        photo=logo_file,
                        caption=success_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML')
                elif update.callback_query:
                    await update.callback_query.message.reply_photo(
                        photo=logo_file,
                        caption=success_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML')
        except Exception as e:
            # If logo sending fails, send as text
            if update.message:
                await update.message.reply_text(text=success_text,
                                                reply_markup=reply_markup,
                                                parse_mode='HTML')
            elif update.callback_query:
                await update.callback_query.message.reply_text(text=success_text,
                                                              reply_markup=reply_markup,
                                                              parse_mode='HTML')
    else:
        # No logo available, send as text
        if update.message:
            await update.message.reply_text(text=success_text,
                                            reply_markup=reply_markup,
                                            parse_mode='HTML')
        elif update.callback_query:
            await update.callback_query.message.reply_text(text=success_text,
                                                          reply_markup=reply_markup,
                                                          parse_mode='HTML')


async def participate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /participate command to join active giveaway"""
    user_id = str(update.effective_user.id)
    user = update.effective_user
    username = user.username

    ensure_data_files()

    # Check if user is banned
    if is_banned(int(user_id), username):
        keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🚫 <b>Access Denied</b>\n\n"
            "❌ You have been banned from using this bot.",
            reply_markup=reply_markup,
            parse_mode='HTML')
        return

    # Import is_admin from admin module
    from admin import is_admin

    # Skip channel check entirely for admins
    if not is_admin(int(user_id)):
        # Check channel membership for regular users
        has_joined = await check_channel_membership(update, context)
        if not has_joined:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "⚠️ <b>Access Restricted</b>\n\n"
                "❌ You must join all required channels first!\n\n"
                "Use /start to see the channels and join them.",
                reply_markup=reply_markup,
                parse_mode='HTML')
            return

    giveaway = load_json(GIVEAWAY_FILE)

    keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if not giveaway.get('active'):
        await update.message.reply_text(
            "❌ <b>No Active Giveaway</b>\n\n"
            "There's no active giveaway right now.\n\n"
            "Check back later!",
            reply_markup=reply_markup,
            parse_mode='HTML')
        return

    participants = giveaway.get('participants', [])

    if user_id in participants:
        await update.message.reply_text(
            "⚠️ <b>Already Participating</b>\n\n"
            "You're already in this giveaway!\n\n"
            "Good luck! 🍀",
            reply_markup=reply_markup,
            parse_mode='HTML')
        return

    participants.append(user_id)
    giveaway['participants'] = participants
    save_json(GIVEAWAY_FILE, giveaway)

    await update.message.reply_text(
        f"🎁 <b>Giveaway Entry Confirmed!</b>\n\n"
        f"✅ You've successfully joined the giveaway!\n\n"
        f"🏆 <b>Winners:</b> {giveaway.get('winners', 1)}\n"
        f"⏰ <b>Ends:</b> {giveaway.get('end_time', 'Soon')[:19]}\n\n"
        f"🍀 Good luck!",
        reply_markup=reply_markup,
        parse_mode='HTML')


async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /redeem command with optional key parameter"""
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username

    ensure_data_files()

    # Check if user is banned
    if is_banned(user_id, username):
        keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🚫 <b>Access Denied</b>\n\n"
            "❌ You have been banned from using this bot.",
            reply_markup=reply_markup,
            parse_mode='HTML')
        return

    # Import is_admin from admin module
    from admin import is_admin

    # Skip channel check entirely for admins
    if not is_admin(user_id):
        # Check channel membership for regular users
        has_joined = await check_channel_membership(update, context)
        if not has_joined:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "⚠️ <b>Access Restricted</b>\n\n"
                "❌ You must join all required channels first!\n\n"
                "Use /start to see the channels and join them.",
                reply_markup=reply_markup,
                parse_mode='HTML')
            return

    # Check if key was provided as argument
    if context.args and len(context.args) > 0:
        key_code = context.args[0].strip().upper()
        await redeem_key(update, context, key_code)
    else:
        keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            text="🎁 <b>Redeem Key</b>\n\n"
            "🔑 Please use the command with your key:\n"
            "<code>/redeem PLATFORM-XXXX-XXXX-XXXX</code>\n\n"
            "📝 Example: <code>/redeem NETFLIX-A2D8-FA2F-VV82</code>",
            reply_markup=reply_markup,
            parse_mode='HTML')