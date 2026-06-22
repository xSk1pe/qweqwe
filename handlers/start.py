from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext  # ← ДОБАВЛЯЕМ ЭТОТ ИМПОРТ
from utils.helpers import init_user_progress, get_progress_text, get_statistics, get_achievements, get_rating, get_daily_tip, get_random_test
from states.learning import Learning  # ← ДОБАВЛЯЕМ ИМПОРТ СОСТОЯНИЙ
import random

router = Router()

# ========== РАСШИРЕННАЯ ГЛАВНАЯ КЛАВИАТУРА ==========
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Уроки"), KeyboardButton(text="📊 Прогресс")],
        [KeyboardButton(text="🏆 Достижения"), KeyboardButton(text="⭐ Рейтинг")],
        [KeyboardButton(text="🎓 Совет дня"), KeyboardButton(text="📝 Случайный тест")],
        [KeyboardButton(text="ℹ️ О боте"), KeyboardButton(text="❓ Помощь")]
    ],
    resize_keyboard=True
)

# ========== КЛАВИАТУРА ДЛЯ ВОЗВРАТА В ГЛАВНОЕ МЕНЮ ==========
back_to_menu_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🏠 Главное меню")]],
    resize_keyboard=True
)

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    init_user_progress(user_id)
    
    welcome_text = (
        "✨ *Привет! Я BraidMaster — твой гид в мире афрокос!*\n\n"
        "📚 *Что я умею:*\n"
        "• 8 пошаговых уроков с видео\n"
        "• Профессиональные советы\n"
        "• Тесты для проверки знаний\n"
        "• Отслеживание прогресса\n"
        "• Достижения и рейтинг\n"
        "• Совет дня от профессионалов\n\n"
        "👇 *Выбери действие в меню ниже*"
    )
    
    await message.answer(welcome_text, reply_markup=main_kb, parse_mode="Markdown")

@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    help_text = (
        "📖 *Как пользоваться ботом:*\n\n"
        "┌─────────────────────────┐\n"
        "│ 📚 *Уроки*              │\n"
        "│   → 8 техник плетения   │\n"
        "│   → Пошаговые инструкции│\n"
        "│   → Видеоуроки с YouTube│\n"
        "├─────────────────────────┤\n"
        "│ 📊 *Прогресс*           │\n"
        "│   → Пройденные уроки    │\n"
        "│   → Статистика          │\n"
        "├─────────────────────────┤\n"
        "│ 🏆 *Достижения*         │\n"
        "│   → Награды за прогресс │\n"
        "│   → Звания мастера      │\n"
        "├─────────────────────────┤\n"
        "│ ⭐ *Рейтинг*            │\n"
        "│   → Сравнение с другими │\n"
        "│   → Место в топе        │\n"
        "├─────────────────────────┤\n"
        "│ 🎓 *Совет дня*          │\n"
        "│   → Полезные советы     │\n"
        "│   → Лайфхаки от мастеров│\n"
        "├─────────────────────────┤\n"
        "│ 📝 *Случайный тест*     │\n"
        "│   → Проверка знаний     │\n"
        "│   → Повторение материала│\n"
        "└─────────────────────────┘\n\n"
        "*Команды:*\n"
        "/start — перезапустить бота\n"
        "/progress — твой прогресс\n"
        "/cancel — отменить урок\n\n"
        "🛑 *В любой момент можно вернуться в меню*\n"
        "   кнопкой «🏠 Главное меню»"
    )
    await message.answer(help_text, reply_markup=main_kb, parse_mode="Markdown")

@router.message(F.text == "ℹ️ О боте")
async def about_bot(message: Message):
    about_text = (
        "🤖 *О BraidMaster*\n\n"
        "Версия: 2.0.0\n"
        "Автор: Мастер по плетению\n\n"
        "📚 *Доступные техники:* 8\n"
        "🎥 *Видеоуроков:* 33+\n"
        "📝 *Тестов:* 30+\n"
        "🏆 *Достижений:* 7\n\n"
        "💡 *Идея:* Помочь каждому\n"
        "научиться плести афрокосы\n"
        "профессионально и красиво.\n\n"
        "📢 *В планах:*\n"
        "• Новые техники\n"
        "• Видео высокого качества\n"
        "• Живые мастер-классы\n\n"
        "❤️ *Спасибо, что учитесь с нами!*"
    )
    await message.answer(about_text, reply_markup=main_kb, parse_mode="Markdown")

@router.message(F.text == "📊 Прогресс")
async def show_progress(message: Message):
    user_id = message.from_user.id
    text = get_progress_text(user_id)
    await message.answer(text, reply_markup=main_kb, parse_mode="Markdown")

@router.message(F.text == "🏆 Достижения")
async def show_achievements(message: Message):
    user_id = message.from_user.id
    achievements_text = get_achievements(user_id)
    await message.answer(achievements_text, reply_markup=main_kb, parse_mode="Markdown")

@router.message(F.text == "⭐ Рейтинг")
async def show_rating(message: Message):
    user_id = message.from_user.id
    rating_text = get_rating(user_id)
    await message.answer(rating_text, reply_markup=main_kb, parse_mode="Markdown")

@router.message(F.text == "🎓 Совет дня")
async def daily_tip(message: Message):
    tip_text = get_daily_tip()
    # Добавляем красивое оформление
    full_tip = f"🎓 *Совет дня*\n━━━━━━━━━━━━━━━\n\n{tip_text}\n\n━━━━━━━━━━━━━━━\n📌 *Новый совет каждый день!*"
    await message.answer(full_tip, reply_markup=main_kb, parse_mode="Markdown")

@router.message(F.text == "📝 Случайный тест")
async def random_test(message: Message, state: FSMContext):
    from handlers.lessons import send_next_question
    
    random_test_data = get_random_test()
    
    if random_test_data:
        # Сохраняем тест в состояние
        await state.update_data(
            tests=[random_test_data],
            current_test_index=0,
            correct_answers=0,
            user_answers={},
            lesson_title="Случайный тест"
        )
        
        await message.answer(
            "🎲 *Случайный тест*\n━━━━━━━━━━━━━━━\n\n"
            "Я выбрал для тебя случайный вопрос.\n"
            "Проверь свои знания!\n\n"
            "👇 *Отвечай на вопрос:*",
            parse_mode="Markdown"
        )
        
        # Отправляем первый вопрос
        await send_next_question(message, state)
        await state.set_state(Learning.test)
    else:
        await message.answer(
            "❌ *Не удалось загрузить тест*\n\n"
            "Попробуй позже или начни урок из меню «📚 Уроки».",
            parse_mode="Markdown"
        )

@router.message(F.text == "🏠 Главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 *Главное меню*\n\n"
        "Выбери действие:",
        reply_markup=main_kb,
        parse_mode="Markdown"
    )

@router.message(Command("progress"))
async def progress_command(message: Message):
    await show_progress(message)

@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "⏹️ *Действие отменено*\n\n"
        "Ты вернулся в главное меню.",
        reply_markup=main_kb,
        parse_mode="Markdown"
    )