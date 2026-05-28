from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from database import pool
from templates.broadcaster.keyboards import (
    main_menu_kb, back_main_kb, content_type_kb,
    schedule_type_kb, weekday_kb, channels_select_kb,
    scheduled_list_kb, message_detail_kb,
    channels_manage_kb
)
from templates.broadcaster.scheduler import (
    schedule_message, cancel_scheduled_message,
    startup_broadcaster_jobs
)

router = Router()


class BcStates(StatesGroup):
    # Xabar yaratish
    select_content_type = State()
    waiting_text = State()
    waiting_photo = State()
    waiting_video = State()
    select_schedule = State()
    waiting_datetime = State()
    waiting_time = State()
    select_weekday = State()
    select_channels = State()
    # Kanal qo'shish
    add_channel_id = State()
    add_channel_name = State()


# ═══════════════════════════════════════
# YORDAMCHI
# ═══════════════════════════════════════

async def get_bot_row(bot: Bot) -> dict | None:
    bot_info = await bot.get_me()
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, admin_id FROM bots WHERE bot_username = $1",
            bot_info.username
        )
        return dict(row) if row else None


async def is_admin_user(bot: Bot, user_id: int) -> bool:
    row = await get_bot_row(bot)
    return row and row['admin_id'] == user_id


async def get_channels(bot_id: int) -> list:
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM broadcaster_channels WHERE bot_id = $1", bot_id
        )
        return [dict(r) for r in rows]


# ═══════════════════════════════════════
# START — FAQAT ADMIN
# ═══════════════════════════════════════

@router.message(CommandStart())
async def bc_start(message: Message, bot: Bot, state: FSMContext):
    await state.clear()
    if not await is_admin_user(bot, message.from_user.id):
        await message.answer(
            "⚠️ Bu bot faqat admin uchun!\n\n"
            "Bot egasi botni sozlash uchun /admin buyrug'ini yuboring."
        )
        return
    await message.answer(
        "📢 <b>Avto Xabar Bot</b>\n\n"
        "Kanallaringizga avtomatik xabar rejalashtiring!",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )

    # Startup — mavjud joblarni yuklash
    row = await get_bot_row(bot)
    await startup_broadcaster_jobs(bot, row['id'])


@router.message(Command("admin"))
async def bc_admin(message: Message, bot: Bot, state: FSMContext):
    await state.clear()
    if not await is_admin_user(bot, message.from_user.id):
        return
    await message.answer(
        "📢 <b>Avto Xabar Bot — Boshqaruv</b>",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "bc_main")
async def bc_main_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "📢 <b>Avto Xabar Bot</b>",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


# ═══════════════════════════════════════
# YANGI XABAR YARATISH
# ═══════════════════════════════════════

@router.callback_query(F.data == "bc_new")
async def bc_new_message(callback: CallbackQuery, bot: Bot, state: FSMContext):
    if not await is_admin_user(bot, callback.from_user.id):
        return

    row = await get_bot_row(bot)
    channels = await get_channels(row['id'])

    if not channels:
        await callback.answer(
            "❌ Avval kanal qo'shing!",
            show_alert=True
        )
        return

    await state.set_state(BcStates.select_content_type)
    await callback.message.edit_text(
        "📝 <b>Xabar turi:</b>",
        reply_markup=content_type_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


# ── Kontent turi ──

@router.callback_query(F.data == "bc_type_text")
async def bc_type_text(callback: CallbackQuery, state: FSMContext):
    await state.update_data(content_type="text", file_id=None)
    await state.set_state(BcStates.waiting_text)
    await callback.message.edit_text(
        "📝 Xabar matnini yozing (HTML formatda):\n\n"
        "Masalan: <code>&lt;b&gt;Yangi post!&lt;/b&gt;</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "bc_type_photo")
async def bc_type_photo(callback: CallbackQuery, state: FSMContext):
    await state.update_data(content_type="photo")
    await state.set_state(BcStates.waiting_photo)
    await callback.message.edit_text("🖼️ Rasm yuboring:")
    await callback.answer()


@router.callback_query(F.data == "bc_type_video")
async def bc_type_video(callback: CallbackQuery, state: FSMContext):
    await state.update_data(content_type="video")
    await state.set_state(BcStates.waiting_video)
    await callback.message.edit_text("🎥 Video yuboring:")
    await callback.answer()


@router.message(BcStates.waiting_photo, F.photo)
async def bc_photo_received(message: Message, state: FSMContext):
    await state.update_data(file_id=message.photo[-1].file_id)
    await state.set_state(BcStates.waiting_text)
    await message.answer("📝 Rasm uchun matn (sarlavha) yozing:")


@router.message(BcStates.waiting_photo)
async def bc_photo_wrong(message: Message):
    await message.answer("❌ Iltimos, rasm yuboring.")


@router.message(BcStates.waiting_video, F.video)
async def bc_video_received(message: Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(BcStates.waiting_text)
    await message.answer("📝 Video uchun matn (sarlavha) yozing:")


@router.message(BcStates.waiting_video)
async def bc_video_wrong(message: Message):
    await message.answer("❌ Iltimos, video yuboring.")


@router.message(BcStates.waiting_text)
async def bc_text_received(message: Message, state: FSMContext):
    await state.update_data(text=message.html_text)
    await state.set_state(BcStates.select_schedule)
    await message.answer(
        "⏰ <b>Yuborish rejimi:</b>",
        reply_markup=schedule_type_kb(),
        parse_mode="HTML"
    )


# ── Rejim tanlash ──

@router.callback_query(F.data == "bc_sched_once")
async def bc_sched_once(callback: CallbackQuery, state: FSMContext):
    await state.update_data(schedule_type="once")
    await state.set_state(BcStates.waiting_datetime)
    await callback.message.edit_text(
        "📅 Yuborish sanasi va vaqtini kiriting:\n\n"
        "Format: <code>DD.MM.YYYY HH:MM</code>\n"
        "Masalan: <code>25.12.2025 14:30</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "bc_sched_daily")
async def bc_sched_daily(callback: CallbackQuery, state: FSMContext):
    await state.update_data(schedule_type="daily")
    await state.set_state(BcStates.waiting_time)
    await callback.message.edit_text(
        "⏰ Har kuni qaysi vaqtda yuborilsin?\n\n"
        "Format: <code>HH:MM</code>\n"
        "Masalan: <code>09:00</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "bc_sched_weekly")
async def bc_sched_weekly(callback: CallbackQuery, state: FSMContext):
    await state.update_data(schedule_type="weekly")
    await state.set_state(BcStates.select_weekday)
    await callback.message.edit_text(
        "📆 Qaysi kuni yuborilsin?",
        reply_markup=weekday_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "bc_sched_monthly")
async def bc_sched_monthly(callback: CallbackQuery, state: FSMContext):
    await state.update_data(schedule_type="monthly")
    await state.set_state(BcStates.waiting_datetime)
    await callback.message.edit_text(
        "🗓️ Har oy qaysi sana va vaqtda yuborilsin?\n\n"
        "Format: <code>DD HH:MM</code>\n"
        "Masalan: <code>15 10:00</code> → har oy 15-kuni soat 10:00",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bc_day_"))
async def bc_weekday_selected(callback: CallbackQuery, state: FSMContext):
    weekday = int(callback.data.split("_")[-1])
    await state.update_data(weekday=weekday)
    await state.set_state(BcStates.waiting_time)
    days = ["Yakshanba", "Dushanba", "Seshanba", "Chorshanba",
            "Payshanba", "Juma", "Shanba"]
    await callback.message.edit_text(
        f"✅ Kun: <b>{days[weekday]}</b>\n\n"
        f"⏰ Vaqtni kiriting:\n"
        f"Format: <code>HH:MM</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(BcStates.waiting_datetime)
async def bc_datetime_received(message: Message, state: FSMContext):
    data = await state.get_data()
    schedule_type = data.get('schedule_type')

    try:
        if schedule_type == 'once':
            dt = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
            if dt < datetime.now():
                await message.answer("❌ O'tgan vaqtni kiritmang!")
                return
        elif schedule_type == 'monthly':
            parts = message.text.strip().split()
            day = int(parts[0])
            time_parts = parts[1].split(":")
            dt = datetime.now().replace(
                day=day,
                hour=int(time_parts[0]),
                minute=int(time_parts[1]),
                second=0
            )
        else:
            raise ValueError

    except (ValueError, IndexError):
        fmt = "DD.MM.YYYY HH:MM" if schedule_type == 'once' else "DD HH:MM"
        await message.answer(f"❌ Format xato! To'g'ri: <code>{fmt}</code>", parse_mode="HTML")
        return

    await state.update_data(scheduled_at=dt.isoformat())
    await state.set_state(BcStates.select_channels)
    await show_channel_select(message, state, data.get('bot_id_temp'))


@router.message(BcStates.waiting_time)
async def bc_time_received(message: Message, state: FSMContext):
    try:
        time_parts = message.text.strip().split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except (ValueError, IndexError):
        await message.answer("❌ Format xato! To'g'ri: <code>HH:MM</code>", parse_mode="HTML")
        return

    now = datetime.now()
    dt = now.replace(hour=hour, minute=minute, second=0)
    await state.update_data(scheduled_at=dt.isoformat())
    await state.set_state(BcStates.select_channels)
    await show_channel_select(message, state)


async def show_channel_select(target, state: FSMContext, bot_id: int = None):
    data = await state.get_data()

    # bot_id ni state dan olish
    from templates.broadcaster.handlers import _temp_bot_ids
    user_id = target.from_user.id if hasattr(target, 'from_user') else target.chat.id
    bot_id = _temp_bot_ids.get(user_id)

    if not bot_id:
        await target.answer("❌ Xato! Qaytadan boshlang.")
        return

    channels = await get_channels(bot_id)
    await state.update_data(selected_channels=[], bot_id=bot_id)

    text = "📢 <b>Xabar yuboriladigan kanallarni tanlang:</b>"
    kb = channels_select_kb(channels, [])

    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await target.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


# Temp storage for bot_id per user
_temp_bot_ids: dict = {}


@router.callback_query(F.data.startswith("bc_sel_ch_"))
async def bc_select_channel(callback: CallbackQuery, state: FSMContext, bot: Bot):
    ch_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    selected = data.get('selected_channels', [])
    bot_id = data.get('bot_id')

    if not bot_id:
        row = await get_bot_row(bot)
        bot_id = row['id']
        await state.update_data(bot_id=bot_id)

    if ch_id in selected:
        selected.remove(ch_id)
    else:
        selected.append(ch_id)

    await state.update_data(selected_channels=selected)

    channels = await get_channels(bot_id)
    await callback.message.edit_reply_markup(
        reply_markup=channels_select_kb(channels, selected)
    )
    await callback.answer()


@router.callback_query(F.data == "bc_confirm_channels")
async def bc_confirm_channels(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    selected = data.get('selected_channels', [])

    if not selected:
        await callback.answer("❌ Kamida 1 ta kanal tanlang!", show_alert=True)
        return

    row = await get_bot_row(bot)
    bot_id = row['id']

    scheduled_at = datetime.fromisoformat(data['scheduled_at'])

    # Har tanlangan kanal uchun xabar yaratish
    async with database.pool.acquire() as conn:
        for ch_id in selected:
            ch = await conn.fetchrow(
                "SELECT channel_id FROM broadcaster_channels WHERE id = $1", ch_id
            )
            if not ch:
                continue

            msg_id = await conn.fetchval("""
                INSERT INTO broadcaster_messages
                (bot_id, channel_id, content_type, text, file_id,
                 schedule_type, scheduled_at, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, TRUE)
                RETURNING id
            """,
                bot_id,
                ch['channel_id'],
                data['content_type'],
                data.get('text'),
                data.get('file_id'),
                data['schedule_type'],
                scheduled_at
            )

            # Schedulerga qo'shish
            await schedule_message(
                bot, bot_id, msg_id,
                data['schedule_type'],
                scheduled_at,
                data.get('weekday')
            )

    await state.clear()

    sched_texts = {
        "once": "bir martalik",
        "daily": "har kuni",
        "weekly": "har hafta",
        "monthly": "har oy",
    }

    await callback.message.edit_text(
        f"✅ <b>Xabar rejalashtirildi!</b>\n\n"
        f"📢 Kanallar: <b>{len(selected)} ta</b>\n"
        f"⏰ Rejim: <b>{sched_texts.get(data['schedule_type'])}</b>\n"
        f"📅 Vaqt: <b>{scheduled_at.strftime('%d.%m.%Y %H:%M')}</b>",
        reply_markup=back_main_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


# ═══════════════════════════════════════
# REJALASHTIRILGANLAR
# ═══════════════════════════════════════

@router.callback_query(F.data == "bc_scheduled")
async def bc_scheduled_list(callback: CallbackQuery, bot: Bot):
    if not await is_admin_user(bot, callback.from_user.id):
        return

    row = await get_bot_row(bot)
    async with database.pool.acquire() as conn:
        messages = await conn.fetch("""
            SELECT id, channel_id, schedule_type, is_active, scheduled_at
            FROM broadcaster_messages
            WHERE bot_id = $1
            ORDER BY created_at DESC
        """, row['id'])

    if not messages:
        await callback.answer("📋 Hali xabarlar yo'q!", show_alert=True)
        return

    await callback.message.edit_text(
        f"📋 <b>Rejalashtirilgan xabarlar ({len(messages)} ta)</b>",
        reply_markup=scheduled_list_kb([dict(m) for m in messages]),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bc_msg_"))
async def bc_message_detail(callback: CallbackQuery, bot: Bot):
    if not await is_admin_user(bot, callback.from_user.id):
        return

    msg_id = int(callback.data.split("_")[-1])

    async with database.pool.acquire() as conn:
        msg = await conn.fetchrow(
            "SELECT * FROM broadcaster_messages WHERE id = $1", msg_id
        )

    if not msg:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return

    msg = dict(msg)
    sched_icons = {
        "once": "1️⃣ Bir martalik",
        "daily": "📅 Har kuni",
        "weekly": "📆 Har hafta",
        "monthly": "🗓️ Har oy",
    }
    status = "✅ Faol" if msg['is_active'] else "⏸ To'xtatilgan"
    content_icons = {"text": "📝", "photo": "🖼️", "video": "🎥"}

    await callback.message.edit_text(
        f"📌 <b>Xabar #{msg_id}</b>\n\n"
        f"{content_icons.get(msg['content_type'], '📝')} Tur: {msg['content_type']}\n"
        f"📢 Kanal: {msg['channel_id']}\n"
        f"⏰ Rejim: {sched_icons.get(msg['schedule_type'])}\n"
        f"📅 Vaqt: {msg['scheduled_at'].strftime('%d.%m.%Y %H:%M')}\n"
        f"📊 Holat: {status}\n"
        f"🕐 Oxirgi yuborilgan: "
        f"{msg['last_sent_at'].strftime('%d.%m %H:%M') if msg['last_sent_at'] else 'hali yo\'q'}",
        reply_markup=message_detail_kb(msg_id, msg['is_active']),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bc_pause_"))
async def bc_pause_message(callback: CallbackQuery, bot: Bot):
    if not await is_admin_user(bot, callback.from_user.id):
        return
    msg_id = int(callback.data.split("_")[-1])
    row = await get_bot_row(bot)

    async with database.pool.acquire() as conn:
        await conn.execute(
            "UPDATE broadcaster_messages SET is_active = FALSE WHERE id = $1", msg_id
        )

    await cancel_scheduled_message(row['id'], msg_id)
    await callback.answer("⏸ To'xtatildi!", show_alert=True)
    await bc_message_detail(callback, bot)


@router.callback_query(F.data.startswith("bc_resume_"))
async def bc_resume_message(callback: CallbackQuery, bot: Bot):
    if not await is_admin_user(bot, callback.from_user.id):
        return
    msg_id = int(callback.data.split("_")[-1])
    row = await get_bot_row(bot)

    async with database.pool.acquire() as conn:
        await conn.execute(
            "UPDATE broadcaster_messages SET is_active = TRUE WHERE id = $1", msg_id
        )
        msg = await conn.fetchrow(
            "SELECT * FROM broadcaster_messages WHERE id = $1", msg_id
        )

    await schedule_message(
        bot, row['id'], msg_id,
        msg['schedule_type'],
        msg['scheduled_at']
    )
    await callback.answer("▶️ Faollashtirildi!", show_alert=True)
    await bc_message_detail(callback, bot)


@router.callback_query(F.data.startswith("bc_del_msg_"))
async def bc_delete_message(callback: CallbackQuery, bot: Bot):
    if not await is_admin_user(bot, callback.from_user.id):
        return
    msg_id = int(callback.data.split("_")[-1])
    row = await get_bot_row(bot)

    await cancel_scheduled_message(row['id'], msg_id)

    async with database.pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM broadcaster_messages WHERE id = $1", msg_id
        )

    await callback.answer("🗑️ O'chirildi!", show_alert=True)
    await bc_scheduled_list(callback, bot)


# ═══════════════════════════════════════
# KANALLAR BOSHQARUVI
# ═══════════════════════════════════════

@router.callback_query(F.data == "bc_channels")
async def bc_channels_handler(callback: CallbackQuery, bot: Bot):
    if not await is_admin_user(bot, callback.from_user.id):
        return
    row = await get_bot_row(bot)
    channels = await get_channels(row['id'])

    await callback.message.edit_text(
        f"📢 <b>Kanallar ({len(channels)} ta)</b>\n\n"
        f"⚠️ Bot har bir kanalda <b>admin</b> bo'lishi kerak!",
        reply_markup=channels_manage_kb(channels),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "bc_add_ch")
async def bc_add_channel(callback: CallbackQuery, bot: Bot, state: FSMContext):
    if not await is_admin_user(bot, callback.from_user.id):
        return
    await state.set_state(BcStates.add_channel_id)
    await callback.message.edit_text(
        "📢 Kanal ID kiriting:\n\n"
        "Masalan: <code>@mening_kanalim</code>\n"
        "yoki <code>-1001234567890</code>\n\n"
        "💡 Raqamli ID olish uchun @getmyid_bot dan foydalaning.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(BcStates.add_channel_id)
async def bc_channel_id(message: Message, state: FSMContext, bot: Bot):
    channel_id = message.text.strip()

    # Kanalda bot admin ekanligini tekshirish
    try:
        chat = await bot.get_chat(channel_id)
        bot_member = await bot.get_chat_member(channel_id, (await bot.get_me()).id)
        if bot_member.status not in ['administrator', 'creator']:
            await message.answer(
                "❌ <b>Bot kanalda admin emas!</b>\n\n"
                "Avval botni kanalga admin qilib, qayta kiriting.",
                parse_mode="HTML"
            )
            return
        channel_name = chat.title or channel_id
    except Exception:
        await message.answer(
            "❌ Kanal topilmadi yoki bot kanalga qo'shilmagan!\n\n"
            "1. Botni kanalga qo'shing\n"
            "2. Admin huquqini bering\n"
            "3. Qayta kiriting."
        )
        return

    await state.update_data(ch_id=channel_id, ch_name=channel_name)
    await state.set_state(BcStates.add_channel_name)
    await message.answer(
        f"✅ Kanal topildi: <b>{channel_name}</b>\n\n"
        f"Kanal uchun nom kiriting (menuda ko'rinadigan nom):",
        parse_mode="HTML"
    )


@router.message(BcStates.add_channel_name)
async def bc_channel_name(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    row = await get_bot_row(bot)

    async with database.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO broadcaster_channels (bot_id, channel_id, channel_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (bot_id, channel_id) DO UPDATE
            SET channel_name = $3
        """, row['id'], data['ch_id'], message.text.strip())

    await message.answer(
        f"✅ <b>{message.text.strip()}</b> kanali qo'shildi!",
        reply_markup=back_main_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("bc_del_ch_"))
async def bc_delete_channel(callback: CallbackQuery, bot: Bot):
    if not await is_admin_user(bot, callback.from_user.id):
        return
    ch_id = int(callback.data.split("_")[-1])

    async with database.pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM broadcaster_channels WHERE id = $1", ch_id
        )

    await callback.answer("✅ Kanal o'chirildi!", show_alert=True)
    await bc_channels_handler(callback, bot)


# ═══════════════════════════════════════
# STATISTIKA
# ═══════════════════════════════════════

@router.callback_query(F.data == "bc_stats")
async def bc_stats_handler(callback: CallbackQuery, bot: Bot):
    if not await is_admin_user(bot, callback.from_user.id):
        return
    row = await get_bot_row(bot)
    bot_id = row['id']

    async with database.pool.acquire() as conn:
        total_msgs = await conn.fetchval(
            "SELECT COUNT(*) FROM broadcaster_messages WHERE bot_id = $1", bot_id
        )
        active_msgs = await conn.fetchval("""
            SELECT COUNT(*) FROM broadcaster_messages
            WHERE bot_id = $1 AND is_active = TRUE
        """, bot_id)
        total_channels = await conn.fetchval(
            "SELECT COUNT(*) FROM broadcaster_channels WHERE bot_id = $1", bot_id
        )
        sent_today = await conn.fetchval("""
            SELECT COUNT(*) FROM broadcaster_messages
            WHERE bot_id = $1 AND DATE(last_sent_at) = CURRENT_DATE
        """, bot_id)

    await callback.message.edit_text(
        f"📊 <b>Statistika</b>\n\n"
        f"📢 Kanallar: <b>{total_channels}</b>\n"
        f"📋 Jami xabarlar: <b>{total_msgs}</b>\n"
        f"✅ Faol xabarlar: <b>{active_msgs}</b>\n"
        f"📤 Bugun yuborildi: <b>{sent_today}</b>",
        reply_markup=back_main_kb(),
        parse_mode="HTML"
    )
    await callback.answer()
