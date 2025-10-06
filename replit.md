# Premium Vault Bot - Project Documentation

## Overview
Telegram bot and web admin panel for managing premium account credentials (Netflix, Crunchyroll, WWE, DisneyPlus, etc.) with key redemption functionality.

## Recent Changes (October 2025)

### ✅ Complete Migration to PostgreSQL (Completed)
- **Date:** October 6, 2025
- **Status:** COMPLETED
- All data storage migrated from JSON files to PostgreSQL database
- Both bot and web admin panel now use unified database
- Complete elimination of JSON file storage

### Database Implementation
- **Schema Created:** platforms, credentials, keys, key_redemptions, users, banned_users, giveaways, giveaway_participants, admin_credentials
- **User Tracking:** Full user details (user_id, username, full_name) tracked for all redemptions and claims
- **Admin Notifications:** Real-time Telegram notifications sent to all admins when keys are redeemed or credentials claimed

### Migration Completed
1. ✅ Database schema with tracking fields (username, full_name)
2. ✅ Admin credentials migrated from admin_credentials.json
3. ✅ Platform credentials migrated from credentials/*.json files (12 credentials)
4. ✅ API server completely refactored (~500 lines) to use PostgreSQL
5. ✅ Bot updated to save full user details and send admin notifications
6. ✅ API endpoints added for redemption/claim history
7. ✅ All JSON data files removed

### Key Features
- **Unified Database:** Single PostgreSQL database for bot and web panel
- **User Tracking:** Complete details (name, chat_id, username) for all redemptions/claims
- **Real-time Notifications:** Instant Telegram alerts to all admins
- **History Tracking:** Full redemption and claim history with user details

## Project Architecture

### Tech Stack
- **Backend:** Python Flask API server
- **Bot:** Python Telegram Bot (python-telegram-bot)
- **Database:** PostgreSQL (Neon-backed Replit database)
- **Frontend:** React-based admin panel

### Core Components
1. **api_server.py** - Flask API for admin panel (uses PostgreSQL)
2. **bot/** - Telegram bot implementation
   - admin.py - Admin commands and management
   - users.py - User commands and key redemption
3. **db_setup.py** - Database initialization and schema
4. **db_helpers.py** - Database operations and admin notifications
5. **admin-panel/** - React web interface

### Database Schema
- **platforms** - Supported platforms (Netflix, Crunchyroll, etc.)
- **credentials** - Account credentials with claim tracking
- **keys** - Redemption keys
- **key_redemptions** - Redemption history with full user details
- **users** - User registration and stats
- **banned_users** - Banned user management
- **giveaways** - Giveaway management
- **giveaway_participants** - Giveaway entries
- **admin_credentials** - Admin accounts with bcrypt passwords

## User Preferences
- Clear, concise communication
- Focus on functionality over documentation
- Progressive implementation with testing

## Environment Variables
- `BOT_TOKEN` - Telegram Bot API token
- `DATABASE_URL` - PostgreSQL connection string (auto-configured)
- Flask secret key configured in api_server.py

## Development Workflow
1. Database initialized via db_setup.py on first run
2. Admin panel runs on port 5000
3. Bot and API server run together via start.py

## Next Steps
- Add UI components to view redemption/claim history in web admin panel
- Add bot admin commands to view history
- Comprehensive testing of complete system
