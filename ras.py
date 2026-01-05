import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from telethon import TelegramClient

BOT_TOKEN = os.getenv("8387590624:AAGQ1tcpNxWzzwTGyfroiruIwedD5RDq-ng")

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

client = None
api_id = None
api_hash = None
session_name = "user_session"

TEXT = ""
CHATS = []
DELAY = 30

# ===== FSM =====
class Form(StatesGroup):
    api_id = State()
    api_hash = State()
    phone = State()
    code = State()
    text = State()
    chats = State()

menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Добавить аккаунт", callback_data="add_acc")],
    [InlineKeyboardButton(text="📝 Текст", callback_data="text")],
    [InlineKeyboardButton(text="📋 Чаты", callback_data="chats")],
    [InlineKeyboardButton(text="▶️ Запуск", callback_data="start")]
])

@dp.message(commands=["start"])
async def start(msg: types.Message):
    await msg.answer("Панель управления рассылкой", reply_markup=menu)

# ===== АККАУНТ =====
@dp.callback_query(lambda c: c.data == "add_acc")
async def add_acc(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.answer("Введи API ID")
    await state.set_state(Form.api_id)

@dp.message(Form.api_id)
async def get_api_id(msg: types.Message, state: FSMContext):
    await state.update_data(api_id=int(msg.text))
    await msg.answer("Введи API HASH")
    await state.set_state(Form.api_hash)

@dp.message(Form.api_hash)
async def get_api_hash(msg: types.Message, state: FSMContext):
    await state.update_data(api_hash=msg.text)
    await msg.answer("Введи номер телефона (+7999...)")
    await state.set_state(Form.phone)

@dp.message(Form.phone)
async def get_phone(msg: types.Message, state: FSMContext):
    global client
    data = await state.get_data()

    client = TelegramClient(session_name, data["api_id"], data["api_hash"])
    await client.connect()
    await client.send_code_request(msg.text)

    await state.update_data(phone=msg.text)
    await msg.answer("Введи код из Telegram")
    await state.set_state(Form.code)

@dp.message(Form.code)
async def get_code(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    await client.sign_in(data["phone"], msg.text)

    await msg.answer("✅ Аккаунт добавлен", reply_markup=menu)
    await state.clear()

# ===== ТЕКСТ =====
@dp.callback_query(lambda c: c.data == "text")
async def set_text(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.answer("Отправь текст рассылки")
    await state.set_state(Form.text)

@dp.message(Form.text)
async def save_text(msg: types.Message, state: FSMContext):
    global TEXT
    TEXT = msg.text
    await msg.answer("✅ Текст сохранён", reply_markup=menu)
    await state.clear()

# ===== ЧАТЫ =====
@dp.callback_query(lambda c: c.data == "chats")
async def set_chats(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.answer(
        "Отправь чаты через запятую\n"
        "Пример:\n-1001234567890, https://t.me/chat"
    )
    await state.set_state(Form.chats)

@dp.message(Form.chats)
async def save_chats(msg: types.Message, state: FSMContext):
    global CHATS
    CHATS = [c.strip() for c in msg.text.split(",")]
    await msg.answer("✅ Чаты сохранены", reply_markup=menu)
    await state.clear()

# ===== РАССЫЛКА =====
@dp.callback_query(lambda c: c.data == "start")
async def start_broadcast(cb: types.CallbackQuery):
    await cb.message.answer("🚀 Рассылка запущена")
    asyncio.create_task(broadcast())

async def broadcast():
    for chat in CHATS:
        try:
            await client.send_message(chat, TEXT)
            await asyncio.sleep(DELAY)
        except Exception as e:
            print("Ошибка:", e)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
