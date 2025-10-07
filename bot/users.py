import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError
import sys
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_helpers import (
    get_platforms, get_platform_by_name, get_key_by_code, redeem_key as db_redeem_key,
    get_or_create_user, get_user_stats, is_user_banned as db_is_user_banned,
    get_active_credential, claim_credential, get_db_connection,
    notify_admins_key_redeemed, notify_admins_credential_claimed
)


# Setup logging
logger = logging.getLogger(__name__)


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


def ensure_data_files():
    """Compatibility function - no longer needed with PostgreSQL"""
    pass


def is_banned(user_id, username):
    """Check if user is banned"""
    return db_is_user_banned(str(user_id), username)


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

    # Check if user is banned
    if is_banned(user_id, username):
        await update.message.reply_text(
            "🚫 <b>Access Denied</b>\n\n"
            "❌ You have been banned from using this bot.",
            parse_mode='HTML')
        return

    # Register user
    get_or_create_user(str(user_id), username)

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
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM giveaways WHERE active = true")
        has_active_giveaway = cur.fetchone()[0] > 0
        cur.close()

    if has_active_giveaway:
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
    user_data = get_user_stats(user_id)

    if not user_data:
        stats_text = "📊 <b>Your Statistics</b>\n\n❌ No data found!"
    else:
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

    with get_db_connection() as conn:
        cur = conn.cursor()

        # Get active giveaway
        cur.execute("""
            SELECT g.id, g.winners, g.end_time
            FROM giveaways g
            WHERE g.active = true
            LIMIT 1
        """)
        result = cur.fetchone()

        if not result:
            await query.edit_message_text(
                text="❌ <b>No Active Giveaway</b>\n\n"
                "There's no active giveaway right now.\n\n"
                "Check back later!",
                parse_mode='HTML')
            return

        giveaway_id, winners, end_time = result

        # Check if user already participated
        cur.execute("""
            SELECT COUNT(*) FROM giveaway_participants 
            WHERE giveaway_id = %s AND user_id = %s
        """, (giveaway_id, user_id))

        if cur.fetchone()[0] > 0:
            await query.answer("⚠️ You're already in this giveaway!",
                               show_alert=True)
            return

        # Add participant
        cur.execute("""
            INSERT INTO giveaway_participants (giveaway_id, user_id)
            VALUES (%s, %s)
        """, (giveaway_id, user_id))

        cur.close()

    keyboard = [[
        InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"🎁 <b>Giveaway Entry Confirmed!</b>\n\n"
        f"✅ You've successfully joined the giveaway!\n\n"
        f"🏆 <b>Winners:</b> {winners}\n"
        f"⏰ <b>Ends:</b> {str(end_time)[:19]}\n\n"
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
    user = update.effective_user
    username_str = user.username if user.username else "N/A"
    full_name = user.full_name if user.full_name else "N/A"

    keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Check 10-minute cooldown
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT redeemed_at FROM key_redemptions 
            WHERE user_id = %s 
            ORDER BY redeemed_at DESC 
            LIMIT 1
        """, (user_id,))
        last_redemption = cur.fetchone()
        cur.close()
        
        if last_redemption:
            from datetime import datetime, timedelta
            last_time = last_redemption[0]
            time_diff = datetime.now() - last_time
            cooldown_seconds = 10 * 60  # 10 minutes
            
            if time_diff.total_seconds() < cooldown_seconds:
                remaining_seconds = int(cooldown_seconds - time_diff.total_seconds())
                remaining_minutes = remaining_seconds // 60
                remaining_secs = remaining_seconds % 60
                
                await update.message.reply_text(
                    f"⏳ <b>Cooldown Active</b>\n\n"
                    f"⚠️ You must wait <b>{remaining_minutes} minutes and {remaining_secs} seconds</b> before redeeming another key.\n\n"
                    f"🕐 Last redemption: {last_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"💡 This cooldown helps prevent abuse and ensures fair distribution!",
                    reply_markup=reply_markup,
                    parse_mode='HTML')
                return

    # Find the key in database
    key_found = get_key_by_code(key_code)

    if not key_found:
        await update.message.reply_text(
            "❌ <b>Invalid Key</b>\n\n"
            "The key you entered is not valid.\n\n"
            "Please check and try again!",
            reply_markup=reply_markup,
            parse_mode='HTML')
        return

    # Check if key is already used
    if key_found.get('status') == 'used' or key_found.get('remaining_uses', 0) <= 0:
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
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM key_redemptions 
            WHERE key_code = %s AND user_id = %s
        """, (key_code, user_id))
        if cur.fetchone()[0] > 0:
            cur.close()
            await update.message.reply_text(
                "⚠️ <b>Already Redeemed</b>\n\n"
                "You've already redeemed this key!\n\n"
                "Try a different key.",
                reply_markup=reply_markup,
                parse_mode='HTML')
            return
        cur.close()

    # Get credential from database
    platform = key_found.get('platform', '')
    credential = get_active_credential(platform)

    keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")]]
    reply_markup_error = InlineKeyboardMarkup(keyboard)

    if not credential:
        await update.message.reply_text(
            "❌ <b>No Accounts Available</b>\n\n"
            "All accounts for this platform are currently used.\n\n"
            "Please try again later!",
            reply_markup=reply_markup_error,
            parse_mode='HTML')
        return

    # Get full user details and platform info
    platform_name = key_found.get('platform', 'Unknown')
    account_text = key_found.get('account_text', 'Premium Account')

    # Claim credential and redeem key atomically
    claim_credential(platform_name, credential['id'], user_id, username_str, full_name)
    db_redeem_key(platform_name, key_found['id'], user_id, username_str, full_name)

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
        'Netflix': 'bot/assets/netflix.png',
        'Crunchyroll': 'bot/assets/crunchyroll.png',
        'WWE': 'bot/assets/wwe.png',
        'ParamountPlus': 'bot/assets/paramountplus.png',
        'Dazn': 'bot/assets/dazn.png',
        'MolotovTV': 'bot/assets/molotovtv.png',
        'DisneyPlus': 'bot/assets/disneyplus.png',
        'PSNFA': 'bot/assets/psnfa.png',
        'Xbox': 'bot/assets/xbox.png',
        'Spotify': 'bot/assets/spotify.png'
    }
    image_path = platform_images.get(platform_name)
    if image_path:
        image_path = os.path.join(project_root, image_path)

    # Send success message with credential
    try:
        if image_path and os.path.exists(image_path) and os.path.getsize(image_path) > 0:
            with open(image_path, 'rb') as photo:
                await update.message.reply_photo(photo=photo,
                                                 caption=success_text,
                                                 reply_markup=reply_markup,
                                                 parse_mode='HTML')
        else:
            await update.message.reply_text(success_text,
                                            reply_markup=reply_markup,
                                            parse_mode='HTML')
    except Exception as e:
        logger.error(f"Failed to send image, sending text instead: {e}")
        await update.message.reply_text(success_text,
                                        reply_markup=reply_markup,
                                        parse_mode='HTML')

    # Send admin notifications immediately after user receives credential
    try:
        await notify_admins_key_redeemed(
            context.bot,
            platform_name,
            user_id,
            username_str,
            full_name,
            key_code
        )
        logger.info(f"Admin notification sent for key redemption: {key_code} by user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send admin notifications: {e}")


async def participate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /participate command to join active giveaway"""
    user_id = str(update.effective_user.id)
    user = update.effective_user
    username = user.username

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

    keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="user_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    with get_db_connection() as conn:
        cur = conn.cursor()

        # Get active giveaway
        cur.execute("""
            SELECT g.id, g.winners, g.end_time
            FROM giveaways g
            WHERE g.active = true
            LIMIT 1
        """)
        result = cur.fetchone()

        if not result:
            await update.message.reply_text(
                "❌ <b>No Active Giveaway</b>\n\n"
                "There's no active giveaway right now.\n\n"
                "Check back later!",
                reply_markup=reply_markup,
                parse_mode='HTML')
            return

        giveaway_id, winners, end_time = result

        # Check if user already participated
        cur.execute("""
            SELECT COUNT(*) FROM giveaway_participants 
            WHERE giveaway_id = %s AND user_id = %s
        """, (giveaway_id, user_id))

        if cur.fetchone()[0] > 0:
            await update.message.reply_text(
                "⚠️ <b>Already Participating</b>\n\n"
                "You're already in this giveaway!\n\n"
                "Good luck! 🍀",
                reply_markup=reply_markup,
                parse_mode='HTML')
            return

        # Add participant
        cur.execute("""
            INSERT INTO giveaway_participants (giveaway_id, user_id)
            VALUES (%s, %s)
        """, (giveaway_id, user_id))

        cur.close()

    await update.message.reply_text(
        f"🎁 <b>Giveaway Entry Confirmed!</b>\n\n"
        f"✅ You've successfully joined the giveaway!\n\n"
        f"🏆 <b>Winners:</b> {winners}\n"
        f"⏰ <b>Ends:</b> {str(end_time)[:19]}\n\n"
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