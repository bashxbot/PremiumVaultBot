from db_setup import get_db_connection
from datetime import datetime
import json
import asyncio

PLATFORMS = ['netflix', 'crunchyroll', 'wwe', 'paramountplus', 'dazn', 'molotovtv', 'disneyplus', 'psnfa', 'xbox']

PLATFORM_DATA = [
    {'name': 'netflix', 'emoji': '🎬'},
    {'name': 'crunchyroll', 'emoji': '🍜'},
    {'name': 'wwe', 'emoji': '🤼'},
    {'name': 'paramountplus', 'emoji': '⭐'},
    {'name': 'dazn', 'emoji': '🥊'},
    {'name': 'molotovtv', 'emoji': '📺'},
    {'name': 'disneyplus', 'emoji': '🏰'},
    {'name': 'psnfa', 'emoji': '🎮'},
    {'name': 'xbox', 'emoji': '🎯'}
]

def get_platforms():
    """Get all platform names with emoji"""
    return PLATFORM_DATA

def get_platform_by_name(name):
    """Check if platform exists"""
    platform_lower = name.lower()
    if platform_lower in PLATFORMS:
        return {'name': platform_lower}
    return None

def add_credential(platform_name, email, password, status='active'):
    """Add a credential to platform-specific table"""
    platform_lower = platform_name.lower()
    if platform_lower not in PLATFORMS:
        return False

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            INSERT INTO {platform_lower}_credentials (email, password, status)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (email, password, status))
        cred_id = cur.fetchone()[0]
        cur.close()
        return cred_id

def get_credentials_by_platform(platform_name):
    """Get all credentials for a platform from platform-specific table"""
    platform_lower = platform_name.lower()
    if platform_lower not in PLATFORMS:
        return []

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, email, password, status, claimed_by, claimed_by_username, 
                   claimed_by_name, claimed_at, created_at
            FROM {platform_lower}_credentials
            ORDER BY created_at DESC
        """)
        credentials = cur.fetchall()
        cur.close()

        return [{
            'id': c[0],
            'email': c[1],
            'password': c[2],
            'status': c[3],
            'claimed_by': c[4],
            'claimed_by_username': c[5],
            'claimed_by_name': c[6],
            'claimed_at': c[7].isoformat() if c[7] else None,
            'created_at': c[8].isoformat() if c[8] else None
        } for c in credentials]

def update_credential(platform_name, cred_id, email=None, password=None, status=None):
    """Update a credential in platform-specific table"""
    platform_lower = platform_name.lower()
    if platform_lower not in PLATFORMS:
        return False

    with get_db_connection() as conn:
        cur = conn.cursor()
        updates = []
        params = []

        if email:
            updates.append("email = %s")
            params.append(email)
        if password:
            updates.append("password = %s")
            params.append(password)
        if status:
            updates.append("status = %s")
            params.append(status)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(cred_id)

        query = f"UPDATE {platform_lower}_credentials SET {', '.join(updates)} WHERE id = %s"
        cur.execute(query, params)
        cur.close()
        return True

def delete_credential(platform_name, cred_id):
    """Delete a credential from platform-specific table"""
    platform_lower = platform_name.lower()
    if platform_lower not in PLATFORMS:
        return False

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {platform_lower}_credentials WHERE id = %s", (cred_id,))
        cur.close()
        return True

def get_active_credential(platform_name):
    """Get an active credential for a platform from platform-specific table"""
    platform_lower = platform_name.lower()
    if platform_lower not in PLATFORMS:
        return None

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, email, password
            FROM {platform_lower}_credentials
            WHERE status = 'active'
            ORDER BY created_at ASC
            LIMIT 1
        """)
        cred = cur.fetchone()
        cur.close()

        if cred:
            return {'id': cred[0], 'email': cred[1], 'password': cred[2]}
        return None

def claim_credential(platform_name, cred_id, user_id, username=None, full_name=None):
    """Mark a credential as claimed with full user details in platform-specific table"""
    platform_lower = platform_name.lower()
    if platform_lower not in PLATFORMS:
        return False

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            UPDATE {platform_lower}_credentials
            SET status = 'claimed', 
                claimed_by = %s, 
                claimed_by_username = %s,
                claimed_by_name = %s,
                claimed_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (user_id, username, full_name, cred_id))
        cur.close()
        return True

def add_key(key_code, platform_name, uses, account_text, giveaway_generated=False, giveaway_winner=None):
    """Add a key to platform-specific table"""
    platform_lower = platform_name.lower()
    if platform_lower not in PLATFORMS:
        return False

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            INSERT INTO {platform_lower}_keys (key_code, uses, remaining_uses, account_text, giveaway_generated, giveaway_winner)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (key_code, uses, uses, account_text, giveaway_generated, giveaway_winner))
        key_id = cur.fetchone()[0]
        cur.close()
        return key_id

def get_key_by_code(key_code):
    """Get a key by its code - search across all platform tables"""
    for platform in PLATFORMS:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT id, key_code, uses, remaining_uses, account_text, status, 
                       created_at, redeemed_at, giveaway_generated, giveaway_winner
                FROM {platform}_keys
                WHERE key_code = %s
            """, (key_code,))
            key = cur.fetchone()
            cur.close()

            if key:
                return {
                    'id': key[0],
                    'key': key[1],
                    'platform': platform,
                    'uses': key[2],
                    'remaining_uses': key[3],
                    'account_text': key[4],
                    'status': key[5],
                    'created_at': key[6].isoformat() if key[6] else None,
                    'redeemed_at': key[7].isoformat() if key[7] else None,
                    'giveaway_generated': key[8],
                    'giveaway_winner': key[9]
                }
    return None

def get_keys_by_platform(platform_name):
    """Get all keys for a platform from platform-specific table"""
    platform_lower = platform_name.lower()
    if platform_lower not in PLATFORMS:
        return []

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, key_code, uses, remaining_uses, account_text, status, 
                   created_at, redeemed_at
            FROM {platform_lower}_keys
            ORDER BY created_at DESC
        """)
        keys = cur.fetchall()
        cur.close()

        result = []
        for k in keys:
            key_data = {
                'id': k[0],
                'key': k[1],
                'platform': platform_name,
                'uses': k[2],
                'remaining_uses': k[3],
                'account_text': k[4],
                'status': k[5],
                'created_at': k[6].isoformat() if k[6] else None,
                'redeemed_at': k[7].isoformat() if k[7] else None,
                'used_by': [],
                'redeemed_by': []
            }

            # Get redemption info with full user details using a new cursor
            with get_db_connection() as conn2:
                cur2 = conn2.cursor()
                cur2.execute("""
                    SELECT user_id, username, full_name, redeemed_at
                    FROM key_redemptions
                    WHERE platform = %s AND key_code = %s
                    ORDER BY redeemed_at DESC
                """, (platform_lower, k[1]))
                redemptions = cur2.fetchall()
                cur2.close()

            for r in redemptions:
                key_data['used_by'].append(r[0])
                key_data['redeemed_by'].append({
                    'user_id': r[0],
                    'username': r[1],
                    'full_name': r[2],
                    'redeemed_at': r[3].isoformat() if r[3] else None
                })

            result.append(key_data)

        return result

def redeem_key(platform_name, key_id, user_id, username=None, full_name=None):
    """Redeem a key with full user details from platform-specific table"""
    platform_lower = platform_name.lower()
    if platform_lower not in PLATFORMS:
        return False

    with get_db_connection() as conn:
        cur = conn.cursor()

        # Get key_code first
        cur.execute(f"SELECT key_code FROM {platform_lower}_keys WHERE id = %s", (key_id,))
        key_row = cur.fetchone()
        if not key_row:
            cur.close()
            return False
        key_code = key_row[0]

        # Update key
        cur.execute(f"""
            UPDATE {platform_lower}_keys
            SET remaining_uses = remaining_uses - 1,
                redeemed_at = CURRENT_TIMESTAMP,
                status = CASE WHEN remaining_uses - 1 <= 0 THEN 'used' ELSE status END
            WHERE id = %s
        """, (key_id,))

        # Add redemption record with full user details
        cur.execute("""
            INSERT INTO key_redemptions (platform, key_code, user_id, username, full_name)
            VALUES (%s, %s, %s, %s, %s)
        """, (platform_lower, key_code, user_id, username, full_name))

        cur.close()
        return True

def delete_keys_by_platform(platform_name):
    """Delete all keys for a platform from platform-specific table"""
    platform_lower = platform_name.lower()
    if platform_lower not in PLATFORMS:
        return False

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {platform_lower}_keys")
        cur.close()
        return True

def is_user_banned(user_id, username=None):
    """Check if user is banned"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        if username:
            cur.execute("""
                SELECT COUNT(*) FROM banned_users 
                WHERE user_identifier IN (%s, %s)
            """, (str(user_id), f"@{username}"))
        else:
            cur.execute("""
                SELECT COUNT(*) FROM banned_users 
                WHERE user_identifier = %s
            """, (str(user_id),))

        count = cur.fetchone()[0]
        cur.close()
        return count > 0

def ban_user(user_identifier):
    """Ban a user"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO banned_users (user_identifier)
            VALUES (%s)
            ON CONFLICT (user_identifier) DO NOTHING
        """, (user_identifier,))
        cur.close()
        return True

def get_or_create_user(user_id, username=None):
    """Get or create user"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (user_id, username)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET username = EXCLUDED.username
            RETURNING id
        """, (str(user_id), username))
        user_pk = cur.fetchone()[0]
        cur.close()
        return user_pk

def get_user_stats(user_id):
    """Get user statistics"""
    with get_db_connection() as conn:
        cur = conn.cursor()

        # Get user info
        cur.execute("""
            SELECT joined_at FROM users WHERE user_id = %s
        """, (str(user_id),))
        user = cur.fetchone()

        if not user:
            return None

        # Get redeemed keys from the new key_redemptions table
        cur.execute("""
            SELECT key_code, platform, redeemed_at
            FROM key_redemptions
            WHERE user_id = %s
            ORDER BY redeemed_at DESC
        """, (str(user_id),))
        redemptions = cur.fetchall()
        cur.close()

        return {
            'joined_at': user[0].isoformat() if user[0] else None,
            'redeemed_keys': [{
                'key': r[0],
                'platform': r[1],
                'redeemed_at': r[2].isoformat() if r[2] else None
            } for r in redemptions]
        }

def get_all_admin_telegram_ids():
    """Get all admin Telegram IDs from database"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT telegram_user_id 
            FROM admin_credentials 
            WHERE telegram_user_id IS NOT NULL AND telegram_user_id != ''
        """)
        results = cur.fetchall()
        cur.close()

        telegram_ids = []
        for row in results:
            if row[0] and str(row[0]).isdigit():
                telegram_ids.append(int(row[0]))
        return telegram_ids

async def notify_admins_key_redeemed(bot, platform, user_id, username, full_name, key_code):
    """Send notification to all admins when a key is redeemed"""
    import os

    # Get admin IDs from database
    admin_ids = get_all_admin_telegram_ids()

    # Add static admin and environment variable admins
    STATIC_ADMIN_ID = 6562270244
    if STATIC_ADMIN_ID not in admin_ids:
        admin_ids.append(STATIC_ADMIN_ID)

    # Add admins from environment variable
    _admin_ids_str = os.getenv('ADMIN_IDS', '')
    if _admin_ids_str:
        for id_str in _admin_ids_str.split(','):
            if id_str.strip() and id_str.strip().isdigit():
                admin_id = int(id_str.strip())
                if admin_id not in admin_ids:
                    admin_ids.append(admin_id)

    if not admin_ids:
        return

    username_text = f"@{username}" if username and username != "N/A" else "N/A"
    full_name_text = full_name if full_name else "N/A"

    message = (
        f"🎉 <b>Key Redeemed Successfully!</b>\n\n"
        f"🔑 <b>Key:</b> <code>{key_code}</code>\n"
        f"🎮 <b>Platform:</b> {platform}\n\n"
        f"👤 <b>User Information:</b>\n"
        f"├ <b>Name:</b> {full_name_text}\n"
        f"├ <b>Username:</b> {username_text}\n"
        f"└ <b>Chat ID:</b> <code>{user_id}</code>\n\n"
        f"⏰ <b>Redeemed At:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    for admin_id in admin_ids:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Failed to notify admin {admin_id}: {e}")

async def notify_admins_credential_claimed(bot, platform, user_id, username, full_name, email):
    """Send notification to all admins when a credential is claimed"""
    import os

    # Get admin IDs from database
    admin_ids = get_all_admin_telegram_ids()

    # Add static admin and environment variable admins
    STATIC_ADMIN_ID = 6562270244
    if STATIC_ADMIN_ID not in admin_ids:
        admin_ids.append(STATIC_ADMIN_ID)

    # Add admins from environment variable
    _admin_ids_str = os.getenv('ADMIN_IDS', '')
    if _admin_ids_str:
        for id_str in _admin_ids_str.split(','):
            if id_str.strip() and id_str.strip().isdigit():
                admin_id = int(id_str.strip())
                if admin_id not in admin_ids:
                    admin_ids.append(admin_id)

    if not admin_ids:
        return

    username_text = f"@{username}" if username else "N/A"
    full_name_text = full_name if full_name else "N/A"

    message = (
        f"📧 <b>Credential Claimed!</b>\n\n"
        f"🎮 <b>Platform:</b> {platform}\n"
        f"📧 <b>Email:</b> <code>{email}</code>\n\n"
        f"👤 <b>User Details:</b>\n"
        f"├ <b>Name:</b> {full_name_text}\n"
        f"├ <b>Chat ID:</b> <code>{user_id}</code>\n"
        f"└ <b>Username:</b> {username_text}\n\n"
        f"⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    for admin_id in admin_ids:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Failed to notify admin {admin_id}: {e}")