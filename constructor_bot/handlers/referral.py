from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from database import pool, get_setting
from keyboards.main_menu import back_to_main_kb

router = Router()


@router.callback_query(F.data == "referral")
async def referral_handler(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    # Bot username olish
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    # Referral statistika
    async with pool.acquire() as conn:
        refs_count = await conn.fetchval("""
            SELECT COUNT(*) FROM referrals WHERE referrer_id = $1
        """, user_id)

        total_earned = await conn.fetchval("""
            SELECT COALESCE(SUM(bonus_amount), 0) FROM referrals
            WHERE referrer_id = $1
        """, user_id)

    bonus = await get_setting('referral_bonus') or '5000'
    referral_enabled = await get_setting('referral_enabled')

    if referral_enabled != 'true':
        await callback.message.edit_text(
            "🔗 Referral tizimi hozircha o'chirilgan.",
            reply_markup=back_to_main_kb()
        )
        await callback.answer()
        return

    text = (
        f"🔗 <b>Do'st taklif qilish</b>\n\n"
        f"Har bir do'stingiz uchun <b>{int(bonus):,} so'm</b> bonus olasiz!\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"👥 Taklif qilganlar: <b>{refs_count} ta</b>\n"
        f"💰 Jami ishlagan: <b>{total_earned:,} so'm</b>\n\n"
        f"🔗 <b>Sizning havolangiz:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        f"Havolani do'stlaringizga yuboring. Ular ro'yxatdan o'tishi bilanoq "
        f"balansingizga bonus tushadi! 🎉"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_main_kb(),
        parse_mode="HTML"
    )
    await callback.answer()
