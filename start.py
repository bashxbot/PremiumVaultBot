
#!/usr/bin/env python
"""
Unified start script for Premium Vault Bot and Admin Panel
Runs both the Telegram bot and Flask web server together
"""

import threading
import logging
import os

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def run_bot():
    """Run the Telegram bot"""
    import sys
    import os
    
    # Add bot directory to Python path
    bot_dir = os.path.join(os.path.dirname(__file__), 'bot')
    if bot_dir not in sys.path:
        sys.path.insert(0, bot_dir)
    
    from telegram import Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
    
    # Import bot modules
    from admin import (admin_start, handle_admin_callback, handle_admin_message,
                      is_admin, ensure_data_files, check_and_process_giveaways)
    from users import (user_start, handle_user_callback, handle_user_message,
                      redeem_command, participate_command)
    
    BOT_TOKEN = os.getenv('BOT_TOKEN', '7941709895:AAH4jPLL6FRxEqo3v0Ai4lKa6huWu1trpYU')
    
    async def start_command(update: Update, context):
        user_id = update.effective_user.id
        if is_admin(user_id):
            await admin_start(update, context)
        else:
            await user_start(update, context)
    
    async def handle_callback_query(update: Update, context):
        query = update.callback_query
        if query.data.startswith("admin_"):
            await handle_admin_callback(update, context)
        elif query.data.startswith("user_"):
            await handle_user_callback(update, context)
        else:
            await query.answer("❌ Unknown action!")
    
    async def handle_text_message(update: Update, context):
        user_id = update.effective_user.id
        if is_admin(user_id):
            await handle_admin_message(update, context)
        else:
            await handle_user_message(update, context)
    
    async def error_handler(update: object, context):
        logger.error(f"Exception while handling an update: {context.error}")
    
    # Ensure data files exist
    ensure_data_files()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("redeem", redeem_command))
    application.add_handler(CommandHandler("participate", participate_command))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_error_handler(error_handler)
    
    # Add background job for giveaway checking
    job_queue = application.job_queue
    job_queue.run_repeating(check_and_process_giveaways, interval=30, first=10)
    logger.info("✅ Giveaway checker job scheduled (runs every 30 seconds)")
    
    # Start bot
    logger.info("🎮 Premium Vault Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

def run_flask():
    """Run the Flask admin panel"""
    from api_server import app, ensure_credentials_dir
    
    ensure_credentials_dir()
    logger.info("🌐 Admin Panel starting on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    logger.info("🚀 Starting Premium Vault - Bot & Admin Panel")
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("✅ Flask admin panel thread started")
    
    # Run bot in main thread (blocking)
    run_bot()
