# Premium Vault Bot - Project Documentation

## Overview
Telegram bot and web admin panel for managing premium account credentials (Netflix, Crunchyroll, WWE, DisneyPlus, etc.) with key redemption functionality.

## Recent Changes (October 2025)

### ✅ Complete Migration to Supabase PostgreSQL (Completed)
- **Date:** October 6-7, 2025
- **Status:** COMPLETED
- All data storage migrated from JSON files to Supabase PostgreSQL database (wbzdmowaxtepyprqhbws.supabase.co)
- Both bot and web admin panel now use unified Supabase database
- Complete elimination of JSON file storage

### Latest Updates (October 7, 2025)
- **✅ Fixed case-sensitivity bug** preventing key generation for platforms like Crunchyroll
- **✅ Created database views** (keys_with_platform, credentials_with_platform) for better Supabase UI
- **✅ Enhanced API responses** to include complete claimer/redeemer information
- **✅ Verified admin notification system** working correctly for all key redemptions and credential claims

### Database Implementation
- **Schema Created:** platforms, credentials, keys, key_redemptions, users, banned_users, giveaways, giveaway_participants, admin_credentials
- **User Tracking:** Full user details (user_id, username, full_name) tracked for all redemptions and claims
- **Admin Notifications:** Real-time Telegram notifications sent to all admins when keys are redeemed or credentials claimed
- **Views:** Database views for easier platform differentiation in Supabase UI

### Migration Completed
1. ✅ Database schema with tracking fields (username, full_name)
2. ✅ Admin credentials migrated from admin_credentials.json
3. ✅ Platform credentials migrated from credentials/*.json files
4. ✅ API server completely refactored to use Supabase PostgreSQL
5. ✅ Bot updated to save full user details and send admin notifications
6. ✅ API endpoints return complete redemption/claim history with user details
7. ✅ All JSON data files removed
8. ✅ Case-insensitive platform lookup implemented

### Key Features
- **Unified Supabase Database:** Single PostgreSQL database for bot and web panel
- **User Tracking:** Complete details (name, chat_id, username) for all redemptions/claims
- **Real-time Notifications:** Instant Telegram alerts to all admins with formatted user details
- **History Tracking:** Full redemption and claim history with user details in API responses
- **Case-Insensitive:** Platform lookups work regardless of case

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

## Important Notes

### Bot Credential Distribution
- **Bot only distributes credentials with 'active' status**
- New credentials added via admin panel default to 'active' status
- When a credential is claimed, status changes to 'claimed' and can't be distributed again
- To test: Add new credentials through admin panel with 'active' status

### Admin Notifications (WORKING)
- Admins receive Telegram notifications when:
  - Users redeem keys (includes platform, key code, user details)
  - Users claim credentials (includes platform, email, user details)
- Messages are formatted with HTML and include user_id, username, full_name, timestamp
- Notifications sent to all admins from the admin_credentials table

### API Response Enhancement
- `/api/credentials/<platform>` includes: claimed_by, claimed_by_username, claimed_by_name, claimed_at
- `/api/keys/<platform>` includes: redeemed_by array with user_id, username, full_name, redeemed_at
- All timestamps in ISO format

## System Status
✅ **FULLY OPERATIONAL**
- Supabase PostgreSQL database connected
- Bot running with admin notifications
- Web admin panel operational on port 5000
- Complete user tracking for all actions
