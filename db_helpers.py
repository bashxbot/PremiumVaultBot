
from db_setup import get_db_connection
from datetime import datetime
import json
import asyncio

def get_platforms():
    """Get all platforms"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, emoji FROM platforms ORDER BY name")
        platforms = cur.fetchall()
        cur.close()
        return [{'id': p[0], 'name': p[1], 'emoji': p[2]} for p in platforms]

def get_platform_by_name(name):
    """Get platform by name"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, emoji FROM platforms WHERE name = %s", (name,))
        platform = cur.fetchone()
        cur.close()
        if platform:
            return {'id': platform[0], 'name': platform[1], 'emoji': platform[2]}
        return None

def add_credential(platform_name, email, password, status='active'):
    """Add a credential"""
    platform = get_platform_by_name(platform_name)
    if not platform:
        return False
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO credentials (platform_id, email, password, status)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (platform['id'], email, password, status))
        cred_id = cur.fetchone()[0]
        cur.close()
        return cred_id

def get_credentials_by_platform(platform_name):
    """Get all credentials for a platform"""
    platform = get_platform_by_name(platform_name)
    if not platform:
        return []
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, email, password, status, claimed_by, claimed_at, created_at
            FROM credentials
            WHERE platform_id = %s
            ORDER BY created_at DESC
        """, (platform['id'],))
        credentials = cur.fetchall()
        cur.close()
        
        return [{
            'id': c[0],
            'email': c[1],
            'password': c[2],
            'status': c[3],
            'claimed_by': c[4],
            'claimed_at': c[5].isoformat() if c[5] else None,
            'created_at': c[6].isoformat() if c[6] else None
        } for c in credentials]

def update_credential(cred_id, email=None, password=None, status=None):
    """Update a credential"""
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
        
        query = f"UPDATE credentials SET {', '.join(updates)} WHERE id = %s"
        cur.execute(query, params)
        cur.close()
        return True

def delete_credential(cred_id):
    """Delete a credential"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM credentials WHERE id = %s", (cred_id,))
        cur.close()
        return True

def get_active_credential(platform_name):
    """Get an active credential for a platform"""
    platform = get_platform_by_name(platform_name)
    if not platform:
        return None
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, email, password
            FROM credentials
            WHERE platform_id = %s AND status = 'active'
            ORDER BY created_at ASC
            LIMIT 1
        """, (platform['id'],))
        cred = cur.fetchone()
        cur.close()
        
        if cred:
            return {'id': cred[0], 'email': cred[1], 'password': cred[2]}
        return None

def claim_credential(cred_id, user_id, username=None, full_name=None):
    """Mark a credential as claimed with full user details"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE credentials 
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
    """Add a key"""
    platform = get_platform_by_name(platform_name)
    if not platform:
        return False
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO keys (key_code, platform_id, uses, remaining_uses, account_text, giveaway_generated, giveaway_winner)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (key_code, platform['id'], uses, uses, account_text, giveaway_generated, giveaway_winner))
        key_id = cur.fetchone()[0]
        cur.close()
        return key_id

def get_key_by_code(key_code):
    """Get a key by its code"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT k.id, k.key_code, p.name, k.uses, k.remaining_uses, k.account_text, k.status, 
                   k.created_at, k.redeemed_at, k.giveaway_generated, k.giveaway_winner
            FROM keys k
            JOIN platforms p ON k.platform_id = p.id
            WHERE k.key_code = %s
        """, (key_code,))
        key = cur.fetchone()
        cur.close()
        
        if key:
            return {
                'id': key[0],
                'key': key[1],
                'platform': key[2],
                'uses': key[3],
                'remaining_uses': key[4],
                'account_text': key[5],
                'status': key[6],
                'created_at': key[7].isoformat() if key[7] else None,
                'redeemed_at': key[8].isoformat() if key[8] else None,
                'giveaway_generated': key[9],
                'giveaway_winner': key[10]
            }
        return None

def get_keys_by_platform(platform_name):
    """Get all keys for a platform"""
    platform = get_platform_by_name(platform_name)
    if not platform:
        return []
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT k.id, k.key_code, k.uses, k.remaining_uses, k.account_text, k.status, 
                   k.created_at, k.redeemed_at
            FROM keys k
            WHERE k.platform_id = %s
            ORDER BY k.created_at DESC
        """, (platform['id'],))
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
            
            # Get redemption info
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id, username, redeemed_at
                FROM key_redemptions
                WHERE key_id = %s
                ORDER BY redeemed_at DESC
            """, (k[0],))
            redemptions = cur.fetchall()
            cur.close()
            
            for r in redemptions:
                key_data['used_by'].append(r[0])
                key_data['redeemed_by'].append({
                    'user_id': r[0],
                    'username': r[1],
                    'redeemed_at': r[2].isoformat() if r[2] else None
                })
            
            result.append(key_data)
        
        return result

def redeem_key(key_id, user_id, username=None, full_name=None):
    """Redeem a key with full user details"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Update key
        cur.execute("""
            UPDATE keys 
            SET remaining_uses = remaining_uses - 1,
                redeemed_at = CURRENT_TIMESTAMP,
                status = CASE WHEN remaining_uses - 1 <= 0 THEN 'used' ELSE status END
            WHERE id = %s
        """, (key_id,))
        
        # Add redemption record with full user details
        cur.execute("""
            INSERT INTO key_redemptions (key_id, user_id, username, full_name)
            VALUES (%s, %s, %s, %s)
        """, (key_id, user_id, username, full_name))
        
        cur.close()
        return True

def delete_keys_by_platform(platform_name):
    """Delete all keys for a platform"""
    platform = get_platform_by_name(platform_name)
    if not platform:
        return False
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM keys
            WHERE platform_id = %s
        """, (platform['id'],))
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
        
        # Get redeemed keys
        cur.execute("""
            SELECT k.key_code, p.name, kr.redeemed_at
            FROM key_redemptions kr
            JOIN keys k ON kr.key_id = k.id
            JOIN platforms p ON k.platform_id = p.id
            WHERE kr.user_id = %s
            ORDER BY kr.redeemed_at DESC
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
    admin_ids = get_all_admin_telegram_ids()
    
    if not admin_ids:
        return
    
    username_text = f"@{username}" if username else "N/A"
    full_name_text = full_name if full_name else "N/A"
    
    message = (
        f"🎁 <b>Key Redeemed!</b>\n\n"
        f"🎮 <b>Platform:</b> {platform}\n"
        f"🔑 <b>Key:</b> <code>{key_code}</code>\n\n"
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

async def notify_admins_credential_claimed(bot, platform, user_id, username, full_name, email):
    """Send notification to all admins when a credential is claimed"""
    admin_ids = get_all_admin_telegram_ids()
    
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
