import os
import asyncio
import logging
import anthropic
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("hermes")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Per-user conversation history (in-memory, resets on restart)
conversation_histories = {}
MAX_HISTORY = 20  # Max messages per user before trimming

SYSTEM_PROMPT = """You are Hermes, an elite AI research and deal intelligence agent for CrosMinX Empire, owned by Sir Anthony Crosbie based in Pottstown, PA.

Your specialties:
- Real estate deal research and analysis (Croshire Estates Corp)
- ARF Financial industry eligibility checks ($5K-$1.5M business loans)
- Velocity Mortgage deal qualification (FlexTerm, ARV Pro, Flex I/O, Fast50)
- Lead intelligence and business research
- Property comps, zoning, market analysis
- Business loan pre-qualification

Lender minimums to know:
- ARF: 575+ Equifax, 1+ month in business, $17K/month revenue
- Velocity: 650+ FICO, various LTV requirements per product

Be concise, sharp, and action-oriented. You are an expert broker's assistant."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    conversation_histories[user_id] = []  # Reset history on /start
    await update.message.reply_text(
        "⚡ Hermes CrosMinX online.\n\n"
        "Deal research. ARF checks. Velocity qualification. Property intel.\n\n"
        "Drop a deal, address, or business — I'll run it."
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    conversation_histories[user_id] = []
    await update.message.reply_text("🔄 Conversation cleared. Fresh start.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_msg = update.message.text
    await update.message.chat.send_action("typing")

    # Initialize history for new users
    if user_id not in conversation_histories:
        conversation_histories[user_id] = []

    # Add user message to history
    conversation_histories[user_id].append({
        "role": "user",
        "content": user_msg
    })

    # Trim history if too long (keep last MAX_HISTORY messages)
    if len(conversation_histories[user_id]) > MAX_HISTORY:
        conversation_histories[user_id] = conversation_histories[user_id][-MAX_HISTORY:]

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            # Prompt caching on system prompt — saves tokens every request
            system=[{
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"}
            }],
            messages=conversation_histories[user_id]
        )

        reply = response.content[0].text

        # Add assistant response to history
        conversation_histories[user_id].append({
            "role": "assistant",
            "content": reply
        })

        # Log cache performance
        usage = response.usage
        if hasattr(usage, 'cache_read_input_tokens'):
            print(f"Cache read: {usage.cache_read_input_tokens} | Cache write: {usage.cache_creation_input_tokens} | Input: {usage.input_tokens}")

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Catch-all so a transient network error never kills the whole app.
    Without this, PTB logs 'No error handlers are registered' and the
    process can go silent for good (this was the root cause of the crashes)."""
    logger.warning(f"Handled error, staying alive: {context.error}")

def build_app():
    # Longer timeouts + PTB's own get_updates retry loop, tuned to survive
    # flaky egress instead of raising all the way up to the process.
    request = HTTPXRequest(
        connect_timeout=15.0,
        read_timeout=30.0,
        write_timeout=15.0,
        pool_timeout=15.0,
    )
    app = Application.builder().token(TELEGRAM_TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    return app

def main():
    """Supervisor loop: if polling ever dies anyway (e.g. DNS blip that
    outlives PTB's internal retry), rebuild the Application and restart
    instead of leaving the container silent until someone restarts it by hand."""
    backoff = 5
    while True:
        try:
            app = build_app()
            logger.info("Hermes CrosMinX Bot starting with prompt caching + conversation memory...")
            app.run_polling(drop_pending_updates=True)
            # run_polling returned cleanly (e.g. graceful shutdown) — stop.
            break
        except Exception as e:
            logger.error(f"Polling crashed: {e}. Restarting in {backoff}s...")
            import time
            time.sleep(backoff)
            backoff = min(backoff * 2, 120)  # exponential backoff, capped at 2min

if __name__ == "__main__":
    main()
