# Premium Vault Bot

## Overview

Premium Vault Bot is a Telegram bot designed for managing premium account giveaways. The bot allows administrators to generate redemption keys for various streaming and entertainment platforms (Netflix, Crunchyroll, Spotify, WWE), manage giveaways, and distribute premium account credentials to users. Regular users can redeem keys to receive premium account credentials after joining required Telegram channels.

The bot features a dual-interface design: an administrative panel for key generation, statistics, user management, and giveaway control, plus a user-facing interface for key redemption with mandatory channel membership verification.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Technology**: Python Telegram Bot (PTB) library v20+
- **Pattern**: Command and callback-based handlers for user interactions
- **Rationale**: PTB provides a robust, well-documented framework for Telegram bot development with built-in support for async operations and inline keyboards

### Authentication & Authorization
- **Admin System**: Environment variable-based admin configuration (ADMIN_IDS)
- **Auto-Admin Fallback**: First user to start the bot becomes admin if no ADMIN_IDS are configured
- **User Verification**: Channel membership verification against a hardcoded list of required channels
- **Ban System**: JSON-based banned users list for access control
- **Rationale**: Simple role-based system without database overhead, suitable for small-to-medium scale deployment

### Data Storage
- **Approach**: File-based JSON storage
- **Structure**:
  - `data/keys.json`: Generated redemption keys with metadata (platform, uses, expiration)
  - `data/users.json`: User registry with join dates and redemption history
  - `data/banned.json`: List of banned user IDs
  - `data/giveaway.json`: Active giveaway state and configuration
  - `credentials/{platform}.json`: Platform-specific account credentials
- **Rationale**: Lightweight solution avoiding database setup complexity; adequate for expected load
- **Pros**: Simple, portable, version-controllable, no external dependencies
- **Cons**: Not suitable for high-concurrency scenarios, lacks transactional safety

### Key Generation System
- **Format**: Platform-specific keys with random alphanumeric segments (e.g., NETFLIX-A2D8-FA2F-VV82)
- **Attributes**: Platform, usage limit, expiration date, account text
- **Credential Linking**: Keys are associated with credentials stored in platform-specific JSON files
- **Rationale**: Human-readable format that's easy to copy and share while maintaining uniqueness

### Module Architecture
- **Separation of Concerns**: Split into three main modules
  - `main.py`: Application entry point, routing, and initialization
  - `admin.py`: Administrative functionality (key generation, stats, broadcasts, user management)
  - `users.py`: User-facing features (channel verification, key redemption)
- **Rationale**: Modular design improves maintainability and allows independent development of admin and user features

### User Flow
- **Channel Verification First**: Users must join all required channels before accessing bot features
- **Interactive Callbacks**: Inline keyboard buttons for navigation and action confirmation
- **State Management**: Context-based conversation flow for multi-step operations (key generation, giveaways)
- **Rationale**: Ensures audience growth for associated channels while providing intuitive user experience

### Admin Features Architecture
- **Key Management**: Multi-step flow (platform selection → count → uses → account text → generation)
- **Statistics Dashboard**: Real-time aggregation from JSON files
- **Broadcast System**: Message distribution to all registered users
- **Giveaway System**: Time-based automated key distribution with winner selection
- **Revocation System**: Granular control over key lifecycle (individual, batch, or all keys)
- **Rationale**: Comprehensive admin toolkit covering typical giveaway management needs

## External Dependencies

### Telegram Bot API
- **Library**: `python-telegram-bot` (version 20+)
- **Purpose**: Core bot functionality, message handling, inline keyboards
- **Authentication**: Bot token from BotFather (configurable via BOT_TOKEN environment variable)
- **Integration Points**: All user interactions, callback queries, message handlers

### Python Standard Library
- **json**: Data persistence and credential management
- **os**: File system operations and environment variable access
- **datetime/timedelta**: Key expiration and giveaway timing
- **random/string**: Key generation randomization
- **logging**: Application monitoring and debugging

### Telegram Channels
- **Required Channels**: @PremiumVaultFigs, @accountvaultportal, @PremiumVaultBackup, @PremiumVault
- **Purpose**: User verification before bot access
- **Integration**: Channel membership checks via Telegram API

### Image Processing (Legacy)
- **Libraries**: PIL (Pillow), ImageDraw, ImageFont
- **Note**: Present in `main.py` from original template but not used in current giveaway bot implementation
- **Status**: Vestigial code from original "stylish text" bot template

### Environment Configuration
- **BOT_TOKEN**: Telegram bot authentication token
- **ADMIN_IDS**: Comma-separated list of Telegram user IDs with admin privileges
- **Fallback**: Hardcoded bot token exists but environment variable usage recommended for security

### Web Admin Panel
- **Technology**: React (Vite), Flask backend
- **Purpose**: Web-based interface for managing credentials and viewing keys
- **Features**:
  - Credentials management (add, edit, delete, bulk upload)
  - Keys viewing and statistics
  - Platform filtering (Netflix, Crunchyroll, Spotify, WWE)
  - Session-based authentication
- **UI/UX**:
  - Modern gradient design with smooth animations
  - Sidebar navigation with collapsible sections
  - Animated transitions: fadeIn, slideIn, bounce, pulse, shimmer effects
  - Responsive tables with hover states
  - Modal dialogs for forms with backdrop blur
  - Icon-based UI using react-icons (Material Design, Simple Icons, Game Icons)
- **Recent Updates (Oct 2025)**:
  - Fixed stats loading to handle unauthenticated states gracefully
  - Added comprehensive CSS animations for improved user experience
  - Enhanced buttons with gradient backgrounds and hover effects
  - Implemented staggered table row animations
  - Replaced all emojis with professional icon components
  - Optimized for performance using transform/opacity animations
  - **Oct 2**: Fixed bot account type response (reply_markup error)
  - **Oct 2**: Enhanced credential generation to prioritize active credentials and show status
  - **Oct 2**: Added platform logos to bot responses for keys and credentials
  - **Oct 2**: Implemented admin management system (owner can add/remove admins)
  - **Oct 2**: Added settings page for changing username and password
  - **Oct 2**: Unified data storage - bot and web panel now share same credential files
  - **Oct 2**: Fixed credential upload functionality in web admin panel