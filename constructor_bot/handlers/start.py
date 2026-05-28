from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from database import pool, get_setting
from keyboards.main_menu import main_menu_kb, subscription_check_kb, back_to_main_kb
from utils.subscription import check_user_subscription
from config import ADMIN_ID

router = Router()


# ═══════════════════════════════════════
# YORDAMCHI FUNKSIYALAR
# ═══════════════════════════════════════

async def get_or_create_user(user_id: int, username: str, full_name: str) -> dict:
    """Foydalanuvchini olish yoki yaratish"""
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE user_id = $1", user_id
        )
        if not user:
            trial_days = int(await get_setting('trial_days') or 7)
            trial_ends = datetime.now() + timedelta(days=trial_days)
            await conn.execute("""
                INSERT INTO users (user_id, username, full_name, trial_ends_at)
                VALUES ($1, $2, $3, $4)
            """, user_id, username, full_name, trial_ends)
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1", user_id
            )
        return dict(user)


async def get_referral_from_args(args: str) -> int | None:
    """Start argumentidan referral ID olish"""
    if args and args.startswith("ref_"):
        try:
            return int(args.split("_")[1])
        except (ValueError, IndexError):
            return None
    return None


async def apply_referral_bonus(referrer_id: int, new_user_id: int):
    """Referral bonus berish"""
    if referrer_id == new_user_id:
        return

    referral_enabled = await get_setting('referral_enabled')
    if referral_enabled != 'true':
        return

    async with pool.acquire() as conn:
        # Avval bu foydalanuvchi orqali referral bo'lganmi tekshirish
        exists = await conn.fetchval("""
            SELECT id FROM referrals WHERE referred_id = $1
        """, new_user_id)
        if exists:
            return

        # Referrer mavjudligini tekshirish
        referrer = await conn.fetchrow(
            "SELECT user_id FROM users WHERE user_id = $1", referrer_id
        )
        if not referrer:
            return

        bonus = int(await get_setting('referral_bonus') or 5000)

        # Bonusni berish
        await conn.execute("""
            UPDATE users SET balance = balance + $1 WHERE user_id = $2
        """, bonus, referrer_id)

        # Referral tarixiga yozish
        await conn.execute("""
            INSERT INTO referrals (referrer_id, referred_id, bonus_amount)
            VALUES ($1, $2, $3)
        """, referrer_id, new_user_id, bonus)

        # Yangi foydalanuvchiga referred_by yozish
        await conn.execute("""
            UPDATE users SET referred_by = $1 WHERE user_id = $2
        """, referrer_id, new_user_id)


async def send_main_menu(target, user: dict, state: FSMContext = None):
    """Asosiy menyuni yuborish"""
    if state:
        await state.clear()

    trial_active = (
        user['trial_ends_at'] and
        user['trial_ends_at'] > datetime.now()
    )

    if trial_active:
        days_left = (user['trial_ends_at'] - datetime.now()).days + 1
        trial_text = f"🎁 Trial: <b>{days_left} kun</b> qoldi\n"
    else:
        trial_text = ""

    text = (
        f"👋 Xush kelibsiz, <b>{user['full_name']}</b>!\n\n"
        f"{trial_text}"
        f"💰 Balans: <b>{user['balance']:,} so'm</b>\n\n"
        f"Quyidagi tugmalardan birini tanlang:"
    )

    if isinstance(target, Message):
        await target.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")
    elif isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=main_menu_kb(), parse_mode="HTML")


# ═══════════════════════════════════════
# HANDLERLAR
# ═══════════════════════════════════════

@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name or "Foydalanuvchi"

    await state.clear()

    # Ban tekshirish
    async with pool.acquire() as conn:
        banned = await conn.fetchval(
            "SELECT is_banned FROM users WHERE user_id = $1", user_id
        )
        if banned:
            await message.answer("🚫 Siz bloklangansiz. Admin bilan bog'laning.")
            return

    # Majburiy obuna tekshirish
    is_subscribed, not_subscribed = await check_user_subscription(bot, user_id)
    if not is_subscribed:
        channels_text = "\n".join([f"• {ch['channel_name']}" for ch in not_subscribed])
        await message.answer(
            f"⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:\n\n"
            f"{channels_text}",
            reply_markup=subscription_check_kb(not_subscribed),
            parse_mode="HTML"
        )
        return

    # Foydalanuvchini yaratish yoki olish
    args = message.text.split()[-1] if len(message.text.split()) > 1 else ""
    referrer_id = await get_referral_from_args(args)

    is_new_user = False
    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT user_id FROM users WHERE user_id = $1", user_id
        )
        if not exists:
            is_new_user = True

    user = await get_or_create_user(user_id, username, full_name)

    # Referral bonus (faqat yangi foydalanuvchilarga)
    if is_new_user and referrer_id:
        await apply_referral_bonus(referrer_id, user_id)

    # Asosiy menyuni ko'rsatish
    await send_main_menu(message, user, state)


@router.callback_query(F.data == "check_subscription")
async def check_subscription_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = callback.from_user.id

    is_subscribed, not_subscribed = await check_user_subscription(bot, user_id)

    if not is_subscribed:
        channels_text = "\n".join([f"• {ch['channel_name']}" for ch in not_subscribed])
        await callback.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)
        await callback.message.edit_text(
            f"⚠️ Quyidagi kanallarga obuna bo'ling:\n\n{channels_text}",
            reply_markup=subscription_check_kb(not_subscribed),
            parse_mode="HTML"
        )
        return

    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE user_id = $1", user_id
        )

    if not user:
        user = await get_or_create_user(
            user_id,
            callback.from_user.username or "",
            callback.from_user.full_name or "Foydalanuvchi"
        )

    await callback.answer("✅ Obuna tasdiqlandi!")
    await send_main_menu(callback, dict(user), state)


@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE user_id = $1", callback.from_user.id
        )
    if user:
        await send_main_menu(callback, dict(user))
    await callback.answer()


@router.callback_query(F.data == "help")
async def help_handler(callback: CallbackQuery):
    text = (
        "📞 <b>Yordam</b>\n\n"
        "❓ <b>Tez-tez so'raladigan savollar:</b>\n\n"
        "▪️ <b>Bot yaratish qancha turadi?</b>\n"
        "Har bir bot uchun kuniga 3,000 so'm yechiladi.\n\n"
        "▪️ <b>Trial nima?</b>\n"
        "Birinchi 7 kun bepul — 1 ta bot yaratishingiz mumkin.\n\n"
        "▪️ <b>Balans tugasa nima bo'ladi?</b>\n"
        "Bot to'xtatiladi. Balans to'ldirilgach qayta ishga tushadi.\n\n"
        "▪️ <b>Nechta bot yaratish mumkin?</b>\n"
        "Cheksiz — har biri uchun alohida 3,000 so'm/kun.\n\n"
        "👨‍💻 Admin bilan bog'lanish: @admin_username"
    )
    await callback.message.edit_text(
        text,
        reply_markup=back_to_main_kb(),
        parse_mode="HTML"
    )
    await callback.answer()
