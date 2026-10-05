import asyncio
import os
from aiohttp import web
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN", "8961568897:AAHcme1vernf8Qm3k3CY2rWK54RqjbX3GKU")
ADMIN_ID = 8960600776

# Admin ko'rgan xabar ID -> foydalanuvchi ID
message_users = {}


# ---------- RENDER UCHUN VEB-SERVER ----------
async def start_web_server():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Support Bot is running!"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


# ---------- HANDLERLAR ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name

    text = f"""Здравствуйте! {name}

Напишите Ваш вопрос, и мы ответим Вам в ближайшее время."""

    await update.message.reply_text(text)


async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    username = f"@{user.username}" if user.username else "Username yo'q"

    # Admin uchun foydalanuvchi haqida ma'lumot
    info = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"👤 {username}\n🆔 ID: {user.id}\n\n📩 Xabar:"
    )

    # Foydalanuvchining xabarini admin'ga yuborish
    copied = await message.copy(
        chat_id=ADMIN_ID,
        reply_to_message_id=info.message_id
    )

    # Admin ko'rgan xabar ID'sini user ID bilan bog'lash
    message_users[copied.message_id] = user.id


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if message.from_user.id != ADMIN_ID:
        return

    # Admin Reply qilgan bo'lishi kerak
    if not message.reply_to_message:
        return

    replied_message_id = message.reply_to_message.message_id

    # Qaysi foydalanuvchiga yuborishni aniqlaymiz
    user_id = message_users.get(replied_message_id)

    if not user_id:
        await message.reply_text(
            "❌ Bu xabarga tegishli foydalanuvchi topilmadi."
        )
        return

    # Admin javobini foydalanuvchiga yuborish
    await message.copy(chat_id=user_id)


# ---------- ISHGA TUSHIRISH ----------
async def main():
    # Render portini ushlab turuvchi veb-serverni ishga tushiramiz
    await start_web_server()

    # PTB ilovasini yaratamiz
    app = Application.builder().token(TOKEN).build()

    # /start
    app.add_handler(CommandHandler("start", start))

    # Admin javoblari
    app.add_handler(
        MessageHandler(
            filters.ALL & filters.User(ADMIN_ID),
            admin_reply
        )
    )

    # Foydalanuvchi xabarlari
    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.User(ADMIN_ID),
            user_message
        )
    )

    print("🤖 Support bot ishga tushdi...")

    # Botni va pollingni ishga tushiramiz
    async with app:
        await app.start()
        await app.updater.start_polling()
        # Bot uzluksiz ishlashi uchun kuting
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
