from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
import os
from datetime import datetime, timedelta
from functools import wraps
import secrets
import string
from db_setup import get_db_connection, init_db_pool, db_pool
from db_helpers import (
    get_platforms, get_platform_by_name, get_credentials_by_platform,
    add_credential as db_add_credential, update_credential as db_update_credential,
    delete_credential as db_delete_credential, get_keys_by_platform, add_key
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

def get_platform_title(platform):
    """Convert platform key to proper title format"""
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

def generate_key_code(platform):
    """Generate a unique key code using cryptographically secure random"""
    prefix = platform.upper()
    alphabet = string.ascii_uppercase + string.digits
    parts = [
        ''.join(secrets.choice(alphabet) for _ in range(4))
        for _ in range(3)
    ]
    return f"{prefix}-{'-'.join(parts)}"

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
        total_keys = 0
        active_keys = 0

        with get_db_connection() as conn:
            cur = conn.cursor()

            for platform in PLATFORMS:
                cur.execute(f"""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'active') as active,
                        COUNT(*) FILTER (WHERE status = 'claimed') as claimed,
                        COUNT(*) FILTER (WHERE status = 'inactive') as inactive
                    FROM {platform}_credentials
                """)
                result = cur.fetchone()

                stats[platform] = {
                    'total': result[0] if result else 0,
                    'active': result[1] if result else 0,
                    'claimed': result[2] if result else 0,
                    'inactive': result[3] if result else 0
                }

                cur.execute(f"SELECT COUNT(*) FROM {platform}_keys")
                platform_total_keys = cur.fetchone()[0]
                total_keys += platform_total_keys

                cur.execute(f"SELECT COUNT(*) FROM {platform}_keys WHERE status = 'active'")
                platform_active_keys = cur.fetchone()[0]
                active_keys += platform_active_keys

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

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, email, password, status, created_at, updated_at
            FROM {platform}_credentials
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        cur.close()

        credentials = []
        for row in rows:
            credentials.append({
                'id': row[0],
                'email': row[1],
                'password': row[2],
                'status': row[3],
                'created_at': row[4].isoformat() if row[4] else None,
                'updated_at': row[5].isoformat() if row[5] else None
            })

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

    platform_title = get_platform_title(platform)

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

    platform_title = get_platform_title(platform)

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

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {platform}_credentials WHERE id = %s", (cred_id,))
        deleted = cur.rowcount > 0
        cur.close()

    if deleted:
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

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            UPDATE {platform}_credentials 
            SET email = %s, password = %s, status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (email, password, status, cred_id))
        updated = cur.rowcount > 0
        cur.close()

    if updated:
        return jsonify({'success': True, 'message': 'Credential updated successfully'})

    return jsonify({'success': False, 'message': 'Failed to update credential'}), 500

@app.route('/api/credentials/<platform>/claimed', methods=['GET'])
@login_required
def get_claimed_credentials(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400

    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT id, email, claimed_by, claimed_by_username, claimed_by_name, claimed_at
                FROM {platform}_credentials
                WHERE status = 'claimed' AND claimed_by IS NOT NULL
                ORDER BY claimed_at DESC
            """)
            rows = cur.fetchall()
            cur.close()

            claimed = []
            for row in rows:
                claimed.append({
                    'id': row[0],
                    'email': row[1],
                    'claimed_by': row[2],
                    'claimed_by_username': row[3] if row[3] else 'N/A',
                    'claimed_by_name': row[4] if row[4] else 'N/A',
                    'claimed_at': row[5].isoformat() if row[5] else None
                })

        return jsonify({'success': True, 'claimed': claimed})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/credentials/<platform>/delete-all', methods=['DELETE'])
@login_required
def delete_all_credentials(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {platform}_credentials")
        cur.close()

    return jsonify({'success': True, 'message': f'All {platform} credentials deleted successfully'})

@app.route('/api/keys/<platform>/delete-all', methods=['DELETE'])
@login_required
def delete_all_keys(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {platform}_keys")
        cur.close()

    return jsonify({'success': True, 'message': f'All {platform} keys deleted successfully'})

@app.route('/api/keys/<platform>', methods=['GET'])
@login_required
def get_keys(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400

    try:
        platform_title = get_platform_title(platform)

        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT id, key_code, uses, remaining_uses, account_text, status, 
                       created_at, redeemed_at, giveaway_generated, giveaway_winner
                FROM {platform}_keys
                ORDER BY created_at DESC
            """)
            rows = cur.fetchall()
            cur.close()

            keys = []
            for row in rows:
                keys.append({
                    'id': row[0],
                    'key_code': row[1],
                    'uses': row[2],
                    'remaining_uses': row[3],
                    'account_text': row[4] if row[4] else '',
                    'status': row[5],
                    'created_at': row[6].isoformat() if row[6] else None,
                    'redeemed_at': row[7].isoformat() if row[7] else None,
                    'giveaway_generated': row[8] if row[8] else False,
                    'giveaway_winner': row[9] if row[9] else None
                })

        return jsonify({'success': True, 'keys': keys})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'keys': []}), 500

@app.route('/api/keys/<platform>', methods=['POST'])
@login_required
def generate_key(platform):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400

    data = request.json
    uses = data.get('uses', 1)
    account_text = data.get('account_text', '')[:255]

    try:
        uses = int(uses)
        if uses < 1 or uses > 100:
            return jsonify({'success': False, 'message': 'Uses must be between 1 and 100'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid uses value'}), 400

    platform_title = get_platform_title(platform)

    max_attempts = 5
    for attempt in range(max_attempts):
        key_code = generate_key_code(platform)
        key_id = add_key(key_code, platform_title, uses, account_text)
        if key_id:
            return jsonify({
                'success': True, 
                'message': 'Key generated successfully',
                'key_code': key_code
            })

    return jsonify({'success': False, 'message': 'Failed to generate unique key after multiple attempts'}), 500

@app.route('/api/keys/<platform>/<int:key_id>', methods=['DELETE'])
@login_required
def delete_key(platform, key_id):
    if platform not in PLATFORMS:
        return jsonify({'success': False, 'message': 'Invalid platform'}), 400

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {platform}_keys WHERE id = %s", (key_id,))
        deleted = cur.rowcount > 0
        cur.close()

    if deleted:
        return jsonify({'success': True, 'message': 'Key deleted successfully'})

    return jsonify({'success': False, 'message': 'Failed to delete key'}), 500

@app.route('/api/redemption-history', methods=['GET'])
@login_required
def get_redemption_history():
    """Get history of all key redemptions with user details"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    user_id,
                    username,
                    full_name,
                    redeemed_at,
                    key_code,
                    platform
                FROM key_redemptions
                ORDER BY redeemed_at DESC
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
        history = []

        with get_db_connection() as conn:
            cur = conn.cursor()

            for platform in PLATFORMS:
                cur.execute(f"""
                    SELECT 
                        claimed_by as user_id,
                        claimed_by_username,
                        claimed_by_name,
                        claimed_at,
                        email
                    FROM {platform}_credentials
                    WHERE status = 'claimed' AND claimed_by IS NOT NULL
                    ORDER BY claimed_at DESC
                    LIMIT 100
                """)
                claims = cur.fetchall()

                for c in claims:
                    history.append({
                        'user_id': c[0],
                        'username': c[1] if c[1] else 'N/A',
                        'full_name': c[2] if c[2] else 'N/A',
                        'claimed_at': c[3].isoformat() if c[3] else None,
                        'email': c[4],
                        'platform': platform
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