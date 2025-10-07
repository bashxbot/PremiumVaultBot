
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
    
    # Parse the URL to extract components
    from urllib.parse import urlparse
    parsed = urlparse(database_url)
    
    # Resolve hostname to IPv4 address
    import socket
    ipv4_addr = None
    try:
        # Force IPv4 resolution by explicitly requesting AF_INET family
        result = socket.getaddrinfo(
            parsed.hostname, 
            None,  # Don't need port for resolution
            socket.AF_INET,  # IPv4 only
            socket.SOCK_STREAM
        )
        if result:
            ipv4_addr = result[0][4][0]
            print(f"✓ Resolved {parsed.hostname} to IPv4: {ipv4_addr}")
    except Exception as e:
        print(f"⚠ IPv4 resolution failed: {e}")
        # Fall back to using hostname directly
        ipv4_addr = parsed.hostname
    
    # Build connection string with resolved IP or hostname
    conn_string = f"postgresql://{parsed.username}:{parsed.password}@{ipv4_addr}:{parsed.port or 5432}{parsed.path}?sslmode=require&connect_timeout=15"
    
    try:
        db_pool = pool.SimpleConnectionPool(
            1,  # minconn
            10,  # maxconn
            conn_string
        )
        print(f"✓ Database pool initialized successfully")
        return db_pool
    except Exception as e:
        print(f"✗ Database pool initialization failed: {e}")
        raise

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
                claimed_by_username VARCHAR(255),
                claimed_by_name VARCHAR(255),
                claimed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add new columns if they don't exist (for existing databases)
        cur.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'credentials' AND column_name = 'claimed_by_username'
                ) THEN
                    ALTER TABLE credentials ADD COLUMN claimed_by_username VARCHAR(255);
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'credentials' AND column_name = 'claimed_by_name'
                ) THEN
                    ALTER TABLE credentials ADD COLUMN claimed_by_name VARCHAR(255);
                END IF;
            END $$;
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
                full_name VARCHAR(255),
                redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add full_name column if it doesn't exist (for existing databases)
        cur.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'key_redemptions' AND column_name = 'full_name'
                ) THEN
                    ALTER TABLE key_redemptions ADD COLUMN full_name VARCHAR(255);
                END IF;
            END $$;
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
