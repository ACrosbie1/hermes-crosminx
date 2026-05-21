import os
import asyncio
import anthropic
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

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
    await update.message.reply_text(
        "⚡ Hermes CrosMinX online.\n\n"
        "Deal research. ARF checks. Velocity qualification. Property intel.\n\n"
        "Drop a deal, address, or business — I'll run it."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    await update.message.chat.send_action("typing")
    
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}]
        )
        reply = response.content[0].text
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Hermes CrosMinX Bot starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
