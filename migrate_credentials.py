#!/usr/bin/env python3
"""
Migration script to move credentials from JSON files to PostgreSQL
"""
import json
import os
from db_helpers import get_db_connection, get_platform_by_name

def migrate_admin_credentials():
    """Migrate admin credentials from JSON to PostgreSQL"""
    print("Migrating admin credentials...")
    
    if not os.path.exists('admin_credentials.json'):
        print("No admin_credentials.json found, skipping")
        return
    
    with open('admin_credentials.json', 'r') as f:
        data = json.load(f)
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        owner = data.get('owner', {})
        if owner:
            cur.execute("""
                INSERT INTO admin_credentials (username, password, role, telegram_user_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE 
                SET password = EXCLUDED.password,
                    role = EXCLUDED.role,
                    telegram_user_id = COALESCE(EXCLUDED.telegram_user_id, admin_credentials.telegram_user_id)
            """, (
                owner.get('username'),
                owner.get('password'),
                owner.get('role', 'owner'),
                owner.get('telegram_user_id')
            ))
            print(f"  Migrated owner: {owner.get('username')}")
        
        for admin in data.get('admins', []):
            cur.execute("""
                INSERT INTO admin_credentials (username, password, role, telegram_user_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE 
                SET password = EXCLUDED.password,
                    telegram_user_id = COALESCE(EXCLUDED.telegram_user_id, admin_credentials.telegram_user_id)
            """, (
                admin.get('username'),
                admin.get('password'),
                'admin',
                admin.get('telegram_user_id')
            ))
            print(f"  Migrated admin: {admin.get('username')}")
        
        conn.commit()
        cur.close()
    
    print("Admin credentials migration completed!")

def migrate_platform_credentials():
    """Migrate platform credentials from JSON to PostgreSQL"""
    print("\nMigrating platform credentials...")
    
    credentials_dir = 'credentials'
    if not os.path.exists(credentials_dir):
        print("No credentials directory found, skipping")
        return
    
    platforms = ['netflix', 'crunchyroll', 'wwe', 'paramountplus', 'dazn', 
                 'molotovtv', 'disneyplus', 'psnfa', 'xbox', 'spotify']
    
    total_migrated = 0
    
    for platform in platforms:
        filepath = os.path.join(credentials_dir, f'{platform}.json')
        if not os.path.exists(filepath):
            continue
        
        try:
            with open(filepath, 'r') as f:
                creds = json.load(f)
        except:
            print(f"  Skipping {platform}: invalid JSON")
            continue
        
        if not creds or not isinstance(creds, list):
            continue
        
        platform_title = platform.capitalize()
        if platform == 'paramountplus':
            platform_title = 'ParamountPlus'
        elif platform == 'molotovtv':
            platform_title = 'MolotovTV'
        elif platform == 'disneyplus':
            platform_title = 'DisneyPlus'
        elif platform == 'psnfa':
            platform_title = 'PSNFA'
        elif platform == 'xbox':
            platform_title = 'Xbox'
        elif platform == 'crunchyroll':
            platform_title = 'Crunchyroll'
        elif platform == 'wwe':
            platform_title = 'WWE'
        elif platform == 'dazn':
            platform_title = 'Dazn'
        
        platform_data = get_platform_by_name(platform_title)
        if not platform_data:
            print(f"  Platform {platform_title} not found in database, skipping")
            continue
        
        platform_id = platform_data['id']
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            for cred in creds:
                email = cred.get('email')
                password = cred.get('password')
                status = cred.get('status', 'active')
                claimed_by = cred.get('claimed_by')
                claimed_at = cred.get('claimed_at')
                
                if not email or not password:
                    continue
                
                cur.execute("""
                    SELECT id FROM credentials 
                    WHERE platform_id = %s AND email = %s
                """, (platform_id, email))
                
                existing = cur.fetchone()
                
                if existing:
                    cur.execute("""
                        UPDATE credentials 
                        SET password = %s, status = %s, claimed_by = %s, claimed_at = %s
                        WHERE id = %s
                    """, (password, status, claimed_by, claimed_at, existing[0]))
                else:
                    cur.execute("""
                        INSERT INTO credentials (platform_id, email, password, status, claimed_by, claimed_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (platform_id, email, password, status, claimed_by, claimed_at))
                    total_migrated += 1
            
            conn.commit()
            cur.close()
        
        print(f"  Migrated {len(creds)} credentials for {platform_title}")
    
    print(f"\nPlatform credentials migration completed! Total new: {total_migrated}")

if __name__ == "__main__":
    print("Starting credentials migration...\n")
    migrate_admin_credentials()
    migrate_platform_credentials()
    print("\n✅ All credentials migrated successfully!")
