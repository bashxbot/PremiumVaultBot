
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
    
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is required")
    
    async def start_command(update: Update, context):
        if not update.effective_user:
            return
        user_id = update.effective_user.id
        if is_admin(user_id):
            await admin_start(update, context)
        else:
            await user_start(update, context)
    
    async def handle_callback_query(update: Update, context):
        query = update.callback_query
        if not query or not query.data:
            return
        if query.data.startswith("admin_"):
            await handle_admin_callback(update, context)
        elif query.data.startswith("user_"):
            await handle_user_callback(update, context)
        else:
            await query.answer("❌ Unknown action!")
    
    async def handle_text_message(update: Update, context):
        if not update.effective_user:
            return
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
    """Run the Flask admin panel with Gunicorn"""
    import subprocess
    import sys
    
    port = os.getenv('PORT', '10000')
    logger.info(f"🌐 Admin Panel starting on port {port} with Gunicorn...")
    
    # Run Gunicorn as a subprocess
    subprocess.Popen([
        sys.executable, '-m', 'gunicorn',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '2',
        '--threads', '2',
        '--timeout', '120',
        '--access-logfile', '-',
        '--error-logfile', '-',
        'api_server:app'
    ])

if __name__ == "__main__":
    logger.info("🚀 Starting Premium Vault - Bot & Admin Panel")
    
    # Initialize database
    try:
        from db_setup import init_database
        logger.info("📊 Initializing PostgreSQL database...")
        init_database()
        logger.info("✅ Database initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.info("⚠️ Continuing without database - please check DATABASE_URL")
    
    # Start Flask with Gunicorn in background
    run_flask()
    logger.info("✅ Gunicorn Flask server started")
    
    # Small delay to let Gunicorn start
    import time
    time.sleep(2)
    
    # Run bot in main thread (blocking)
    run_bot()
