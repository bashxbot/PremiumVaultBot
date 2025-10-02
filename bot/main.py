#!/usr/bin/env python
"""
Premium Vault Bot - Telegram Giveaway Bot
A bot for managing premium account giveaways with key generation and redemption.
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Import admin and user modules
from admin import (
    admin_start,
    handle_admin_callback,
    handle_admin_message,
    is_admin,
    ensure_data_files
)
from users import (
    user_start,
    handle_user_callback,
    handle_user_message,
    redeem_command
)

# Bot token - load from environment variable or use the provided token
import os
BOT_TOKEN = os.getenv('BOT_TOKEN', '8039142646:AAFpnOAX197pxqMqWjw99o-o25oD0SA1BC8')

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # Import ADMIN_IDS to modify it
    from admin import ADMIN_IDS
    
    # Auto-admin: If no admins exist, make @beastsec admin, or first user becomes admin
    if len(ADMIN_IDS) == 0:
        if username == "beastsec" or True:  # First user or @beastsec becomes admin
            ADMIN_IDS.append(user_id)
            logger.info(f"🔐 New admin added: {username} (ID: {user_id})")
    
    # Also check if username is @beastsec and add as admin if not already
    if username == "beastsec" and user_id not in ADMIN_IDS:
        ADMIN_IDS.append(user_id)
        logger.info(f"🔐 @beastsec added as admin (ID: {user_id})")
    
    # Route to admin or user start
    if is_admin(user_id):
        await admin_start(update, context)
    else:
        await user_start(update, context)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Route to admin or user callback handler
    if query.data.startswith("admin_"):
        await handle_admin_callback(update, context)
    elif query.data.startswith("user_"):
        await handle_user_callback(update, context)
    else:
        await query.answer("❌ Unknown action!")


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all text messages"""
    user_id = update.effective_user.id
    
    # Route to admin or user message handler
    if is_admin(user_id):
        await handle_admin_message(update, context)
    else:
        await handle_user_message(update, context)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Exception while handling an update: {context.error}")


def main() -> None:
    """Start the bot"""
    # Ensure data files exist
    ensure_data_files()
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("redeem", redeem_command))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Add message handler for text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("🎮 Premium Vault Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
