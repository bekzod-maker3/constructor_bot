from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

import database
from database import get_setting
from keyboards.bot_create_menu import balance_kb, topup_amounts_kb, after_topup_kb
from keyboards.main_menu import back_to_main_kb
from utils.billing import get_payment_history, reactivate_bots_if_balance
from utils.notifications import notify_payment_confirmed
from config import ADMIN_ID

router = Router()


class BalanceStates(StatesGroup):
    waiting_custom_amount = State()
    waiting_check = State()


# ═══════════════════════════════════════
# BALANS SAHIFASI
# ═══════════════════════════════════════

@router.callback_query(F.data == "balance")
async def balance_handler(callback: CallbackQuery):
    async with database.pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE user_id = $1", callback.from_user.id
        )

    trial_active = (
        user['trial_ends_at'] and
        user['trial_ends_at'] > datetime.now()
    )

    if trial_active:
        days_left = (user['trial_ends_at'] - datetime.now()).days + 1
        trial_text = f"🎁 Trial: <b>{days_left} kun</b> qoldi\n"
    else:
        trial_text = ""

    daily_price = await get_setting('daily_price') or '3000'

    # Faol botlar soni
    async with database.pool.acquire() as conn:
        bots_count = await conn.fetchval("""
            SELECT COUNT(*) FROM bots
            WHERE user_id = $1 AND is_running = TRUE
        """, callback.from_user.id)

    daily_total = int(daily_price) * (bots_count or 0)

    text = (
        f"💰 <b>Balans</b>\n\n"
        f"{trial_text}"
        f"💵 Joriy balans: <b>{user['balance']:,} so'm</b>\n"
        f"🤖 Faol botlar: <b>{bots_count} ta</b>\n"
        f"📊 Kunlik to'lov: <b>{daily_total:,} so'm</b>\n\n"
        f"Balansni to'ldirish uchun tugmani bosing 👇"
    )

    await callback.message.edit_text(
        text,
        reply_markup=balance_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


# ═══════════════════════════════════════
# BALANS TO'LDIRISH
# ═══════════════════════════════════════

@router.callback_query(F.data == "topup_balance")
async def topup_handler(callback: CallbackQuery):
    card = await get_setting('payment_card') or "Karta raqami sozlanmagan"
    text = (
        f"💳 <b>Balans to'ldirish</b>\n\n"
        f"To'lov kartasi: <code>{card}</code>\n\n"
        f"Quyidagi miqdorlardan birini tanlang yoki o'zingiz kiriting:"
    )
    await callback.message.edit_text(
        text,
        reply_markup=topup_amounts_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("topup_") & ~F.data.endswith("custom"))
async def topup_amount_selected(callback: CallbackQuery, state: FSMContext):
    amount_str = callback.data.replace("topup_", "")
    try:
        amount = int(amount_str)
    except ValueError:
        return

    card = await get_setting('payment_card') or "Karta raqami sozlanmagan"

    await state.set_state(BalanceStates.waiting_check)
    await state.update_data(topup_amount=amount)

    await callback.message.edit_text(
        f"💳 <b>{amount:,} so'm</b> to'lash uchun:\n\n"
        f"Karta: <code>{card}</code>\n\n"
        f"To'lovni amalga oshirib, chek (screenshot) yuboring 👇",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "topup_custom")
async def topup_custom_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BalanceStates.waiting_custom_amount)
    await callback.message.edit_text(
        "✏️ To'ldirmoqchi bo'lgan miqdorni kiriting (so'mda):\n\n"
        "Masalan: <code>75000</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(BalanceStates.waiting_custom_amount)
async def custom_amount_handler(message: Message, state: FSMContext):
    try:
        amount = int(message.text.replace(" ", "").replace(",", ""))
        if amount < 10000:
            await message.answer("❌ Minimal to'lov: 10,000 so'm")
            return
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting. Masalan: 75000")
        return

    card = await get_setting('payment_card') or "Karta raqami sozlanmagan"

    await state.set_state(BalanceStates.waiting_check)
    await state.update_data(topup_amount=amount)

    await message.answer(
        f"💳 <b>{amount:,} so'm</b> to'lash uchun:\n\n"
        f"Karta: <code>{card}</code>\n\n"
        f"To'lovni amalga oshirib, chek (screenshot) yuboring 👇",
        parse_mode="HTML"
    )


@router.message(BalanceStates.waiting_check, F.photo)
async def check_received_handler(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    amount = data.get('topup_amount', 0)
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id

    # To'lovni DBga yozish
    async with database.pool.acquire() as conn:
        payment_id = await conn.fetchval("""
            INSERT INTO payments (user_id, amount, check_file_id, status)
            VALUES ($1, $2, $3, 'pending')
            RETURNING id
        """, user_id, amount, photo_id)

    await state.clear()

    # Foydalanuvchiga xabar
    await message.answer(
        f"✅ Chekingiz qabul qilindi!\n\n"
        f"💰 Miqdor: <b>{amount:,} so'm</b>\n"
        f"⏳ Admin tasdiqlashini kuting (odatda 1-2 soat ichida)\n\n"
        f"Tasdiqlanishi bilanoq balansingiz yangilanadi.",
        reply_markup=after_topup_kb(),
        parse_mode="HTML"
    )

    # Adminga xabar
    user = message.from_user
    admin_text = (
        f"💳 <b>Yangi to'lov so'rovi #{payment_id}</b>\n\n"
        f"👤 Foydalanuvchi: {user.full_name}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📱 Username: @{user.username or 'yo\'q'}\n"
        f"💰 Miqdor: <b>{amount:,} so'm</b>"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✅ Tasdiqlash",
            callback_data=f"admin_confirm_payment_{payment_id}"
        ),
        InlineKeyboardButton(
            text="❌ Rad etish",
            callback_data=f"admin_reject_payment_{payment_id}"
        ),
    ]])

    await bot.send_photo(
        ADMIN_ID,
        photo=photo_id,
        caption=admin_text,
        reply_markup=admin_kb,
        parse_mode="HTML"
    )


@router.message(BalanceStates.waiting_check)
async def check_wrong_format(message: Message):
    await message.answer(
        "❌ Iltimos, chekni <b>rasm (screenshot)</b> ko'rinishida yuboring.",
        parse_mode="HTML"
    )


# ═══════════════════════════════════════
# TO'LOV TARIXI
# ═══════════════════════════════════════

@router.callback_query(F.data == "payment_history")
async def payment_history_handler(callback: CallbackQuery):
    payments = await get_payment_history(callback.from_user.id)

    if not payments:
        await callback.answer("📋 To'lov tarixi bo'sh", show_alert=True)
        return

    status_icons = {
        'pending': '⏳',
        'confirmed': '✅',
        'rejected': '❌',
    }

    lines = []
    for p in payments:
        icon = status_icons.get(p['status'], '❓')
        date = p['created_at'].strftime('%d.%m.%Y')
        lines.append(f"{icon} {date} — <b>{p['amount']:,} so'm</b>")

    text = "📋 <b>To'lov tarixi (oxirgi 10 ta):</b>\n\n" + "\n".join(lines)

    await callback.message.edit_text(
        text,
        reply_markup=back_to_main_kb(),
        parse_mode="HTML"
    )
    await callback.answer()
