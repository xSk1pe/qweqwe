from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from states.learning import Learning
from lessons_data.content import LESSONS
from utils.helpers import mark_lesson_completed
import re

router = Router()

def get_lessons_keyboard():
    buttons = []
    for idx, (name, _) in enumerate(LESSONS.items()):
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"lesson_{idx}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_next_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Далее", callback_data="next_step")]
    ])

def is_vk_url(url: str) -> bool:
    patterns = [
        r'(https?://)?(www\.)?(vk\.com)/',
        r'(https?://)?(www\.)?(vkvideo\.ru)/',
        r'(https?://)?(www\.)?(vkontakte\.ru)/'
    ]
    return any(re.match(pattern, url) for pattern in patterns) if url else False

def get_continue_button():
    """Кнопка для перехода к видео после последнего шага"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Получить видеоурок", callback_data="show_video")],
        [InlineKeyboardButton(text="🛑 Отменить урок", callback_data="cancel_lesson")]
    ])

def get_video_and_test_button(video_url: str = None):
    """Кнопки после получения видео: переход к тесту и другие опции"""
    buttons = []
    if video_url:
        buttons.append([InlineKeyboardButton(text="🎬 Смотреть видео", url=video_url)])
    buttons.append([InlineKeyboardButton(text="📝 Перейти к тесту", callback_data="start_test")])
    buttons.append([InlineKeyboardButton(text="🔄 Пройти заново", callback_data="restart_lesson")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def send_step(message: Message, step_data: dict, step_num: int, total_steps: int, lesson_title: str):
    header = f"📚 *{lesson_title}*\n━━━━━━━━━━━━━━━\n*Шаг {step_num}/{total_steps}*\n\n"
    full_text = header + step_data["text"]
    await message.answer(full_text, parse_mode="Markdown")

@router.message(F.text == "📚 Уроки")
async def list_lessons(message: Message):
    await message.answer(
        "🌟 *Выбери технику плетения:*\n\n"
        "👇 *Нажми на кнопку ниже, чтобы выбрать урок*",
        reply_markup=get_lessons_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("lesson_"))
async def start_lesson(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    lesson_title = list(LESSONS.keys())[idx]
    lesson_data = LESSONS[lesson_title]
    
    steps = lesson_data["steps"]
    tests = lesson_data.get("tests", [])
    video_url = lesson_data.get("video_url", "")
    
    await state.update_data(
        lesson_title=lesson_title,
        steps=steps,
        current_step=0,  # текущий шаг (0 - первый)
        total_steps=len(steps),
        tests=tests,
        current_test_index=0,
        correct_answers=0,
        user_answers={},
        lesson_data=lesson_data,
        video_url=video_url
    )
    
    # Отправляем первый шаг сразу
    await send_step(
        callback.message,
        steps[0],
        1,
        len(steps),
        lesson_title
    )
    
    # Отправляем кнопку "Далее" для перехода ко второму шагу
    await callback.message.answer(
        "👇 *Нажми «Далее», чтобы продолжить*",
        reply_markup=get_next_button(),
        parse_mode="Markdown"
    )
    
    await state.set_state(Learning.waiting_for_next)
    await callback.answer()

@router.callback_query(Learning.waiting_for_next, F.data == "next_step")
async def next_step_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current = data.get("current_step", 0)  # текущий индекс шага (0,1,2...)
    steps = data["steps"]
    lesson_title = data["lesson_title"]
    total_steps = data["total_steps"]
    
    # Индекс следующего шага
    next_step_index = current + 1
    
    if next_step_index < total_steps:
        # Есть следующий шаг - отправляем его
        await send_step(
            callback.message,
            steps[next_step_index],
            next_step_index + 1,  # номер для отображения (1,2,3...)
            total_steps,
            lesson_title
        )
        
        # Обновляем текущий шаг
        await state.update_data(current_step=next_step_index)
        
        # Проверяем, не последний ли это шаг
        if next_step_index + 1 == total_steps:
            # Это предпоследний шаг, после него будет последний
            await callback.message.answer(
                "👇 *Нажми «Далее», чтобы перейти к последнему шагу*",
                reply_markup=get_next_button(),
                parse_mode="Markdown"
            )
        else:
            # Обычный шаг
            await callback.message.answer(
                "👇 *Нажми «Далее», чтобы продолжить*",
                reply_markup=get_next_button(),
                parse_mode="Markdown"
            )
        
    elif next_step_index == total_steps:
        # Это был последний шаг (current был total_steps-1)
        # Обновляем состояние, чтобы не зациклиться
        await state.update_data(current_step=next_step_index)
        
        # Отправляем сообщение о завершении всех шагов
        await callback.message.answer(
            "🎉 *Ты изучил все шаги урока!*\n\n"
            "Теперь можешь посмотреть видеоурок, затем перейти к тесту.",
            reply_markup=get_continue_button(),
            parse_mode="Markdown"
        )
    else:
        # Уже всё пройдено
        await callback.message.answer(
            "✅ Ты уже завершил все шаги этого урока.\n"
            "Нажми «Получить видеоурок», чтобы продолжить.",
            reply_markup=get_continue_button(),
            parse_mode="Markdown"
        )
    
    await callback.answer()

@router.callback_query(F.data == "show_video")
async def show_video_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    video_url = data.get("video_url", "")
    lesson_title = data.get("lesson_title", "")
    
    if video_url and is_vk_url(video_url):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Смотреть видеоурок", url=video_url)]
        ])
        await callback.message.answer(
            f"📹 *Видеоурок по теме: {lesson_title}*\n\n"
            f"Посмотри видео, затем пройди тест для закрепления материала:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer(
            "❌ *Видеоурок временно недоступен*\n\n"
            "Ты можешь сразу перейти к тесту.",
            parse_mode="Markdown"
        )
    
    # Отправляем кнопку для перехода к тесту
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Перейти к тесту", callback_data="start_test")],
        [InlineKeyboardButton(text="🔄 Пройти заново", callback_data="restart_lesson")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")]
    ])
    await callback.message.answer(
        "👇 *Выбери дальнейшее действие:*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data == "start_test")
async def start_test_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tests = data.get("tests", [])
    
    if tests:
        # Сбрасываем индексы теста
        await state.update_data(
            current_test_index=0,
            correct_answers=0,
            user_answers={}
        )
        
        await callback.message.answer(
            f"📝 *Начинаем тестирование!*\n\n"
            f"Тест состоит из {len(tests)} вопросов.\n"
            f"Для зачёта нужно ответить правильно на 70% вопросов.\n\n"
            f"👇 *Отвечай на вопросы:*",
            parse_mode="Markdown"
        )
        
        await send_next_question(callback.message, state)
        await state.set_state(Learning.test)
    else:
        await callback.message.answer(
            "❌ *Ошибка:* Тесты не найдены для этого урока.",
            parse_mode="Markdown"
        )
    
    await callback.answer()

async def send_next_question(message: Message, state: FSMContext):
    data = await state.get_data()
    tests = data.get("tests", [])
    current_test_index = data.get("current_test_index", 0)
    
    if current_test_index < len(tests):
        test = tests[current_test_index]
        question = test["question"]
        options = test["options"]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"test_{current_test_index}_{i}")] 
            for i, opt in enumerate(options)
        ])
        
        progress_text = f"📝 *Вопрос {current_test_index + 1} из {len(tests)}*\n\n"
        
        await message.answer(
            progress_text + question,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        correct_answers = data.get("correct_answers", 0)
        total_questions = len(tests)
        lesson_title = data["lesson_title"]
        user_id = message.from_user.id
        
        percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        if percentage >= 70:
            mark_lesson_completed(user_id, lesson_title)
            result_text = (
                f"🎉 *Поздравляю!* Ты успешно сдал тест!\n\n"
                f"📊 *Результат:* {correct_answers}/{total_questions} ({percentage:.0f}%)\n"
                f"🏆 Урок «{lesson_title}» засчитан!"
            )
        else:
            result_text = (
                f"📚 *Нужно повторить материал*\n\n"
                f"📊 *Результат:* {correct_answers}/{total_questions} ({percentage:.0f}%)\n"
                f"❌ Для зачёта нужно 70% правильных ответов.\n\n"
                f"💡 Пересмотри видеоурок и попробуй ещё раз."
            )
        
        await message.answer(result_text, parse_mode="Markdown")
        
        # Разбор ошибок
        if percentage < 100:
            review_text = "📖 *Разбор ошибок:*\n\n"
            for i, test in enumerate(tests):
                user_answer_index = data.get(f"answer_{i}", -1)
                is_correct = (user_answer_index == test["correct"])
                status = "✅" if is_correct else "❌"
                correct_answer = test["options"][test["correct"]]
                review_text += f"{status} *{test['question']}*\n"
                if not is_correct:
                    review_text += f"   Правильный ответ: {correct_answer}\n"
                    if "explanation" in test:
                        review_text += f"   💡 {test['explanation']}\n"
                review_text += "\n"
            await message.answer(review_text, parse_mode="Markdown")
        
        # Кнопки для дальнейших действий
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 Другие уроки", callback_data="back_to_lessons")],
            [InlineKeyboardButton(text="🔄 Пройти заново", callback_data="restart_lesson")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")]
        ])
        await message.answer(
            "👇 *Выбери дальнейшее действие:*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await state.clear()

@router.callback_query(Learning.test, F.data.startswith("test_"))
async def answer_test(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    question_index = int(parts[1])
    answer_index = int(parts[2])
    
    data = await state.get_data()
    tests = data.get("tests", [])
    current_test_index = data.get("current_test_index", 0)
    correct_answers = data.get("correct_answers", 0)
    user_answers = data.get("user_answers", {})
    
    if question_index == current_test_index:
        user_answers[question_index] = answer_index
        
        is_correct = (answer_index == tests[question_index]["correct"])
        if is_correct:
            correct_answers += 1
            response_text = "✅ *Верно!*"
        else:
            correct_answer = tests[question_index]["options"][tests[question_index]["correct"]]
            response_text = f"❌ *Неверно*\nПравильный ответ: {correct_answer}"
        
        if "explanation" in tests[question_index]:
            response_text += f"\n\n💡 {tests[question_index]['explanation']}"
        
        await callback.message.answer(response_text, parse_mode="Markdown")
        
        await state.update_data(
            current_test_index=current_test_index + 1,
            correct_answers=correct_answers,
            user_answers=user_answers
        )
        
        await send_next_question(callback.message, state)
    else:
        await callback.message.answer("⏳ Пожалуйста, ответь на текущий вопрос.")
    
    await callback.answer()

@router.callback_query(F.data == "restart_lesson")
async def restart_lesson_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lesson_data = data.get("lesson_data")
    lesson_title = data.get("lesson_title")
    video_url = data.get("video_url", "")
    
    if lesson_data and lesson_title:
        steps = lesson_data["steps"]
        tests = lesson_data.get("tests", [])
        
        await state.update_data(
            current_step=0,
            total_steps=len(steps),
            tests=tests,
            current_test_index=0,
            correct_answers=0,
            user_answers={},
            video_url=video_url
        )
        
        # Отправляем первый шаг заново
        await send_step(
            callback.message,
            steps[0],
            1,
            len(steps),
            lesson_title
        )
        
        await callback.message.answer(
            "👇 *Нажми «Далее», чтобы продолжить*",
            reply_markup=get_next_button(),
            parse_mode="Markdown"
        )
        
        await state.set_state(Learning.waiting_for_next)
    else:
        await callback.message.answer(
            "❌ *Ошибка:* Не удалось перезапустить урок.",
            parse_mode="Markdown"
        )
    
    await callback.answer()

@router.callback_query(F.data == "back_to_lessons")
async def back_to_lessons_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await list_lessons(callback.message)
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    from handlers.start import main_kb
    await callback.message.answer(
        "🏠 *Главное меню*\n\nВыбери действие:",
        reply_markup=main_kb,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_lesson")
async def cancel_lesson_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    from handlers.start import main_kb
    await callback.message.answer(
        "⏹️ *Урок отменён*\n\nТы вернулся в главное меню.",
        reply_markup=main_kb,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(Command("cancel"))
async def cancel_lesson_text(message: Message, state: FSMContext):
    await state.clear()
    from handlers.start import main_kb
    await message.answer(
        "⏹️ *Урок отменён*\n\nТы вернулся в главное меню.",
        reply_markup=main_kb,
        parse_mode="Markdown"
    )
    await callback.answer()