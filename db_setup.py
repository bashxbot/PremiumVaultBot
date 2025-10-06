
import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager

# Database connection pool
db_pool = None

def init_db_pool():
    """Initialize database connection pool"""
    global db_pool
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    # Use connection pooler for better performance
    database_url = database_url.replace('.us-east-2', '-pooler.us-east-2')
    
    db_pool = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=database_url
    )
    return db_pool

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    global db_pool
    if db_pool is None:
        init_db_pool()
    
    conn = db_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        db_pool.putconn(conn)

def init_database():
    """Create database tables if they don't exist"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Create platforms table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS platforms (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                emoji VARCHAR(10) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create credentials table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id SERIAL PRIMARY KEY,
                platform_id INTEGER REFERENCES platforms(id) ON DELETE CASCADE,
                email VARCHAR(255) NOT NULL,
                password VARCHAR(255) NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                claimed_by VARCHAR(50),
                claimed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create keys table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS keys (
                id SERIAL PRIMARY KEY,
                key_code VARCHAR(100) UNIQUE NOT NULL,
                platform_id INTEGER REFERENCES platforms(id) ON DELETE CASCADE,
                uses INTEGER DEFAULT 1,
                remaining_uses INTEGER DEFAULT 1,
                account_text VARCHAR(255),
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                redeemed_at TIMESTAMP,
                giveaway_generated BOOLEAN DEFAULT FALSE,
                giveaway_winner VARCHAR(50)
            )
        """)
        
        # Create key_redemptions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS key_redemptions (
                id SERIAL PRIMARY KEY,
                key_id INTEGER REFERENCES keys(id) ON DELETE CASCADE,
                user_id VARCHAR(50) NOT NULL,
                username VARCHAR(255),
                redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50) UNIQUE NOT NULL,
                username VARCHAR(255),
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create banned_users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (
                id SERIAL PRIMARY KEY,
                user_identifier VARCHAR(255) UNIQUE NOT NULL,
                banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create giveaways table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS giveaways (
                id SERIAL PRIMARY KEY,
                platform_id INTEGER REFERENCES platforms(id) ON DELETE CASCADE,
                active BOOLEAN DEFAULT TRUE,
                duration VARCHAR(10),
                winners INTEGER,
                end_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create giveaway_participants table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS giveaway_participants (
                id SERIAL PRIMARY KEY,
                giveaway_id INTEGER REFERENCES giveaways(id) ON DELETE CASCADE,
                user_id VARCHAR(50) NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(giveaway_id, user_id)
            )
        """)
        
        # Create admin_credentials table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admin_credentials (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'admin',
                telegram_user_id VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default platforms (excluding Spotify)
        platforms = [
            ('Netflix', '🎬'),
            ('Crunchyroll', '🍜'),
            ('WWE', '🤼'),
            ('ParamountPlus', '⭐'),
            ('Dazn', '🥊'),
            ('MolotovTV', '📺'),
            ('DisneyPlus', '🏰'),
            ('PSNFA', '🎮'),
            ('Xbox', '🎯')
        ]
        
        for name, emoji in platforms:
            cur.execute("""
                INSERT INTO platforms (name, emoji) 
                VALUES (%s, %s) 
                ON CONFLICT (name) DO NOTHING
            """, (name, emoji))
        
        # Insert default admin if not exists
        default_admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        default_admin_password = os.getenv('ADMIN_PASSWORD', 'changeme')
        
        cur.execute("""
            INSERT INTO admin_credentials (username, password, role)
            VALUES (%s, %s, 'owner')
            ON CONFLICT (username) DO NOTHING
        """, (default_admin_username, default_admin_password))
        
        conn.commit()
        cur.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    print("Database initialized successfully!")
