#!/usr/bin/env python
import os
import random
import string
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_helpers import (
    get_platforms, add_key, get_keys_by_platform, get_key_by_code,
    delete_keys_by_platform, is_user_banned as db_is_user_banned,
    ban_user as db_ban_user, get_db_connection, get_all_admin_telegram_ids
)

logger = logging.getLogger(__name__)

# Admin user IDs - Static admin + environment variable
# Static admin (always has access)
STATIC_ADMIN_ID = 6562270244  # @BEASTSEC

# Additional admins from environment variable
_admin_ids_str = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [STATIC_ADMIN_ID]  # Start with static admin

if _admin_ids_str:
    additional_admins = [
        int(id.strip()) for id in _admin_ids_str.split(',') if id.strip()
    ]
    ADMIN_IDS.extend([id for id in additional_admins if id not in ADMIN_IDS])

# Available platforms - This is now fetched from the database in db_helpers

def get_admin_ids_from_db():
    """Get admin IDs from database"""
    return get_all_admin_telegram_ids()

def is_admin(user_id):
    """Check if user is admin"""
    # Check static and environment variable admins
    if user_id in ADMIN_IDS:
        return True

    # Check admin credentials file for telegram IDs
    telegram_admin_ids = get_admin_ids_from_db()
    if user_id in telegram_admin_ids:
        return True

    return False

def ensure_data_files():
    """Compatibility function - no longer needed with PostgreSQL"""
    pass

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

    keyboard = [
        [
            InlineKeyboardButton("🔑 Generate Keys",
                                 callback_data="admin_generate_keys")
        ],
        [
            InlineKeyboardButton("🎫 Generate Credentials",
                                 callback_data="admin_generate_credentials")
        ],
        [InlineKeyboardButton("📊 Bot Stats", callback_data="admin_bot_stats")],
        [
            InlineKeyboardButton("📋 List All Keys",
                                 callback_data="admin_list_keys")
        ],
        [
            InlineKeyboardButton("🗑️ Clear Expired Keys",
                                 callback_data="admin_clear_expired")
        ],
        [
            InlineKeyboardButton("🎁 Start Giveaway",
                                 callback_data="admin_start_giveaway")
        ],
        [
            InlineKeyboardButton("🛑 Stop Giveaway",
                                 callback_data="admin_stop_giveaway")
        ],
        [
            InlineKeyboardButton("❌ Revoke Key",
                                 callback_data="admin_revoke_key")
        ],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban_user")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = ("🎮 <b>Admin Panel - Premium Vault Bot</b> 🎮\n\n"
                    "👋 Welcome back, Admin!\n\n"
                    "🔧 <b>What would you like to do?</b>\n\n"
                    "Select an option from the menu below:")

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=welcome_text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(text=welcome_text,
                                        reply_markup=reply_markup,
                                        parse_mode='HTML')


async def admin_generate_keys_platform(update: Update,
                                       context: ContextTypes.DEFAULT_TYPE):
    """Show platform selection for key generation"""
    query = update.callback_query
    await query.answer()

    platforms = get_platforms()
    keyboard = []
    for platform in platforms:
        keyboard.append([
            InlineKeyboardButton(
                f"{platform['emoji']} {platform['name']}",
                callback_data=f"admin_gen_platform_{platform['name'].lower()}")
        ])
    keyboard.append(
        [InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=
        "🎯 <b>Choose the Platform</b>\n\nSelect which platform you want to generate keys for:",
        reply_markup=reply_markup,
        parse_mode='HTML')


async def admin_generate_credentials_platform(
        update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show platform selection for credential generation"""
    query = update.callback_query
    await query.answer()

    platforms = get_platforms()
    keyboard = []
    for platform in platforms:
        keyboard.append([
            InlineKeyboardButton(
                f"{platform['emoji']} {platform['name']}",
                callback_data=f"admin_cred_platform_{platform['name'].lower()}")
        ])
    keyboard.append(
        [InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=
        "🎫 <b>Generate Credentials</b>\n\nSelect which platform you want to generate credentials for:",
        reply_markup=reply_markup,
        parse_mode='HTML')


async def handle_admin_callback(update: Update,
                                context: ContextTypes.DEFAULT_TYPE):
    """Handle admin callback queries"""
    query = update.callback_query
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await query.answer("❌ You are not authorized!", show_alert=True)
        return

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

        keyboard = [[
            InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=f"🎫 <b>Platform: {platform.capitalize()}</b>\n\n"
            f"How many credentials do you want to generate?\n\n"
            f"📝 Please send a number (e.g., 5):",
            reply_markup=reply_markup,
            parse_mode='HTML')

    elif data.startswith("admin_gen_platform_"):
        platform = data.replace("admin_gen_platform_", "")
        context.user_data['gen_platform'] = platform
        context.user_data['gen_step'] = 'count'
        await query.answer()

        keyboard = [[
            InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=f"🔢 <b>Platform: {platform.capitalize()}</b>\n\n"
            f"How many keys do you want to generate?\n\n"
            f"📝 Please send a number (e.g., 5):",
            reply_markup=reply_markup,
            parse_mode='HTML')

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
            parse_mode='HTML')

    elif data == "admin_stop_giveaway":
        await stop_giveaway(update, context)

    elif data == "admin_revoke_key":
        context.user_data['revoke_step'] = 'platform'
        await query.answer()
        platforms = get_platforms()
        keyboard = []
        for platform in platforms:
            keyboard.append([
                InlineKeyboardButton(
                    f"{platform['emoji']} {platform['name']}",
                    callback_data=f"admin_revoke_platform_{platform['name'].lower()}")
            ])
        keyboard.append(
            [InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="❌ <b>Revoke Key</b>\n\nSelect the platform:",
            reply_markup=reply_markup,
            parse_mode='HTML')

    elif data.startswith("admin_revoke_platform_"):
        platform = data.replace("admin_revoke_platform_", "")
        context.user_data['revoke_platform'] = platform
        context.user_data['revoke_step'] = 'option'
        await query.answer()

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 Last Generated Key",
                    callback_data=f"admin_revoke_option_last_{platform}")
            ],
            [
                InlineKeyboardButton("🗑️ All Keys",
                                     callback_data=f"admin_revoke_option_all_{platform}")
            ],
            [
                InlineKeyboardButton("✅ Claimed Keys",
                                     callback_data=f"admin_revoke_option_claimed_{platform}")
            ],
            [
                InlineKeyboardButton("🔙 Back to Revoke Platform",
                                     callback_data="admin_revoke_key")
            ],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="admin_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=f"❌ <b>Revoke {platform.capitalize()} Keys</b>\n\nSelect an option:",
            reply_markup=reply_markup,
            parse_mode='HTML')

    elif data.startswith("admin_revoke_option_"):
        parts = data.replace("admin_revoke_option_", "").split("_", 1)
        option = parts[0]
        platform = parts[1]
        context.user_data['revoke_option'] = option
        context.user_data['revoke_platform'] = platform
        context.user_data['revoke_step'] = 'confirm'
        await query.answer()

        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM platforms WHERE name ILIKE %s", (platform,))
            platform_result = cur.fetchone()
            if not platform_result:
                await query.edit_message_text("❌ Platform not found!", parse_mode='HTML')
                return
            platform_id = platform_result[0]
            
            count = 0
            if option == "last":
                cur.execute("""
                    SELECT COUNT(*) FROM keys WHERE platform_id = %s
                    ORDER BY created_at DESC LIMIT 1
                """, (platform_id,))
                count = cur.fetchone()[0]
            elif option == "all":
                cur.execute("SELECT COUNT(*) FROM keys WHERE platform_id = %s", (platform_id,))
                count = cur.fetchone()[0]
            elif option == "claimed":
                cur.execute("SELECT COUNT(*) FROM keys WHERE platform_id = %s AND status = 'used'", (platform_id,))
                count = cur.fetchone()[0]
            cur.close()

        text = f"⚠️ <b>Confirm Revocation</b>\n\nAre you sure you want to revoke {count} key(s) for {platform.capitalize()} ({option})?\n\n📊 This action cannot be undone."
        
        keyboard = [[
            InlineKeyboardButton("✅ Yes, Revoke",
                                 callback_data="admin_revoke_confirm_yes")
        ],
                    [
                        InlineKeyboardButton(
                            "❌ Cancel", callback_data="admin_revoke_confirm_no")
                    ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text=text,
                                      reply_markup=reply_markup,
                                      parse_mode='HTML')

    elif data == "admin_revoke_confirm_yes":
        await execute_revoke(update, context)
    elif data == "admin_revoke_confirm_no":
        await query.answer("❌ Revoke cancelled")
        await admin_start(update, context)

    elif data == "admin_broadcast":
        context.user_data['broadcast_step'] = 'message'
        await query.answer()
        await query.edit_message_text(
            text="📢 <b>Broadcast Message</b>\n\n"
            "Send the message you want to broadcast to all users:\n\n"
            "💡 You can use HTML formatting.",
            parse_mode='HTML')

    elif data == "admin_ban_user":
        context.user_data['ban_step'] = 'user_id'
        await query.answer()
        await query.edit_message_text(
            text="🚫 <b>Ban User</b>\n\n"
            "Send the user ID or username to ban:\n\n"
            "📝 Example: @username or 123456789",
            parse_mode='HTML')


async def show_bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics"""
    query = update.callback_query
    await query.answer()

    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Get key statistics
        cur.execute("SELECT COUNT(*) FROM keys")
        total_keys = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM keys WHERE status = 'active'")
        active_keys = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM keys WHERE status = 'used'")
        used_keys = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM keys WHERE status = 'expired'")
        expired_keys = cur.fetchone()[0]
        
        # Get total users
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        
        stats_text = ("📊 <b>Bot Statistics</b>\n\n"
                      f"👥 <b>Total Users:</b> {total_users}\n\n"
                      f"🔑 <b>Total Keys:</b> {total_keys}\n"
                      f"✅ <b>Active Keys:</b> {active_keys}\n"
                      f"🎯 <b>Used Keys:</b> {used_keys}\n"
                      f"⏰ <b>Expired Keys:</b> {expired_keys}\n\n")
        
        # Platform breakdown
        cur.execute("""
            SELECT p.name, k.status, COUNT(*) 
            FROM keys k 
            JOIN platforms p ON k.platform_id = p.id 
            GROUP BY p.name, k.status
        """)
        
        platform_stats = {}
        for row in cur.fetchall():
            platform, status, count = row
            if platform not in platform_stats:
                platform_stats[platform] = {'total': 0, 'active': 0, 'used': 0, 'expired': 0}
            platform_stats[platform]['total'] += count
            if status == 'active':
                platform_stats[platform]['active'] = count
            elif status == 'used':
                platform_stats[platform]['used'] = count
            elif status == 'expired':
                platform_stats[platform]['expired'] = count
        
        if platform_stats:
            stats_text += "📱 <b>Platform Breakdown:</b>\n"
            for platform, stats in platform_stats.items():
                emoji = {
                    "Netflix": "🎬",
                    "Crunchyroll": "🍜",
                    "WWE": "🤼",
                    "ParamountPlus": "⭐",
                    "Dazn": "🥊",
                    "MolotovTV": "📺",
                    "DisneyPlus": "🏰",
                    "PSNFA": "🎮",
                    "Xbox": "🎯"
                }.get(platform, "📦")
                stats_text += f"{emoji} <b>{platform}:</b> {stats['total']} total, {stats['active']} active, {stats['used']} used, {stats['expired']} expired\n"
        
        cur.close()

    keyboard = [[
        InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=stats_text,
                                  reply_markup=reply_markup,
                                  parse_mode='HTML')


async def list_all_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all keys by platform"""
    query = update.callback_query
    await query.answer()

    platforms = get_platforms()
    keyboard = []
    for platform in platforms:
        keyboard.append([
            InlineKeyboardButton(
                f"{platform['emoji']} {platform['name']} Keys",
                callback_data=f"admin_list_platform_{platform['name'].lower()}")
        ])
    keyboard.append(
        [InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=
        "📋 <b>List Keys by Platform</b>\n\nSelect a platform to view all keys:",
        reply_markup=reply_markup,
        parse_mode='HTML')


async def list_keys_by_platform(update: Update,
                                context: ContextTypes.DEFAULT_TYPE, platform):
    """List keys for a specific platform with detailed stats"""
    query = update.callback_query
    await query.answer()

    platform_name = get_platform_display_name(platform)
    platform_keys = get_keys_by_platform(platform_name)

    if not platform_keys:
        text = f"📋 <b>{platform_name} Keys</b>\n\nNo keys found for this platform."
    else:
        # Calculate statistics
        total_keys = len(platform_keys)
        active_keys = len([k for k in platform_keys if k.get('status') == 'active'])
        used_keys = len([k for k in platform_keys if k.get('status') == 'used'])
        expired_keys = len([k for k in platform_keys if k.get('status') == 'expired'])

        # Count total unique users who redeemed
        all_users = set()
        for key in platform_keys:
            if key.get('used_by'):
                all_users.update(key.get('used_by', []))
        total_users = len(all_users)

        text = (f"📋 <b>{platform_name} Keys Statistics</b>\n\n"
                f"📊 <b>Total Keys:</b> {total_keys}\n"
                f"✅ <b>Active:</b> {active_keys}\n"
                f"🎯 <b>Used:</b> {used_keys}\n"
                f"⏰ <b>Expired:</b> {expired_keys}\n"
                f"👥 <b>Total Users Redeemed:</b> {total_users}\n\n"
                f"🔑 <b>Key List:</b>\n")

        for key_data in platform_keys[:15]:  # Show first 15 keys
            key_code = key_data['key']
            status = key_data.get('status', 'active')
            status_emoji = {
                "active": "✅",
                "used": "🎯",
                "expired": "⏰"
            }.get(status, "❓")
            remaining = key_data.get('remaining_uses', 0)
            total_uses = key_data.get('uses', 1)
            created_at = key_data.get('created_at', 'Unknown')[:10]
            redeemed_count = len(key_data.get('used_by', []))

            text += f"\n{status_emoji} <code>{key_code}</code>\n"
            text += f"   📅 Created: {created_at}\n"
            text += f"   🎯 Uses: {redeemed_count}/{total_uses} (Remaining: {remaining})\n"

            if key_data.get('redeemed_at'):
                text += f"   ⏰ Last Redeemed: {key_data.get('redeemed_at')[:19]}\n"
            if key_data.get('used_by'):
                last_user = key_data['used_by'][-1]
                text += f"   👤 Last User: {last_user}\n"


        if len(platform_keys) > 15:
            text += f"\n... and {len(platform_keys) - 15} more keys"

    keyboard = [[
        InlineKeyboardButton("🔙 Back to List", callback_data="admin_list_keys")
    ], [InlineKeyboardButton("🏠 Main Menu", callback_data="admin_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=text,
                                  reply_markup=reply_markup,
                                  parse_mode='HTML')


async def clear_expired_keys(update: Update,
                             context: ContextTypes.DEFAULT_TYPE):
    """Clear all expired keys"""
    query = update.callback_query
    await query.answer()

    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Count expired keys
        cur.execute("SELECT COUNT(*) FROM keys WHERE status = 'expired'")
        removed_count = cur.fetchone()[0]
        
        # Delete expired keys
        cur.execute("DELETE FROM keys WHERE status = 'expired'")
        
        # Count remaining keys
        cur.execute("SELECT COUNT(*) FROM keys")
        remaining_count = cur.fetchone()[0]
        
        cur.close()

    text = ("🗑️ <b>Clear Expired Keys</b>\n\n"
            f"✅ Successfully removed {removed_count} expired keys!\n\n"
            f"📊 Remaining keys: {remaining_count}")

    keyboard = [[
        InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=text,
                                  reply_markup=reply_markup,
                                  parse_mode='HTML')


async def start_giveaway_platform(update: Update,
                                  context: ContextTypes.DEFAULT_TYPE):
    """Show platform selection for giveaway"""
    query = update.callback_query
    await query.answer()

    platforms = get_platforms()
    keyboard = []
    for platform in platforms:
        keyboard.append([
            InlineKeyboardButton(
                f"{platform['emoji']} {platform['name']}",
                callback_data=f"admin_giveaway_platform_{platform['name'].lower()}")
        ])
    keyboard.append(
        [InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=
        "🎁 <b>Start Giveaway</b>\n\nSelect the platform for this giveaway:",
        reply_markup=reply_markup,
        parse_mode='HTML')


async def start_giveaway_duration(update: Update,
                                  context: ContextTypes.DEFAULT_TYPE):
    """Show giveaway duration options"""
    query = update.callback_query
    await query.answer()

    platform = context.user_data.get('giveaway_platform', 'Unknown')

    keyboard = [
        [
            InlineKeyboardButton("⏱️ 1 Minute",
                                 callback_data="admin_giveaway_duration_1m")
        ],
        [
            InlineKeyboardButton("⏱️ 5 Minutes",
                                 callback_data="admin_giveaway_duration_5m")
        ],
        [
            InlineKeyboardButton("⏱️ 30 Minutes",
                                 callback_data="admin_giveaway_duration_30m")
        ],
        [
            InlineKeyboardButton("⏱️ 1 Hour",
                                 callback_data="admin_giveaway_duration_1h")
        ],
        [
            InlineKeyboardButton("⏱️ 3 Hours",
                                 callback_data="admin_giveaway_duration_3h")
        ],
        [
            InlineKeyboardButton("⏱️ 6 Hours",
                                 callback_data="admin_giveaway_duration_6h")
        ],
        [
            InlineKeyboardButton("⏱️ 12 Hours",
                                 callback_data="admin_giveaway_duration_12h")
        ],
        [
            InlineKeyboardButton("⏱️ 24 Hours",
                                 callback_data="admin_giveaway_duration_24h")
        ],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=
        f"🎁 <b>Start Giveaway - {platform.capitalize()}</b>\n\nSelect the giveaway duration:",
        reply_markup=reply_markup,
        parse_mode='HTML')


async def stop_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop active giveaway and notify all participants"""
    query = update.callback_query
    await query.answer()

    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Get active giveaway
        cur.execute("""
            SELECT g.id, p.name
            FROM giveaways g
            JOIN platforms p ON g.platform_id = p.id
            WHERE g.active = true
            LIMIT 1
        """)
        result = cur.fetchone()
        
        if not result:
            text = "🛑 <b>Stop Giveaway</b>\n\n❌ No active giveaway found!"
        else:
            giveaway_id, platform = result
            
            # Get participants
            cur.execute("""
                SELECT user_id FROM giveaway_participants WHERE giveaway_id = %s
            """, (giveaway_id,))
            participants = [row[0] for row in cur.fetchall()]
            
            cancellation_text = (
                "🚫 <b>Giveaway Cancelled</b>\n\n"
                f"⚠️ The <b>{platform}</b> giveaway has been cancelled by the administrators.\n\n"
                "😔 We apologize for the inconvenience.\n\n"
                "💡 <b>Don't worry!</b> Stay tuned for more giveaways coming soon!\n\n"
                "🔔 Keep checking back for new opportunities!")

            # Send notification to each participant
            for user_id in participants:
                try:
                    await context.bot.send_message(chat_id=int(user_id),
                                                   text=cancellation_text,
                                                   parse_mode='HTML')
                except Exception as e:
                    logger.error(f"Failed to notify user {user_id}: {e}")

            # Deactivate giveaway
            cur.execute("UPDATE giveaways SET active = false WHERE id = %s", (giveaway_id,))
            
            text = f"🛑 <b>Giveaway Stopped</b>\n\n✅ The giveaway has been stopped successfully!\n\n📨 Sent cancellation notifications to {len(participants)} participant(s)."
        
        cur.close()

    keyboard = [[
        InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=text,
                                  reply_markup=reply_markup,
                                  parse_mode='HTML')


async def revoke_key_platform(update: Update,
                              context: ContextTypes.DEFAULT_TYPE):
    """Show platform selection for key revocation"""
    query = update.callback_query
    await query.answer()

    platforms = get_platforms()
    keyboard = []
    for platform in platforms:
        keyboard.append([
            InlineKeyboardButton(
                f"{platform['emoji']} {platform['name']}",
                callback_data=f"admin_revoke_platform_{platform['name'].lower()}")
        ])
    keyboard.append(
        [InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text="❌ <b>Revoke Keys</b>\n\nSelect the platform:",
        reply_markup=reply_markup,
        parse_mode='HTML')


async def revoke_key_options(update: Update,
                             context: ContextTypes.DEFAULT_TYPE, platform):
    """Show revoke options"""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "🔙 Revoke Last Generated",
                callback_data=f"admin_revoke_option_last_{platform}")
        ],
        [
            InlineKeyboardButton(
                "🗑️ Revoke All Keys",
                callback_data=f"admin_revoke_option_all_{platform}")
        ],
        [
            InlineKeyboardButton(
                "✅ Revoke Claimed Keys",
                callback_data=f"admin_revoke_option_claimed_{platform}")
        ],
        [
            InlineKeyboardButton("🔙 Back to Revoke Platform",
                                 callback_data="admin_revoke_key")
        ], [InlineKeyboardButton("🏠 Main Menu", callback_data="admin_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.user_data['revoke_platform'] = platform
    
    await query.edit_message_text(
        text=f"❌ <b>Revoke {platform.capitalize()} Keys</b>\n\nSelect an option:",
        reply_markup=reply_markup,
        parse_mode='HTML')


async def revoke_key_execute(update: Update,
                             context: ContextTypes.DEFAULT_TYPE):
    """Execute key revocation"""
    query = update.callback_query
    await query.answer()

    platform = context.user_data.get('revoke_platform')
    option = context.user_data.get('revoke_option')

    if not platform or not option:
        await query.edit_message_text("❌ Error: Missing revoke details. Please start over.", parse_mode='HTML')
        return

    with get_db_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM platforms WHERE name ILIKE %s", (platform,))
        platform_result = cur.fetchone()
        if not platform_result:
            await query.edit_message_text("❌ Platform not found!", parse_mode='HTML')
            return
        
        platform_id = platform_result[0]
        
        count = 0
        if option == "last":
            cur.execute("""
                DELETE FROM keys 
                WHERE id = (SELECT id FROM keys WHERE platform_id = %s ORDER BY created_at DESC LIMIT 1)
            """, (platform_id,))
            count = cur.rowcount
        elif option == "all":
            cur.execute("DELETE FROM keys WHERE platform_id = %s", (platform_id,))
            count = cur.rowcount
        elif option == "claimed":
            cur.execute("DELETE FROM keys WHERE platform_id = %s AND status = 'used'", (platform_id,))
            count = cur.rowcount
        
        cur.close()

    text = (f"✅ <b>Keys Revoked</b>\n\n"
            f"Successfully revoked {count} {platform.capitalize()} key(s)!")

    keyboard = [[
        InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=text,
                                  reply_markup=reply_markup,
                                  parse_mode='HTML')

def get_project_root():
    """Get the project root directory (parent of bot folder)"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

async def handle_admin_message(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
    """Handle admin text messages"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        return

    # Handle key generation steps
    if context.user_data.get('gen_step') == 'count':
        try:
            count = int(update.message.text)
            context.user_data['gen_count'] = count
            context.user_data['gen_step'] = 'uses'

            keyboard = [[
                InlineKeyboardButton("❌ Cancel", callback_data="admin_main")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"🎯 <b>Count: {count}</b>\n\n"
                f"How many times can each key be used?\n\n"
                f"📝 Please send a number (e.g., 1):",
                reply_markup=reply_markup,
                parse_mode='HTML')
        except ValueError:
            keyboard = [[
                InlineKeyboardButton("🔙 Back to Main",
                                     callback_data="admin_main")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("❌ Please send a valid number!",
                                            reply_markup=reply_markup,
                                            parse_mode='HTML')

    elif context.user_data.get('gen_step') == 'uses':
        try:
            uses = int(update.message.text)
            context.user_data['gen_uses'] = uses
            context.user_data['gen_step'] = 'account_text'

            keyboard = [[
                InlineKeyboardButton("❌ Cancel", callback_data="admin_main")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"✅ <b>Uses: {uses}</b>\n\n"
                f"What account type is this?\n\n"
                f"📝 Please send the account text (e.g., Premium Account):",
                reply_markup=reply_markup,
                parse_mode='HTML')
        except ValueError:
            keyboard = [[
                InlineKeyboardButton("🔙 Back to Main",
                                     callback_data="admin_main")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("❌ Please send a valid number!",
                                            reply_markup=reply_markup,
                                            parse_mode='HTML')

    elif context.user_data.get('gen_step') == 'account_text':
        account_text = update.message.text.strip()

        # Generate keys
        platform = context.user_data.get('gen_platform')
        count = context.user_data.get('gen_count')
        uses = context.user_data.get('gen_uses')

        if not platform or count is None or uses is None:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("❌ Error: Missing data. Please start over.", reply_markup=reply_markup, parse_mode='HTML')
            context.user_data.pop('gen_step', None)
            context.user_data.pop('gen_platform', None)
            context.user_data.pop('gen_count', None)
            context.user_data.pop('gen_uses', None)
            return

        platform_name = get_platform_display_name(platform)
        generated_keys = []

        for _ in range(count):
            key_code = generate_key_code(platform_name)
            add_key(key_code, platform_name, uses, account_text)
            generated_keys.append(key_code)

        # Clear user data
        context.user_data.pop('gen_step', None)
        context.user_data.pop('gen_platform', None)
        context.user_data.pop('gen_count', None)
        context.user_data.pop('gen_uses', None)

        keys_text = "\n".join([f"<code>{k}</code>" for k in generated_keys])

        # Create keyboard for back button
        keyboard = [[
            InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send platform image with keys
        project_root = get_project_root()
        platform_images = {
            'netflix': 'attached_assets/platforms/netflix.png',
            'crunchyroll': 'attached_assets/platforms/crunchyroll.png',
            'wwe': 'attached_assets/platforms/wwe.png',
            'paramountplus': 'attached_assets/platforms/paramountplus.png',
            'dazn': 'attached_assets/platforms/dazn.png',
            'molotovtv': 'attached_assets/platforms/molotovtv.png',
            'disneyplus': 'attached_assets/platforms/disneyplus.png',
            'psnfa': 'attached_assets/platforms/psnfa.png',
            'xbox': 'attached_assets/platforms/xbox.png'
        }

        caption_text = (f"🔑 <b>Generated Keys for {platform_name}</b>\n\n"
                        f"📊 Created {count} key(s):\n"
                        f"{keys_text}\n\n"
                        f"✅ Keys saved to database!\n"
                        f"💡 <i>Tap to copy!</i>")

        image_path = platform_images.get(platform.lower())
        if image_path:
            image_path = os.path.join(project_root, image_path)
            
        # Try to send with image, fall back to text if image doesn't exist
        try:
            if image_path and os.path.exists(image_path) and os.path.getsize(image_path) > 0:
                with open(image_path, 'rb') as photo:
                    await update.message.reply_photo(photo=photo,
                                                     caption=caption_text,
                                                     reply_markup=reply_markup,
                                                     parse_mode='HTML')
            else:
                await update.message.reply_text(caption_text,
                                                reply_markup=reply_markup,
                                                parse_mode='HTML')
        except Exception as e:
            logger.error(f"Failed to send image, sending text instead: {e}")
            await update.message.reply_text(caption_text,
                                            reply_markup=reply_markup,
                                            parse_mode='HTML')

    # Handle giveaway winner count
    elif context.user_data.get('giveaway_step') == 'winners':
        try:
            winners = int(update.message.text)
            duration_str = context.user_data.get('giveaway_duration')
            platform = context.user_data.get('giveaway_platform', 'Unknown')

            if not duration_str or not platform:
                 await update.message.reply_text("❌ Error: Missing giveaway details. Please start over.", parse_mode='HTML')
                 return

            duration_seconds = parse_duration(duration_str)
            end_time = datetime.now() + timedelta(seconds=duration_seconds)

            # Create giveaway in database
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # Deactivate any active giveaways
                cur.execute("UPDATE giveaways SET active = false WHERE active = true")
                
                # Get platform ID
                cur.execute("SELECT id FROM platforms WHERE name ILIKE %s", (platform,))
                platform_result = cur.fetchone()
                if platform_result:
                    platform_id = platform_result[0]
                    
                    # Insert new giveaway
                    cur.execute("""
                        INSERT INTO giveaways (platform_id, active, duration, winners, end_time)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (platform_id, True, duration_str, winners, end_time))
                
                cur.close()

            context.user_data.pop('giveaway_step', None)
            context.user_data.pop('giveaway_duration', None)
            context.user_data.pop('giveaway_platform', None)

            keyboard = [[
                InlineKeyboardButton("🔙 Back to Main",
                                     callback_data="admin_main")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"🎁 <b>Giveaway Started!</b>\n\n"
                f"🎮 <b>Platform:</b> {platform.capitalize()}\n"
                f"⏱️ <b>Duration:</b> {duration_str}\n"
                f"🏆 <b>Winners:</b> {winners}\n"
                f"⏰ <b>Ends at:</b> {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"✅ Users can now participate!",
                reply_markup=reply_markup,
                parse_mode='HTML')
        except ValueError:
            keyboard = [[
                InlineKeyboardButton("🔙 Back to Main",
                                     callback_data="admin_main")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("❌ Please send a valid number!",
                                            reply_markup=reply_markup,
                                            parse_mode='HTML')
        except Exception as e:
            logger.error(f"Error setting up giveaway: {e}")
            await update.message.reply_text(f"❌ An error occurred: {e}", parse_mode='HTML')


    # Handle credential generation
    elif context.user_data.get('cred_step') == 'count':
        try:
            count = int(update.message.text)
            platform = context.user_data.get('cred_platform', '').lower()

            # Get platform name
            platform_title = get_platform_display_name(platform)
            
            # Check if platform has active credentials in database
            from db_helpers import get_credentials_by_platform
            credentials = get_credentials_by_platform(platform_title)
            active_creds = [c for c in credentials if c['status'] == 'active']
            
            if not active_creds:
                keyboard = [[
                    InlineKeyboardButton("🔙 Back to Main",
                                         callback_data="admin_main")
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"❌ <b>No Active Credentials</b>\n\n"
                    f"There are no active credentials for {platform_title} in the database.\n\n"
                    f"Please add credentials through the admin panel first!",
                    reply_markup=reply_markup,
                    parse_mode='HTML')
                context.user_data.pop('cred_step', None)
                context.user_data.pop('cred_platform', None)
                return

            if len(active_creds) < count:
                keyboard = [[
                    InlineKeyboardButton("🔙 Back to Main",
                                         callback_data="admin_main")
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"❌ <b>Insufficient Credentials</b>\n\n"
                    f"You requested {count} keys but only {len(active_creds)} active credentials are available.\n\n"
                    f"Please add more credentials or reduce the number of keys.",
                    reply_markup=reply_markup,
                    parse_mode='HTML')
                context.user_data.pop('cred_step', None)
                context.user_data.pop('cred_platform', None)
                return

            # Generate keys
            from db_helpers import add_key
            keys_generated = []
            
            for i in range(count):
                key_code = generate_key(platform_title)
                account_text = active_creds[i]['email']  # Use email as account text
                add_key(key_code, platform_title, uses=1, account_text=account_text)
                keys_generated.append(key_code)
            
            keyboard = [[
                InlineKeyboardButton("🔙 Back to Main",
                                     callback_data="admin_main")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            keys_list = "\n".join([f"• <code>{k}</code>" for k in keys_generated])
            
            await update.message.reply_text(
                f"✅ <b>Keys Generated Successfully!</b>\n\n"
                f"🎮 <b>Platform:</b> {platform_title}\n"
                f"🔑 <b>Count:</b> {count}\n\n"
                f"<b>Generated Keys:</b>\n{keys_list}\n\n"
                f"💡 Users can redeem these keys to get accounts!",
                reply_markup=reply_markup,
                parse_mode='HTML')
            
            context.user_data.pop('cred_step', None)
            context.user_data.pop('cred_platform', None)
            
        except ValueError:
            keyboard = [[
                InlineKeyboardButton("🔙 Back to Main",
                                     callback_data="admin_main")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("❌ Please send a valid number!",
                                            reply_markup=reply_markup,
                                            parse_mode='HTML')
        except Exception as e:
            logger.error(f"Error setting up giveaway: {e}")
            await update.message.reply_text(f"❌ An error occurred: {e}", parse_mode='HTML')dential_file_path}` doesn't exist.\n\n"
                    f"Please create it first with some credentials!",
                    reply_markup=reply_markup,
                    parse_mode='HTML')
                context.user_data.pop('cred_step', None)
                context.user_data.pop('cred_platform', None)
                return

            with open(credential_file_path, 'r') as f:
                credentials = json.load(f)

            # Separate credentials by status: active first, then claimed, then used/others
            active_creds = [
                c for c in credentials if c.get('status') == 'active'
            ]
            claimed_creds = [
                c for c in credentials if c.get('status') == 'claimed'
            ]
            other_creds = [
                c for c in credentials
                if c.get('status') not in ['active', 'claimed']
            ]

            # Combine in priority order: active > claimed > others
            available_creds = active_creds + claimed_creds + other_creds

            if count > len(available_creds):
                keyboard = [[
                    InlineKeyboardButton("🔙 Back to Main",
                                         callback_data="admin_main")
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"❌ <b>Not Enough Credentials</b>\n\n"
                    f"You requested {count} credentials but only {len(available_creds)} are available.\n\n"
                    f"Please add more credentials in the admin panel first!",
                    reply_markup=reply_markup,
                    parse_mode='HTML')
                context.user_data.pop('cred_step', None)
                context.user_data.pop('cred_platform', None)
                return

            # Get the requested credentials (active ones first)
            creds_to_send = available_creds[:count]
            creds_text = ""

            # Count active vs non-active
            active_count = sum(1 for c in creds_to_send
                               if c.get('status') == 'active')
            non_active_count = count - active_count

            for i, cred in enumerate(creds_to_send, 1):
                status_emoji = "✅" if cred.get(
                    'status') == 'active' else "🔄" if cred.get(
                        'status') == 'claimed' else "❌"
                creds_text += f"\n<b>Account {i}:</b> {status_emoji}\n"
                creds_text += f"📧 Email: <code>{cred['email']}</code>\n"
                creds_text += f"🔑 Password: <code>{cred['password']}</code>\n"
                creds_text += f"📊 Status: {cred.get('status', 'unknown')}\n"

            # Add warning if non-active credentials are included
            warning_text = ""
            if non_active_count > 0:
                warning_text = f"\n\n⚠️ <b>Warning:</b> {non_active_count} credential(s) are already claimed/used. Only {active_count} are fresh and ready to distribute."

            context.user_data.pop('cred_step', None)
            context.user_data.pop('cred_platform', None)

            keyboard = [[
                InlineKeyboardButton("🔙 Back to Main",
                                     callback_data="admin_main")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send platform image with credentials
            project_root = get_project_root()
            platform_images = {
                'netflix': 'attached_assets/platforms/netflix.png',
                'crunchyroll': 'attached_assets/platforms/crunchyroll.png',
                'wwe': 'attached_assets/platforms/wwe.png',
                'paramountplus': 'attached_assets/platforms/paramountplus.png',
                'dazn': 'attached_assets/platforms/dazn.png',
                'molotovtv': 'attached_assets/platforms/molotovtv.png',
                'disneyplus': 'attached_assets/platforms/disneyplus.png',
                'psnfa': 'attached_assets/platforms/psnfa.png',
                'xbox': 'attached_assets/platforms/xbox.png'
            }

            caption_text = (f"🎫 <b>{platform.capitalize()} Credentials</b>\n\n"
                            f"📊 Retrieved {count} credential(s):\n"
                            f"{creds_text}{warning_text}\n\n"
                            f"💡 <i>Tap to copy!</i>")

            image_path = platform_images.get(platform)
            if image_path:
                image_path = os.path.join(project_root, image_path)

            # Try to send with image, fall back to text if image doesn't exist
            try:
                if image_path and os.path.exists(image_path) and os.path.getsize(image_path) > 0:
                    with open(image_path, 'rb') as photo:
                        await update.message.reply_photo(photo=photo,
                                                         caption=caption_text,
                                                         reply_markup=reply_markup,
                                                         parse_mode='HTML')
                else:
                    await update.message.reply_text(caption_text,
                                                    reply_markup=reply_markup,
                                                    parse_mode='HTML')
            except Exception as e:
                logger.error(f"Failed to send image, sending text instead: {e}")
                await update.message.reply_text(caption_text,
                                                reply_markup=reply_markup,
                                                parse_mode='HTML')
        except ValueError:
            keyboard = [[
                InlineKeyboardButton("🔙 Back to Main",
                                     callback_data="admin_main")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("❌ Please send a valid number!",
                                            reply_markup=reply_markup,
                                            parse_mode='HTML')
        except Exception as e:
             logger.error(f"Error handling credentials: {e}")
             await update.message.reply_text(f"❌ An error occurred: {e}", parse_mode='HTML')


    # Handle broadcast
    elif context.user_data.get('broadcast_step') == 'message':
        message = update.message.text
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM users")
            user_ids = [row[0] for row in cur.fetchall()]
            cur.close()

        success_count = 0
        fail_count = 0

        for user_id_str in user_ids:
            try:
                await context.bot.send_message(
                    chat_id=int(user_id_str),
                    text=f"📢 <b>Broadcast Message</b>\n\n{message}",
                    parse_mode='HTML')
                success_count += 1
            except Exception as e:
                fail_count += 1
                logger.error(f"Failed to send broadcast to {user_id_str}: {e}")

        context.user_data.pop('broadcast_step', None)

        keyboard = [[
            InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"📢 <b>Broadcast Complete</b>\n\n"
            f"✅ Successfully sent to {success_count} users\n"
            f"❌ Failed to send to {fail_count} users",
            reply_markup=reply_markup,
            parse_mode='HTML')

    # Handle ban user
    elif context.user_data.get('ban_step') == 'user_id':
        user_input = update.message.text.strip()

        # Try to extract user ID
        if user_input.startswith('@'):
            user_identifier = user_input
        else:
            try:
                user_identifier = str(int(user_input))
            except ValueError:
                keyboard = [[
                    InlineKeyboardButton("🔙 Back to Main",
                                         callback_data="admin_main")
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "❌ Invalid user ID or username!",
                    reply_markup=reply_markup,
                    parse_mode='HTML')
                return

        if not db_is_user_banned(user_identifier):
            db_ban_user(user_identifier)
            context.user_data.pop('ban_step', None)

            keyboard = [[
                InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"🚫 <b>User Banned</b>\n\n"
                f"✅ User {user_input} has been banned from using the bot!",
                reply_markup=reply_markup,
                parse_mode='HTML')
        else:
            keyboard = [[
                InlineKeyboardButton("🔙 Back to Main", callback_data="admin_main")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("❌ User is already banned!",
                                            reply_markup=reply_markup,
                                            parse_mode='HTML')


async def check_and_process_giveaways(context: ContextTypes.DEFAULT_TYPE):
    """Background job to check for expired giveaways and select winners"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Get active giveaway that has ended
            cur.execute("""
                SELECT g.id, g.winners, p.name
                FROM giveaways g
                JOIN platforms p ON g.platform_id = p.id
                WHERE g.active = true AND g.end_time <= NOW()
            """)
            expired_giveaways = cur.fetchall()
            
            if not expired_giveaways:
                return

            for giveaway_id, num_winners, platform in expired_giveaways:
                # Get participants
                cur.execute("""
                    SELECT user_id FROM giveaway_participants WHERE giveaway_id = %s
                """, (giveaway_id,))
                participants = [row[0] for row in cur.fetchall()]
                
                # If no participants, just deactivate
                if not participants:
                    cur.execute("UPDATE giveaways SET active = false WHERE id = %s", (giveaway_id,))
                    logger.info(f"Giveaway {giveaway_id} ({platform}): No participants. Deactivating.")
                    continue
                
                # Select random winners (don't select more winners than participants)
                actual_winners_count = min(num_winners, len(participants))
                winner_ids = random.sample(participants, actual_winners_count)
                
                logger.info(
                    f"Giveaway {giveaway_id} ({platform}): Selecting {actual_winners_count} winners from {len(participants)} participants."
                )

                # Platform images
                platform_images = {
                    'Netflix': 'attached_assets/platforms/netflix.png',
                    'Crunchyroll': 'attached_assets/platforms/crunchyroll.png',
                    'WWE': 'attached_assets/platforms/wwe.png',
                    'ParamountPlus': 'attached_assets/platforms/paramountplus.png',
                    'Dazn': 'attached_assets/platforms/dazn.png',
                    'MolotovTV': 'attached_assets/platforms/molotov.png',
                    'DisneyPlus': 'attached_assets/platforms/disneyplus.png',
                    'PSNFA': 'attached_assets/platforms/psnfa.png',
                    'Xbox': 'attached_assets/platforms/xbox.png'
                }
                image_path = platform_images.get(platform)
                project_root = get_project_root()
                if image_path:
                    image_path = os.path.join(project_root, image_path)

                # Generate and send keys to winners
                keys_distributed = 0
                for winner_id in winner_ids:
                    # Generate a new key for this winner
                    key_code = generate_key_code(platform)
                    account_text = f"{platform} Giveaway Prize"

                    # Add key to database
                    add_key(key_code, platform, 1, account_text, giveaway_generated=True, giveaway_winner=str(winner_id))

                    logger.info(
                        f"Generated new key {key_code} for giveaway winner {winner_id}"
                    )

                    # Create winner message
                    winner_text = (
                        f"🎉 <b>Congratulations! You Won!</b> 🎉\n\n"
                        f"🏆 You've been selected as a winner in the <b>{platform}</b> giveaway!\n\n"
                        f"🎁 <b>Your Prize:</b> {account_text}\n"
                        f"🔑 <b>Redemption Key:</b> <code>{key_code}</code>\n\n"
                        f"📝 <b>How to Redeem:</b>\n"
                        f"1️⃣ Use the /redeem command\n"
                        f"2️⃣ Send your key: <code>{key_code}</code>\n"
                        f"3️⃣ Get your account credentials!\n\n"
                        f"💡 <i>Tap the key to copy it!</i>\n\n"
                        f"💝 Thank you for participating in Premium Vault giveaways!")

                    # Send with platform image if available
                    try:
                        if image_path and os.path.exists(image_path):
                            with open(image_path, 'rb') as photo:
                                await context.bot.send_photo(chat_id=int(winner_id),
                                                             photo=photo,
                                                             caption=winner_text,
                                                             parse_mode='HTML')
                        else:
                            await context.bot.send_message(chat_id=int(winner_id),
                                                           text=winner_text,
                                                           parse_mode='HTML')
                        keys_distributed += 1
                        logger.info(f"Sent key to winner {winner_id}")
                    except Exception as e:
                        logger.error(f"Failed to send key to winner {winner_id}: {e}")

                # Deactivate the giveaway
                cur.execute("UPDATE giveaways SET active = false WHERE id = %s", (giveaway_id,))

                logger.info(
                    f"Giveaway {giveaway_id} ({platform}) processing complete. Distributed {keys_distributed} keys to {len(winner_ids)} winners."
                )
            cur.close()

    except Exception as e:
        logger.error(f"Error in check_and_process_giveaways: {e}")

def get_platform_display_name(platform):
    """Get proper platform display name"""
    platform_map = {
        'netflix': 'Netflix',
        'crunchyroll': 'Crunchyroll',
        'wwe': 'WWE',
        'paramountplus': 'ParamountPlus',
        'dazn': 'Dazn',
        'molotovtv': 'MolotovTV',
        'disneyplus': 'DisneyPlus',
        'psnfa': 'PSNFA',
        'xbox': 'Xbox'
    }
    return platform_map.get(platform.lower(), platform.capitalize())

def parse_duration(duration_str):
    """Parse duration string to seconds"""
    duration_str = duration_str.lower().strip()
    if duration_str.endswith('s'):
        return int(duration_str[:-1])
    elif duration_str.endswith('m'):
        return int(duration_str[:-1]) * 60
    elif duration_str.endswith('h'):
        return int(duration_str[:-1]) * 3600
    elif duration_str.endswith('d'):
        return int(duration_str[:-1]) * 86400
    else:
        try:
            return int(duration_str) # Assume seconds if no unit
        except ValueError:
            return 0 # Default to 0 if invalid

# Dummy function to satisfy linters if needed, actual implementation relies on get_db_connection
def load_json(file_path):
    """Placeholder for JSON loading, actual logic uses DB."""
    print(f"Attempted to load JSON from {file_path}, but using DB instead.")
    return [] # Return empty list as DB is used

import json # Import json for credential handling