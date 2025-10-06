"""
Database operations to replace JSON file operations
"""
from db_helpers import get_db_connection
from datetime import datetime
import json

# Keys operations
def get_all_keys():
    """Get all keys from database"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT k.*, p.name as platform
            FROM keys k
            JOIN platforms p ON k.platform_id = p.id
            ORDER BY k.created_at DESC
        """)
        
        keys = []
        for row in cur.fetchall():
            keys.append({
                'key': row[1],
                'platform': row[10],
                'uses': row[3],
                'remaining_uses': row[4],
                'account_text': row[5],
                'status': row[6],
                'created_at': str(row[7]) if row[7] else None,
                'redeemed_at': str(row[8]) if row[8] else None,
                'giveaway_generated': row[9],
                'giveaway_winner': row[10] if len(row) > 10 else None
            })
        return keys

def get_keys_by_platform(platform_name):
    """Get keys for a specific platform"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT k.*, p.name as platform
            FROM keys k
            JOIN platforms p ON k.platform_id = p.id
            WHERE p.name = %s
            ORDER BY k.created_at DESC
        """, (platform_name,))
        
        keys = []
        for row in cur.fetchall():
            keys.append({
                'key': row[1],
                'platform': row[10],
                'uses': row[3],
                'remaining_uses': row[4],
                'account_text': row[5],
                'status': row[6],
                'created_at': str(row[7]) if row[7] else None,
                'redeemed_at': str(row[8]) if row[8] else None
            })
        return keys

def find_key_by_code(key_code):
    """Find a key by its code"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT k.*, p.name as platform
            FROM keys k
            JOIN platforms p ON k.platform_id = p.id
            WHERE k.key_code = %s
        """, (key_code,))
        
        row = cur.fetchone()
        if row:
            return {
                'id': row[0],
                'key': row[1],
                'platform': row[10],
                'uses': row[3],
                'remaining_uses': row[4],
                'account_text': row[5],
                'status': row[6],
                'created_at': str(row[7]) if row[7] else None,
                'redeemed_at': str(row[8]) if row[8] else None,
                'giveaway_generated': row[9] if len(row) > 9 else False
            }
        return None

def create_key(key_code, platform_name, uses, account_text, giveaway=False, winner=None):
    """Create a new key"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Get platform ID
        cur.execute("SELECT id FROM platforms WHERE name = %s", (platform_name,))
        result = cur.fetchone()
        if not result:
            return False
        
        platform_id = result[0]
        
        cur.execute("""
            INSERT INTO keys (
                key_code, platform_id, uses, remaining_uses, account_text,
                status, created_at, giveaway_generated, giveaway_winner
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            key_code, platform_id, uses, uses, account_text,
            'active', datetime.now(), giveaway, winner
        ))
        
        conn.commit()
        return True

def redeem_key(key_code, user_id, username=None):
    """Redeem a key"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Get key
        cur.execute("SELECT id, remaining_uses, status FROM keys WHERE key_code = %s", (key_code,))
        result = cur.fetchone()
        if not result:
            return False
        
        key_id, remaining_uses, status = result
        
        if status != 'active' or remaining_uses <= 0:
            return False
        
        # Update key
        new_remaining = remaining_uses - 1
        new_status = 'used' if new_remaining == 0 else 'active'
        redeemed_at = datetime.now() if new_remaining == 0 else None
        
        cur.execute("""
            UPDATE keys 
            SET remaining_uses = %s, status = %s, redeemed_at = %s
            WHERE id = %s
        """, (new_remaining, new_status, redeemed_at, key_id))
        
        # Add redemption record
        cur.execute("""
            INSERT INTO key_redemptions (key_id, user_id, username, redeemed_at)
            VALUES (%s, %s, %s, %s)
        """, (key_id, user_id, username, datetime.now()))
        
        conn.commit()
        return True

def delete_keys_by_platform(platform_name):
    """Delete all keys for a platform"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM keys
            WHERE platform_id = (SELECT id FROM platforms WHERE name = %s)
        """, (platform_name,))
        conn.commit()

# User operations
def get_user(user_id):
    """Get user by ID"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT user_id, username, joined_at
            FROM users
            WHERE user_id = %s
        """, (user_id,))
        
        row = cur.fetchone()
        if row:
            return {
                'user_id': row[0],
                'username': row[1],
                'joined_at': str(row[2]) if row[2] else None
            }
        return None

def create_user(user_id, username=None):
    """Create a new user"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (user_id, username, joined_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET username = %s
        """, (user_id, username, datetime.now(), username))
        conn.commit()

def get_all_users():
    """Get all users"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, joined_at FROM users")
        
        users = {}
        for row in cur.fetchall():
            users[row[0]] = {
                'username': row[1],
                'joined_at': str(row[2]) if row[2] else None
            }
        return users

# Banned users operations
def is_user_banned(user_identifier):
    """Check if user is banned"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM banned_users WHERE user_identifier = %s
        """, (user_identifier,))
        return cur.fetchone()[0] > 0

def ban_user(user_identifier):
    """Ban a user"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO banned_users (user_identifier, banned_at)
            VALUES (%s, %s)
            ON CONFLICT (user_identifier) DO NOTHING
        """, (user_identifier, datetime.now()))
        conn.commit()

def unban_user(user_identifier):
    """Unban a user"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM banned_users WHERE user_identifier = %s
        """, (user_identifier,))
        conn.commit()

def get_banned_users():
    """Get all banned users"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_identifier FROM banned_users")
        return [row[0] for row in cur.fetchall()]

# Giveaway operations
def get_active_giveaway():
    """Get active giveaway"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT g.id, g.platform_id, g.active, g.duration, g.winners, g.end_time, p.name
            FROM giveaways g
            JOIN platforms p ON g.platform_id = p.id
            WHERE g.active = true
            LIMIT 1
        """)
        
        row = cur.fetchone()
        if row:
            # Get participants
            cur.execute("""
                SELECT user_id FROM giveaway_participants WHERE giveaway_id = %s
            """, (row[0],))
            participants = [p[0] for p in cur.fetchall()]
            
            return {
                'active': row[2],
                'platform': row[6],
                'duration': row[3],
                'winners': row[4],
                'end_time': str(row[5]) if row[5] else None,
                'participants': participants
            }
        
        return {'active': False}

def create_giveaway(platform_name, duration, winners, end_time):
    """Create a giveaway"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Deactivate any active giveaways
        cur.execute("UPDATE giveaways SET active = false WHERE active = true")
        
        # Get platform ID
        cur.execute("SELECT id FROM platforms WHERE name = %s", (platform_name,))
        result = cur.fetchone()
        if not result:
            return None
        
        platform_id = result[0]
        
        cur.execute("""
            INSERT INTO giveaways (platform_id, active, duration, winners, end_time, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (platform_id, True, duration, winners, end_time, datetime.now()))
        
        giveaway_id = cur.fetchone()[0]
        conn.commit()
        return giveaway_id

def add_giveaway_participant(user_id):
    """Add participant to active giveaway"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Get active giveaway
        cur.execute("SELECT id FROM giveaways WHERE active = true LIMIT 1")
        result = cur.fetchone()
        if not result:
            return False
        
        giveaway_id = result[0]
        
        cur.execute("""
            INSERT INTO giveaway_participants (giveaway_id, user_id, joined_at)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (giveaway_id, user_id, datetime.now()))
        
        conn.commit()
        return True

def end_giveaway():
    """End active giveaway"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE giveaways SET active = false WHERE active = true")
        conn.commit()
