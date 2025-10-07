
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
import os
from datetime import datetime, timedelta
from functools import wraps
import secrets
from db_setup import get_db_connection
from db_helpers import (
    get_platforms, get_platform_by_name, get_credentials_by_platform,
    add_credential as db_add_credential, update_credential as db_update_credential,
    delete_credential as db_delete_credential, get_keys_by_platform
)

app = Flask(__name__, static_folder='admin-panel/dist', static_url_path='')
CORS(app)

# Generate or load persistent secret key
SECRET_KEY_FILE = '.flask_secret_key'
if os.path.exists(SECRET_KEY_FILE):
    with open(SECRET_KEY_FILE, 'r') as f:
        app.secret_key = f.read().strip()
else:
    app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
    with open(SECRET_KEY_FILE, 'w') as f:
        f.write(app.secret_key)

app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=86400)

PLATFORMS = ['netflix', 'crunchyroll', 'wwe', 'paramountplus', 'dazn', 'molotovtv', 'disneyplus', 'psnfa', 'xbox']

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT username, password, role 
            FROM admin_credentials 
            WHERE username = %s
        """, (username,))
        user = cur.fetchone()
        cur.close()
        
        if user and user[1] == password:
            session.permanent = True
            session['logged_in'] = True
            session['username'] = user[0]
            session['role'] = user[2]
            return jsonify({'success': True, 'role': user[2]})
    
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'logged_in' in session:
        return jsonify({'authenticated': True, 'role': session.get('role', 'admin'), 'username': session.get('username')})
    return jsonify({'authenticated': False})

@app.route('/api/admins', methods=['GET'])
@login_required
def get_admins():
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'message': 'Only owner can view admins'}), 403
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT username FROM admin_credentials 
            WHERE role = 'admin'
        """)
        admins = cur.fetchall()
        cur.close()
        
    safe_admins = [{'username': admin[0]} for admin in admins]
    return jsonify({'success': True, 'admins': safe_admins})

@app.route('/api/admins', methods=['POST'])
@login_required
def add_admin():
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'message': 'Only owner can add admins'}), 403
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO admin_credentials (username, password, role)
                VALUES (%s, %s, 'admin')
            """, (username, password))
            cur.close()
        return jsonify({'success': True, 'message': 'Admin added successfully'})
    except Exception as e:
        if 'duplicate key' in str(e).lower() or 'unique' in str(e).lower():
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admins/<username>', methods=['DELETE'])
@login_required
def delete_admin(username):
    if session.get('role') != 'owner':
        return jsonify({'success': False, 'message': 'Only owner can delete admins'}), 403
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM admin_credentials 
            WHERE username = %s AND role = 'admin'
        """, (username,))
        cur.close()
    
    return jsonify({'success': True, 'message': 'Admin deleted successfully'})

@app.route('/api/change-username', methods=['POST'])
@login_required
def change_username():
    data = request.json
    new_username = data.get('newUsername')
    
    if not new_username:
        return jsonify({'success': False, 'message': 'New username is required'}), 400
    
    current_username = session.get('username')
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE admin_credentials 
                SET username = %s 
                WHERE username = %s
            """, (new_username, current_username))
            cur.close()
        
        session['username'] = new_username
        return jsonify({'success': True, 'message': 'Username changed successfully'})
    except Exception as e:
        if 'duplicate key' in str(e).lower() or 'unique' in str(e).lower():
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.json
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'message': 'Current and new passwords are required'}), 400
    
    current_username = session.get('username')
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT password FROM admin_credentials 
            WHERE username = %s
        """, (current_username,))
        result = cur.fetchone()
        
        if not result or result[0] != current_password:
            cur.close()
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401
        
        cur.execute("""
            UPDATE admin_credentials 
            SET password = %s 
            WHERE username = %s
        """, (new_password, current_username))
        cur.close()
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})

@app.route('/api/telegram-id', methods=['GET'])
@login_required
def get_telegram_id():
    current_username = session.get('username')
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT telegram_user_id FROM admin_credentials 
            WHERE username = %s
        """, (current_username,))
        result = cur.fetchone()
        cur.close()
        
        telegram_id = result[0] if result and result[0] else ''
    
    return jsonify({'success': True, 'telegram_user_id': telegram_id})

@app.route('/api/telegram-id', methods=['POST'])
@login_required
def set_telegram_id():
    data = request.json
    telegram_id = data.get('telegramUserId', '').strip()
    
    if not telegram_id:
        return jsonify({'success': False, 'message': 'Telegram User ID is required'}), 400
    
    if not telegram_id.isdigit():
        return jsonify({'success': False, 'message': 'Telegram User ID must be a number'}), 400
    
    current_username = session.get('username')
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE admin_credentials 
            SET telegram_user_id = %s 
            WHERE username = %s
        """, (telegram_id, current_username))
        cur.close()
    
    return jsonify({'success': True, 'message': 'Telegram User ID updated successfully'})

@app.route('/api/stats')
@login_required
def get_stats():
    try:
        stats = {}
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            for platform in PLATFORMS:
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
                
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'active') as active,
                        COUNT(*) FILTER (WHERE status = 'claimed') as claimed,
                        COUNT(*) FILTER (WHERE status = 'inactive') as inactive
                    FROM credentials c
                    JOIN platforms p ON c.platform_id = p.id
                    WHERE p.name = %s
                """, (platform_title,))
                result = cur.fetchone()
                
                stats[platform] = {
                    'total': result[0] if result else 0,
                    'active': result[1] if result else 0,
                    'claimed': result[2] if result else 0,
                    'inactive': result[3] if result else 0
                }
            
            cur.execute("SELECT COUNT(*) FROM keys")
            total_keys = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM keys WHERE status = 'active'")
            active_keys = cur.fetchone()[0]
            
            cur.close()
        
        return jsonify({
            'success': True,
            'platforms': PLATFORMS,
            'stats': stats,
            'total_keys': total_keys,
            'active_keys': active_keys
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/credentials/<platform>', methods=['GET'])
@login_required
def get_credentials(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
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
    
    credentials = get_credentials_by_platform(platform_title)
    return jsonify({'success': True, 'credentials': credentials})

@app.route('/api/credentials/<platform>', methods=['POST'])
@login_required
def add_credential(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
    data = request.json
    email = data.get('email')
    password = data.get('password')
    status = data.get('status', 'active')
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400
    
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
    
    cred_id = db_add_credential(platform_title, email, password, status)
    if cred_id:
        return jsonify({'success': True, 'message': 'Credential added successfully'})
    return jsonify({'success': False, 'message': 'Failed to add credential'}), 500

@app.route('/api/credentials/<platform>/upload', methods=['POST'])
@login_required
def upload_credentials(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
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
    
    content = file.read().decode('utf-8')
    lines = content.strip().split('\n')
    
    added_count = 0
    skipped_count = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split(':')
        if len(parts) >= 2:
            email = parts[0].strip()
            password = parts[1].strip()
            status = parts[2].strip() if len(parts) >= 3 else 'active'
            
            if email and password and '@' in email:
                cred_id = db_add_credential(platform_title, email, password, status)
                if cred_id:
                    added_count += 1
                else:
                    skipped_count += 1
            else:
                skipped_count += 1
        else:
            skipped_count += 1
    
    message = f'Successfully added {added_count} credentials'
    if skipped_count > 0:
        message += f' ({skipped_count} skipped due to invalid format)'
    
    return jsonify({'success': True, 'message': message, 'added': added_count, 'skipped': skipped_count})

@app.route('/api/credentials/<platform>/<int:cred_id>', methods=['DELETE'])
@login_required
def delete_credential(platform, cred_id):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
    if db_delete_credential(platform, cred_id):
        return jsonify({'success': True, 'message': 'Credential deleted successfully'})
    
    return jsonify({'success': False, 'message': 'Failed to delete credential'}), 500

@app.route('/api/credentials/<platform>/<int:cred_id>', methods=['PUT'])
@login_required
def edit_credential(platform, cred_id):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
    data = request.json
    email = data.get('email')
    password = data.get('password')
    status = data.get('status')
    
    if db_update_credential(platform, cred_id, email, password, status):
        return jsonify({'success': True, 'message': 'Credential updated successfully'})
    
    return jsonify({'success': False, 'message': 'Failed to update credential'}), 500

@app.route('/api/credentials/<platform>/delete-all', methods=['DELETE'])
@login_required
def delete_all_credentials(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
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
        return jsonify({'success': False, 'message': 'Platform not found'}), 404
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM credentials WHERE platform_id = %s", (platform_data['id'],))
        cur.close()
    
    return jsonify({'success': True, 'message': f'All {platform} credentials deleted successfully'})

@app.route('/api/keys/<platform>/delete-all', methods=['DELETE'])
@login_required
def delete_all_keys(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
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
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM platforms WHERE name = %s", (platform_title,))
        result = cur.fetchone()
        if result:
            platform_id = result[0]
            cur.execute("DELETE FROM keys WHERE platform_id = %s", (platform_id,))
        cur.close()
    
    return jsonify({'success': True, 'message': f'All {platform} keys deleted successfully'})

@app.route('/api/keys/<platform>', methods=['GET'])
@login_required
def get_keys(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400
    
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
    
    platform_keys = get_keys_by_platform(platform_title)
    
    return jsonify({'success': True, 'keys': platform_keys})

@app.route('/api/redemption-history', methods=['GET'])
@login_required
def get_redemption_history():
    """Get history of all key redemptions with user details"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    kr.user_id,
                    kr.username,
                    kr.full_name,
                    kr.redeemed_at,
                    k.key_code,
                    p.name as platform
                FROM key_redemptions kr
                JOIN keys k ON kr.key_id = k.id
                JOIN platforms p ON k.platform_id = p.id
                ORDER BY kr.redeemed_at DESC
                LIMIT 100
            """)
            redemptions = cur.fetchall()
            cur.close()
            
            history = []
            for r in redemptions:
                history.append({
                    'user_id': r[0],
                    'username': r[1] if r[1] else 'N/A',
                    'full_name': r[2] if r[2] else 'N/A',
                    'redeemed_at': r[3].isoformat() if r[3] else None,
                    'key_code': r[4],
                    'platform': r[5]
                })
            
            return jsonify({'success': True, 'history': history})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/claim-history', methods=['GET'])
@login_required
def get_claim_history():
    """Get history of all credential claims with user details"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    c.claimed_by as user_id,
                    c.claimed_by_username,
                    c.claimed_by_name,
                    c.claimed_at,
                    c.email,
                    p.name as platform
                FROM credentials c
                JOIN platforms p ON c.platform_id = p.id
                WHERE c.status = 'claimed' AND c.claimed_by IS NOT NULL
                ORDER BY c.claimed_at DESC
                LIMIT 100
            """)
            claims = cur.fetchall()
            cur.close()
            
            history = []
            for c in claims:
                history.append({
                    'user_id': c[0],
                    'username': c[1] if c[1] else 'N/A',
                    'full_name': c[2] if c[2] else 'N/A',
                    'claimed_at': c[3].isoformat() if c[3] else None,
                    'email': c[4],
                    'platform': c[5]
                })
            
            return jsonify({'success': True, 'history': history})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/<path:path>')
def catch_all(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
