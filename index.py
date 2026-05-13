import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from openai import AsyncOpenAI

# Завантаження змінних середовища
load_dotenv()

# Підключення до OpenRouter через OpenAI SDK
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Ініціалізація Telegram-бота
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

# Аналіз коду через два послідовні запити
async def run_multi_agent_review(user_code):

    # Модель для обробки запитів
    model_name = "openai/gpt-4o-mini"

    async def get_ai_response(prompt):
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                extra_headers={
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "CodeReviewer AI Project",
                }
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI Error: {e}")
            return f"❌ Помилка запиту до ШІ: {str(e)}"

    # Перевірка коду на помилки
    prompt1 = (
        f"Перевір цей код на критичні помилки та потенційні вразливості:\n{user_code}"
    )
    bugs_report = await get_ai_response(prompt1)

    if "❌" in bugs_report:
        return bugs_report

    # Формування виправленого варіанту
    prompt2 = f"""
    Код користувача:
    {user_code}

    Знайдені проблеми:
    {bugs_report}

    Завдання:
    1. Покажи покращений варіант коду.
    2. Коротко поясни внесені зміни українською.
    3. Використовуй Markdown для форматування.
    """

    return await get_ai_response(prompt2)

# Клавіатура бота
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Аналізувати код"), KeyboardButton(text="💡 Приклад")],
        [KeyboardButton(text="📜 Про методику")]
    ],
    resize_keyboard=True
)

# Команда старту
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        f"Привіт, {message.from_user.first_name}! Я Code Reviewer Bot 🤖",
        reply_markup=main_kb
    )

# Приклад для тесту
@dp.message(F.text == "💡 Приклад")
async def example_handler(message: types.Message):
    await message.answer(
        "Надішли: `function test() { var x = 10 / 0; }`",
        parse_mode="Markdown"
    )

# Інформація про принцип роботи
@dp.message(F.text == "📜 Про методику")
async def method_handler(message: types.Message):
    await message.answer(
        "Бот виконує перевірку коду та пропонує покращений варіант."
    )

# Обробка повідомлень користувача
@dp.message()
async def handle_code(message: types.Message):

    if not message.text or message.text.startswith('/'):
        return

    status = await message.answer("⏳ Аналіз коду...")

    try:
        result = await run_multi_agent_review(message.text)

        await status.delete()

        await message.answer(result, parse_mode="Markdown")

    except Exception as e:
        await status.edit_text(f"❌ Помилка: {e}")

# Запуск бота
async def main():
    print("✅ Бот запущено")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
