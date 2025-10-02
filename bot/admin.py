import json
import os
import random
import string
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Admin user IDs - load from environment variable or use default
# Set ADMIN_IDS environment variable with comma-separated user IDs
# Example: ADMIN_IDS=123456789,987654321
_admin_ids_str = os.getenv('ADMIN_IDS', '')
if _admin_ids_str:
    ADMIN_IDS = [int(id.strip()) for id in _admin_ids_str.split(',') if id.strip()]
else:
    # If no admin IDs are set, any user who starts the bot will become an admin
    # This is for initial setup - the first user becomes admin
    ADMIN_IDS = []

# Database files
KEYS_FILE = 'data/keys.json'
USERS_FILE = 'data/users.json'
BANNED_FILE = 'data/banned.json'
GIVEAWAY_FILE = 'data/giveaway.json'

# Available platforms
PLATFORMS = ['Netflix', 'Crunchyroll', 'Spotify', 'WWE']


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
        return [] if filename != GIVEAWAY_FILE else {"active": False}


def save_json(filename, data):
    """Save JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS


def generate_key_code(platform):
    """Generate a unique key code"""
    prefix = platform.upper()
    parts = [
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        for _ in range(3)
    ]
    return f"{prefix}-{'-'.join(parts)}"


async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin main menu"""
    user_id = update.effective_user.id
    
    # Add user to admin list if not already there
    if user_id not in ADMIN_IDS:
        ADMIN_IDS.append(user_id)
    
    keyboard = [
        [InlineKeyboardButton("🔑 Generate Keys", callback_data="admin_generate_keys")],
        [InlineKeyboardButton("🎫 Generate Credentials", callback_data="admin_generate_credentials")],
        [InlineKeyboardButton("📊 Bot Stats", callback_data="admin_bot_stats")],
        [InlineKeyboardButton("📋 List All Keys", callback_data="admin_list_keys")],
        [InlineKeyboardButton("🗑️ Clear Expired Keys", callback_data="admin_clear_expired")],
        [InlineKeyboardButton("🎁 Start Giveaway", callback_data="admin_start_giveaway")],
        [InlineKeyboardButton("🛑 Stop Giveaway", callback_data="admin_stop_giveaway")],
        [InlineKeyboardButton("❌ Revoke Key", callback_data="admin_revoke_key")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban_user")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🎮 <b>Admin Panel - Premium Vault Bot</b> 🎮\n\n"
        "👋 Welcome back, Admin!\n\n"
        "🔧 <b>What would you like to do?</b>\n\n"
        "Select an option from the menu below:"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text=welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )


async def admin_generate_keys_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show platform selection for key generation"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for platform in PLATFORMS:
        emoji = {"Netflix": "🎬", "Crunchyroll": "🍜", "Spotify": "🎵", "WWE": "🤼"}.get(platform, "📦")
        keyboard.append([InlineKeyboardButton(f"{emoji} {platform}", callback_data=f"admin_gen_platform_{platform}")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="🎯 <b>Choose the Platform</b>\n\nSelect which platform you want to generate keys for:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def admin_generate_credentials_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show platform selection for credential generation"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for platform in PLATFORMS:
        emoji = {"Netflix": "🎬", "Crunchyroll": "🍜", "Spotify": "🎵", "WWE": "🤼"}.get(platform, "📦")
        keyboard.append([InlineKeyboardButton(f"{emoji} {platform}", callback_data=f"admin_cred_platform_{platform}")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="🎫 <b>Generate Credentials</b>\n\nSelect which platform you want to generate credentials for:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin callback queries"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await query.answer("❌ You are not authorized!", show_alert=True)
        return
    
    ensure_data_files()
    
    data = query.data
    
    if data == "admin_main":
        await admin_start(update, context)
    
    elif data == "admin_generate_keys":
        await admin_generate_keys_platform(update, context)
    
    elif data == "admin_generate_credentials":
        await admin_generate_credentials_platform(update, context)
    
    elif data.startswith("admin_cred_platform_"):
        platform = data.replace("admin_cred_platform_", "")
        context.user_data['cred_platform'] = platform
        context.user_data['cred_step'] = 'count'
        await query.answer()
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"🎫 <b>Platform: {platform}</b>\n\n"
                 f"How many credentials do you want to generate?\n\n"
                 f"📝 Please send a number (e.g., 5):",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif data.startswith("admin_gen_platform_"):
        platform = data.replace("admin_gen_platform_", "")
        context.user_data['gen_platform'] = platform
        context.user_data['gen_step'] = 'count'
        await query.answer()
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"🔢 <b>Platform: {platform}</b>\n\n"
                 f"How many keys do you want to generate?\n\n"
                 f"📝 Please send a number (e.g., 5):",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif data == "admin_bot_stats":
        await show_bot_stats(update, context)
    
    elif data == "admin_list_keys":
        await list_all_keys(update, context)
    
    elif data.startswith("admin_list_platform_"):
        platform = data.replace("admin_list_platform_", "")
        await list_keys_by_platform(update, context, platform)
    
    elif data == "admin_clear_expired":
        await clear_expired_keys(update, context)
    
    elif data == "admin_start_giveaway":
        await start_giveaway_platform(update, context)
    
    elif data.startswith("admin_giveaway_platform_"):
        platform = data.replace("admin_giveaway_platform_", "")
        context.user_data['giveaway_platform'] = platform
        await start_giveaway_duration(update, context)
    
    elif data.startswith("admin_giveaway_duration_"):
        duration = data.replace("admin_giveaway_duration_", "")
        context.user_data['giveaway_duration'] = duration
        context.user_data['giveaway_step'] = 'winners'
        await query.answer()
        await query.edit_message_text(
            text=f"🎁 <b>Giveaway Duration: {duration}</b>\n\n"
                 f"How many winners should there be?\n\n"
                 f"📝 Please send a number (e.g., 3):",
            parse_mode='HTML'
        )
    
    elif data == "admin_stop_giveaway":
        await stop_giveaway(update, context)
    
    elif data == "admin_revoke_key":
        await revoke_key_platform(update, context)
    
    elif data.startswith("admin_revoke_platform_"):
        platform = data.replace("admin_revoke_platform_", "")
        await revoke_key_options(update, context, platform)
    
    elif data.startswith("admin_revoke_option_"):
        parts = data.replace("admin_revoke_option_", "").split("_", 1)
        option = parts[0]
        platform = parts[1]
        await revoke_key_execute(update, context, platform, option)
    
    elif data.startswith("admin_revoke_confirm_"):
        action = data.replace("admin_revoke_confirm_", "")
        if action == "yes":
            await execute_revoke(update, context)
        else:
            await query.answer("❌ Revoke cancelled")
            await admin_start(update, context)
    
    elif data == "admin_broadcast":
        context.user_data['broadcast_step'] = 'message'
        await query.answer()
        await query.edit_message_text(
            text="📢 <b>Broadcast Message</b>\n\n"
                 "Send the message you want to broadcast to all users:\n\n"
                 "💡 You can use HTML formatting.",
            parse_mode='HTML'
        )
    
    elif data == "admin_ban_user":
        context.user_data['ban_step'] = 'user_id'
        await query.answer()
        await query.edit_message_text(
            text="🚫 <b>Ban User</b>\n\n"
                 "Send the user ID or username to ban:\n\n"
                 "📝 Example: @username or 123456789",
            parse_mode='HTML'
        )


async def show_bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics"""
    query = update.callback_query
    await query.answer()
    
    keys = load_json(KEYS_FILE)
    users = load_json(USERS_FILE)
    
    total_keys = len(keys)
    active_keys = len([k for k in keys if k.get('status') == 'active'])
    used_keys = len([k for k in keys if k.get('status') == 'used'])
    expired_keys = len([k for k in keys if k.get('status') == 'expired'])
    
    total_users = len(users)
    
    stats_text = (
        "📊 <b>Bot Statistics</b>\n\n"
        f"👥 <b>Total Users:</b> {total_users}\n\n"
        f"🔑 <b>Total Keys:</b> {total_keys}\n"
        f"✅ <b>Active Keys:</b> {active_keys}\n"
        f"🎯 <b>Used Keys:</b> {used_keys}\n"
        f"⏰ <b>Expired Keys:</b> {expired_keys}\n\n"
    )
    
    # Platform breakdown
    platform_stats = {}
    for key in keys:
        platform = key.get('platform', 'Unknown')
        if platform not in platform_stats:
            platform_stats[platform] = {'total': 0, 'active': 0, 'used': 0}
        platform_stats[platform]['total'] += 1
        if key.get('status') == 'active':
            platform_stats[platform]['active'] += 1
        elif key.get('status') == 'used':
            platform_stats[platform]['used'] += 1
    
    if platform_stats:
        stats_text += "📱 <b>Platform Breakdown:</b>\n"
        for platform, stats in platform_stats.items():
            emoji = {"Netflix": "🎬", "Crunchyroll": "🍜", "Spotify": "🎵", "WWE": "🤼"}.get(platform, "📦")
            stats_text += f"{emoji} <b>{platform}:</b> {stats['total']} total, {stats['active']} active, {stats['used']} used\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=stats_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def list_all_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all keys by platform"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for platform in PLATFORMS:
        emoji = {"Netflix": "🎬", "Crunchyroll": "🍜", "Spotify": "🎵", "WWE": "🤼"}.get(platform, "📦")
        keyboard.append([InlineKeyboardButton(f"{emoji} {platform} Keys", callback_data=f"admin_list_platform_{platform}")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="📋 <b>List Keys by Platform</b>\n\nSelect a platform to view all keys:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def list_keys_by_platform(update: Update, context: ContextTypes.DEFAULT_TYPE, platform):
    """List keys for a specific platform with detailed stats"""
    query = update.callback_query
    await query.answer()
    
    keys = load_json(KEYS_FILE)
    platform_keys = [k for k in keys if k.get('platform') == platform]
    
    if not platform_keys:
        text = f"📋 <b>{platform} Keys</b>\n\nNo keys found for this platform."
    else:
        # Calculate statistics
        total_keys = len(platform_keys)
        active_keys = len([k for k in platform_keys if k.get('status') == 'active'])
        used_keys = len([k for k in platform_keys if k.get('status') == 'used'])
        expired_keys = len([k for k in platform_keys if k.get('status') == 'expired'])
        
        # Count total unique users who redeemed
        all_users = set()
        for key in platform_keys:
            all_users.update(key.get('used_by', []))
        total_users = len(all_users)
        
        text = (
            f"📋 <b>{platform} Keys Statistics</b>\n\n"
            f"📊 <b>Total Keys:</b> {total_keys}\n"
            f"✅ <b>Active:</b> {active_keys}\n"
            f"🎯 <b>Used:</b> {used_keys}\n"
            f"⏰ <b>Expired:</b> {expired_keys}\n"
            f"👥 <b>Total Users:</b> {total_users}\n\n"
            f"🔑 <b>Key List:</b>\n"
        )
        
        for key in platform_keys[:15]:  # Show first 15 keys
            status_emoji = {"active": "✅", "used": "🎯", "expired": "⏰"}.get(key.get('status', 'active'), "❓")
            remaining = key.get('remaining_uses', 0)
            total_uses = key.get('uses', 1)
            created_at = key.get('created_at', 'Unknown')[:10]
            redeemed_count = len(key.get('used_by', []))
            
            text += f"\n{status_emoji} <code>{key['key']}</code>\n"
            text += f"   📅 Created: {created_at}\n"
            text += f"   🎯 Uses: {redeemed_count}/{total_uses} (Remaining: {remaining})\n"
            
            if key.get('redeemed_at'):
                text += f"   ⏰ Last Redeemed: {key.get('redeemed_at')[:19]}\n"
        
        if len(platform_keys) > 15:
            text += f"\n... and {len(platform_keys) - 15} more keys"
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back to List", callback_data="admin_list_keys")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="admin_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def clear_expired_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all expired keys"""
    query = update.callback_query
    await query.answer()
    
    keys = load_json(KEYS_FILE)
    initial_count = len(keys)
    
    # Remove expired keys
    keys = [k for k in keys if k.get('status') != 'expired']
    removed_count = initial_count - len(keys)
    
    save_json(KEYS_FILE, keys)
    
    text = (
        "🗑️ <b>Clear Expired Keys</b>\n\n"
        f"✅ Successfully removed {removed_count} expired keys!\n\n"
        f"📊 Remaining keys: {len(keys)}"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def start_giveaway_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show platform selection for giveaway"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for platform in PLATFORMS:
        emoji = {"Netflix": "🎬", "Crunchyroll": "🍜", "Spotify": "🎵", "WWE": "🤼"}.get(platform, "📦")
        keyboard.append([InlineKeyboardButton(f"{emoji} {platform}", callback_data=f"admin_giveaway_platform_{platform}")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="🎁 <b>Start Giveaway</b>\n\nSelect the platform for this giveaway:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def start_giveaway_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show giveaway duration options"""
    query = update.callback_query
    await query.answer()
    
    platform = context.user_data.get('giveaway_platform', 'Unknown')
    
    keyboard = [
        [InlineKeyboardButton("⏱️ 30 Minutes", callback_data="admin_giveaway_duration_30m")],
        [InlineKeyboardButton("⏱️ 1 Hour", callback_data="admin_giveaway_duration_1h")],
        [InlineKeyboardButton("⏱️ 2 Hours", callback_data="admin_giveaway_duration_2h")],
        [InlineKeyboardButton("⏱️ 3 Hours", callback_data="admin_giveaway_duration_3h")],
        [InlineKeyboardButton("⏱️ 6 Hours", callback_data="admin_giveaway_duration_6h")],
        [InlineKeyboardButton("⏱️ 12 Hours", callback_data="admin_giveaway_duration_12h")],
        [InlineKeyboardButton("⏱️ 24 Hours", callback_data="admin_giveaway_duration_24h")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"🎁 <b>Start Giveaway - {platform}</b>\n\nSelect the giveaway duration:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def stop_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop active giveaway"""
    query = update.callback_query
    await query.answer()
    
    giveaway = load_json(GIVEAWAY_FILE)
    
    if not giveaway.get('active'):
        text = "🛑 <b>Stop Giveaway</b>\n\n❌ No active giveaway found!"
    else:
        giveaway['active'] = False
        save_json(GIVEAWAY_FILE, giveaway)
        text = "🛑 <b>Giveaway Stopped</b>\n\n✅ The giveaway has been stopped successfully!"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def revoke_key_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show platform selection for key revocation"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for platform in PLATFORMS:
        emoji = {"Netflix": "🎬", "Crunchyroll": "🍜", "Spotify": "🎵", "WWE": "🤼"}.get(platform, "📦")
        keyboard.append([InlineKeyboardButton(f"{emoji} {platform}", callback_data=f"admin_revoke_platform_{platform}")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="❌ <b>Revoke Keys</b>\n\nSelect the platform:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def revoke_key_options(update: Update, context: ContextTypes.DEFAULT_TYPE, platform):
    """Show revoke options"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Revoke Last Generated", callback_data=f"admin_revoke_option_last_{platform}")],
        [InlineKeyboardButton("🗑️ Revoke All Keys", callback_data=f"admin_revoke_option_all_{platform}")],
        [InlineKeyboardButton("🔙 Back to Revoke", callback_data="admin_revoke_key")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="admin_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    context.user_data['revoke_platform'] = platform
    
    await query.edit_message_text(
        text=f"❌ <b>Revoke {platform} Keys</b>\n\nSelect an option:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def revoke_key_execute(update: Update, context: ContextTypes.DEFAULT_TYPE, platform, option):
    """Execute key revocation"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['revoke_platform'] = platform
    context.user_data['revoke_option'] = option
    
    keys = load_json(KEYS_FILE)
    platform_keys = [k for k in keys if k.get('platform') == platform]
    
    if option == "last":
        count = 1
        text = f"⚠️ <b>Confirm Revocation</b>\n\nAre you sure you want to revoke the last generated {platform} key?\n\n📊 This will revoke {count} key(s)."
    elif option == "all":
        count = len(platform_keys)
        text = f"⚠️ <b>Confirm Revocation</b>\n\nAre you sure you want to revoke ALL {platform} keys?\n\n📊 This will revoke {count} key(s)."
    
    keyboard = [
        [InlineKeyboardButton("✅ Yes, Revoke", callback_data="admin_revoke_confirm_yes")],
        [InlineKeyboardButton("❌ Cancel", callback_data="admin_revoke_confirm_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def execute_revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the actual revocation"""
    query = update.callback_query
    await query.answer()
    
    platform = context.user_data.get('revoke_platform')
    option = context.user_data.get('revoke_option')
    
    keys = load_json(KEYS_FILE)
    
    if option == "last":
        # Find and remove the last key
        platform_keys = [k for k in keys if k.get('platform') == platform]
        if platform_keys:
            last_key = platform_keys[-1]
            keys.remove(last_key)
            count = 1
        else:
            count = 0
    elif option == "all":
        initial_count = len(keys)
        keys = [k for k in keys if k.get('platform') != platform]
        count = initial_count - len(keys)
    
    save_json(KEYS_FILE, keys)
    
    text = (
        "✅ <b>Keys Revoked</b>\n\n"
        f"Successfully revoked {count} {platform} key(s)!"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin text messages"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    ensure_data_files()
    
    # Handle key generation steps
    if context.user_data.get('gen_step') == 'count':
        try:
            count = int(update.message.text)
            context.user_data['gen_count'] = count
            context.user_data['gen_step'] = 'uses'
            
            keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="admin_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"🎯 <b>Count: {count}</b>\n\n"
                f"How many times can each key be used?\n\n"
                f"📝 Please send a number (e.g., 1):",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except ValueError:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ Please send a valid number!",
                reply_markup=reply_markup
            )
    
    elif context.user_data.get('gen_step') == 'uses':
        try:
            uses = int(update.message.text)
            context.user_data['gen_uses'] = uses
            context.user_data['gen_step'] = 'account_text'
            
            keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="admin_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ <b>Uses: {uses}</b>\n\n"
                f"What account type is this?\n\n"
                f"📝 Please send the account text (e.g., Premium Account):",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except ValueError:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ Please send a valid number!",
                reply_markup=reply_markup
            )
    
    elif context.user_data.get('gen_step') == 'account_text':
        account_text = update.message.text
        
        # Generate keys
        platform = context.user_data.get('gen_platform')
        count = context.user_data.get('gen_count')
        uses = context.user_data.get('gen_uses')
        
        # Load both main keys and platform-specific keys
        keys_data = load_json(KEYS_FILE)
        
        # Create keys folder if it doesn't exist
        os.makedirs('keys', exist_ok=True)
        platform_keys_file = f'keys/{platform.lower()}.json'
        platform_keys_data = load_json(platform_keys_file) if os.path.exists(platform_keys_file) else []
        
        generated_keys = []
        
        for _ in range(count):
            key_code = generate_key_code(platform)
            key_data = {
                "key": key_code,
                "platform": platform,
                "uses": uses,
                "remaining_uses": uses,
                "account_text": account_text,
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "redeemed_at": None,
                "redeemed_by": [],
                "used_by": []
            }
            keys_data.append(key_data)
            platform_keys_data.append(key_data)
            generated_keys.append(key_code)
        
        save_json(KEYS_FILE, keys_data)
        save_json(platform_keys_file, platform_keys_data)
        
        # Clear user data
        context.user_data.pop('gen_step', None)
        context.user_data.pop('gen_platform', None)
        context.user_data.pop('gen_count', None)
        context.user_data.pop('gen_uses', None)
        
        keys_text = "\n".join([f"<code>{k}</code>" for k in generated_keys])
        
        result_text = (
            "✅ <b>Keys Generated Successfully!</b>\n\n"
            f"📦 <b>Platform:</b> {platform}\n"
            f"🔢 <b>Generated Keys:</b> {count}\n"
            f"🎯 <b>Uses per Key:</b> {uses}\n"
            f"📝 <b>Account Type:</b> {account_text}\n\n"
            f"🔑 <b>Generated Keys:</b>\n{keys_text}\n\n"
            f"💡 <i>Tap on any key to copy it!</i>"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text=result_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    # Handle giveaway winner count
    elif context.user_data.get('giveaway_step') == 'winners':
        try:
            winners = int(update.message.text)
            duration = context.user_data.get('giveaway_duration')
            platform = context.user_data.get('giveaway_platform', 'Unknown')
            
            # Parse duration
            duration_map = {
                '30m': 30,
                '1h': 60,
                '2h': 120,
                '3h': 180,
                '6h': 360,
                '12h': 720,
                '24h': 1440
            }
            
            duration_minutes = duration_map.get(duration, 60)
            end_time = datetime.now() + timedelta(minutes=duration_minutes)
            
            giveaway = {
                "active": True,
                "platform": platform,
                "duration": duration,
                "winners": winners,
                "end_time": end_time.isoformat(),
                "participants": []
            }
            
            save_json(GIVEAWAY_FILE, giveaway)
            
            context.user_data.pop('giveaway_step', None)
            context.user_data.pop('giveaway_duration', None)
            context.user_data.pop('giveaway_platform', None)
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"🎁 <b>Giveaway Started!</b>\n\n"
                f"🎮 <b>Platform:</b> {platform}\n"
                f"⏱️ <b>Duration:</b> {duration}\n"
                f"🏆 <b>Winners:</b> {winners}\n"
                f"⏰ <b>Ends at:</b> {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"✅ Users can now participate!",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except ValueError:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ Please send a valid number!",
                reply_markup=reply_markup
            )
    
    # Handle credential generation
    elif context.user_data.get('cred_step') == 'count':
        try:
            count = int(update.message.text)
            platform = context.user_data.get('cred_platform', '').lower()
            
            credential_file = f'credentials/{platform}.json'
            credentials = load_json(credential_file)
            
            # Get active credentials
            active_creds = [c for c in credentials if c.get('status') == 'active']
            
            if count > len(active_creds):
                keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"❌ <b>Not Enough Credentials</b>\n\n"
                    f"You requested {count} credentials but only {len(active_creds)} are available.\n\n"
                    f"Please generate more credentials in the {platform}.json file first!",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                context.user_data.pop('cred_step', None)
                context.user_data.pop('cred_platform', None)
                return
            
            # Get the requested credentials
            creds_to_send = active_creds[:count]
            creds_text = ""
            
            for i, cred in enumerate(creds_to_send, 1):
                creds_text += f"\n<b>Account {i}:</b>\n"
                creds_text += f"📧 Email: <code>{cred['email']}</code>\n"
                creds_text += f"🔑 Password: <code>{cred['password']}</code>\n"
            
            context.user_data.pop('cred_step', None)
            context.user_data.pop('cred_platform', None)
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"🎫 <b>{platform.title()} Credentials</b>\n\n"
                f"📊 Generated {count} credential(s):\n"
                f"{creds_text}\n\n"
                f"💡 <i>Tap to copy!</i>",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except ValueError:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ Please send a valid number!",
                reply_markup=reply_markup
            )
    
    # Handle broadcast
    elif context.user_data.get('broadcast_step') == 'message':
        message = update.message.text
        users = load_json(USERS_FILE)
        
        success_count = 0
        fail_count = 0
        
        for user_id_str in users.keys():
            try:
                await context.bot.send_message(
                    chat_id=int(user_id_str),
                    text=f"📢 <b>Broadcast Message</b>\n\n{message}",
                    parse_mode='HTML'
                )
                success_count += 1
            except Exception as e:
                fail_count += 1
                logger.error(f"Failed to send broadcast to {user_id_str}: {e}")
        
        context.user_data.pop('broadcast_step', None)
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📢 <b>Broadcast Complete</b>\n\n"
            f"✅ Successfully sent to {success_count} users\n"
            f"❌ Failed to send to {fail_count} users",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    # Handle ban user
    elif context.user_data.get('ban_step') == 'user_id':
        user_input = update.message.text.strip()
        
        banned = load_json(BANNED_FILE)
        
        # Try to extract user ID
        if user_input.startswith('@'):
            user_identifier = user_input
        else:
            try:
                user_identifier = int(user_input)
            except ValueError:
                keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "❌ Invalid user ID or username!",
                    reply_markup=reply_markup
                )
                return
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if user_identifier not in banned:
            banned.append(user_identifier)
            save_json(BANNED_FILE, banned)
            
            context.user_data.pop('ban_step', None)
            
            await update.message.reply_text(
                f"🚫 <b>User Banned</b>\n\n"
                f"✅ User {user_input} has been banned from using the bot!",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ User is already banned!",
                reply_markup=reply_markup
            )
