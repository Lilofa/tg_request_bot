import asyncio
import sqlite3
import ssl
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.session.aiohttp import AiohttpSession

BOT_TOKEN = "8211657897:AAF5wOqRwrU0Pwbhj95OjMWgWEZ5JPccNzk"
ADMIN_ID = 7792664457
PROXY = "socks5://72.194.42.156:4145"

conn = sqlite3.connect("requests.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        name TEXT,
        message TEXT,
        created_at TEXT
    )
""")
conn.commit()


def register_handlers(dp: Dispatcher):
    @dp.message(Command("start"))
    async def start(message: types.Message):
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Оставить заявку")]],
            resize_keyboard=True
        )
        await message.answer(
            "Привет! Я бот для приёма заявок.\n"
            "Нажми «Оставить заявку» или просто напиши сообщение.",
            reply_markup=kb
        )

    @dp.message(F.text == "Оставить заявку")
    async def ask_request(message: types.Message):
        await message.answer("Напиши свою заявку одним сообщением:")

    @dp.message(Command("admin"))
    async def admin_panel(message: types.Message):
        if message.from_user.id != ADMIN_ID:
            await message.answer("Нет доступа.")
            return
        cursor.execute("SELECT COUNT(*) FROM requests")
        total = cursor.fetchone()[0]
        cursor.execute(
            "SELECT id, name, message, created_at FROM requests ORDER BY id DESC LIMIT 5"
        )
        rows = cursor.fetchall()
        text = f"Всего заявок: {total}\n\nПоследние 5:\n\n"
        for r in rows:
            text += f"#{r[0]} | {r[1]} | {r[3]}\n{r[2]}\n\n"
        await message.answer(text)

    @dp.message()
    async def handle_request(message: types.Message):
        user_id = message.from_user.id
        username = message.from_user.username or "нет"
        name = message.from_user.full_name
        text = message.text
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        cursor.execute(
            "INSERT INTO requests (user_id, username, name, message, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, username, name, text, now)
        )
        conn.commit()

        await message.answer("Заявка принята! Свяжемся с тобой.")
        try:
            await message.bot.send_message(
                ADMIN_ID,
                f"Новая заявка\n\n"
                f"От: {name} (@{username})\n"
                f"Время: {now}\n\n"
                f"{text}"
            )
        except Exception as e:
            print(f"Не удалось уведомить админа: {e}")


async def main():
    session = AiohttpSession(proxy=PROXY)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    session._connector_init["ssl"] = ssl_context

    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher()
    register_handlers(dp)

    print("Бот запущен. Нажми Ctrl+C для остановки.")
    try:
        await dp.start_polling(bot)
    finally:
        await session.close()

asyncio.run(main())