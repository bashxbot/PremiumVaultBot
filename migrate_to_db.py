#!/usr/bin/env python
import json
import os
from datetime import datetime
from db_helpers import get_db_connection

def migrate_keys():
    """Migrate keys from JSON to database"""
    print("Migrating keys...")
    
    keys_file = 'data/keys.json'
    if not os.path.exists(keys_file):
        print("No keys.json found")
        return
    
    with open(keys_file, 'r') as f:
        keys = json.load(f)
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        for key_data in keys:
            # Get platform ID
            platform_name = key_data.get('platform', 'Netflix')
            cur.execute("SELECT id FROM platforms WHERE name = %s", (platform_name,))
            result = cur.fetchone()
            
            if not result:
                print(f"Platform {platform_name} not found, skipping key")
                continue
            
            platform_id = result[0]
            
            # Insert key
            cur.execute("""
                INSERT INTO keys (
                    key_code, platform_id, uses, remaining_uses, account_text,
                    status, created_at, redeemed_at, giveaway_generated, giveaway_winner
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (key_code) DO UPDATE SET key_code = EXCLUDED.key_code
                RETURNING id
            """, (
                key_data.get('key'),
                platform_id,
                key_data.get('uses', 1),
                key_data.get('remaining_uses', 1),
                key_data.get('account_text', ''),
                key_data.get('status', 'active'),
                key_data.get('created_at'),
                key_data.get('redeemed_at'),
                key_data.get('giveaway_generated', False),
                key_data.get('giveaway_winner')
            ))
            
            # Insert redemptions
            key_id = cur.fetchone()[0]
            for redemption in key_data.get('redeemed_by', []):
                cur.execute("""
                    INSERT INTO key_redemptions (key_id, user_id, username, redeemed_at)
                    VALUES (%s, %s, %s, %s)
                """, (
                    key_id,
                    redemption.get('user_id'),
                    redemption.get('username'),
                    redemption.get('redeemed_at')
                ))
        
        conn.commit()
        print(f"Migrated {len(keys)} keys")

def migrate_users():
    """Migrate users from JSON to database"""
    print("Migrating users...")
    
    users_file = 'data/users.json'
    if not os.path.exists(users_file):
        print("No users.json found")
        return
    
    with open(users_file, 'r') as f:
        users = json.load(f)
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        for user_id, user_data in users.items():
            cur.execute("""
                INSERT INTO users (user_id, username, joined_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
            """, (
                user_id,
                user_data.get('username'),
                user_data.get('joined_at')
            ))
        
        conn.commit()
        print(f"Migrated {len(users)} users")

def migrate_banned_users():
    """Migrate banned users from JSON to database"""
    print("Migrating banned users...")
    
    banned_file = 'data/banned.json'
    if not os.path.exists(banned_file):
        print("No banned.json found")
        return
    
    with open(banned_file, 'r') as f:
        banned = json.load(f)
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        for user_identifier in banned:
            cur.execute("""
                INSERT INTO banned_users (user_identifier)
                VALUES (%s)
                ON CONFLICT (user_identifier) DO NOTHING
            """, (user_identifier,))
        
        conn.commit()
        print(f"Migrated {len(banned)} banned users")

def migrate_giveaway():
    """Migrate giveaway from JSON to database"""
    print("Migrating giveaway...")
    
    giveaway_file = 'data/giveaway.json'
    if not os.path.exists(giveaway_file):
        print("No giveaway.json found")
        return
    
    with open(giveaway_file, 'r') as f:
        giveaway = json.load(f)
    
    if not giveaway.get('active'):
        print("No active giveaway to migrate")
        return
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Get platform ID
        platform_name = giveaway.get('platform')
        if platform_name:
            cur.execute("SELECT id FROM platforms WHERE name = %s", (platform_name,))
            result = cur.fetchone()
            
            if result:
                platform_id = result[0]
                
                # Insert giveaway
                cur.execute("""
                    INSERT INTO giveaways (
                        platform_id, active, duration, winners, end_time
                    ) VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    platform_id,
                    giveaway.get('active', False),
                    giveaway.get('duration', 0),
                    giveaway.get('winners', 1),
                    giveaway.get('end_time')
                ))
                
                giveaway_id = cur.fetchone()[0]
                
                # Insert participants
                for participant in giveaway.get('participants', []):
                    cur.execute("""
                        INSERT INTO giveaway_participants (giveaway_id, user_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (giveaway_id, participant))
        
        conn.commit()
        print("Migrated giveaway data")

if __name__ == "__main__":
    print("Starting migration from JSON to PostgreSQL...")
    print("=" * 50)
    
    try:
        migrate_keys()
        migrate_users()
        migrate_banned_users()
        migrate_giveaway()
        
        print("=" * 50)
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
