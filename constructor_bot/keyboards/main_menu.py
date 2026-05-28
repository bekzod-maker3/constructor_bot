from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu_kb() -> InlineKeyboardMarkup:
    """Asosiy menyu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Bot yaratish", callback_data="create_bot")],
        [InlineKeyboardButton(text="📋 Mening botlarim", callback_data="my_bots")],
        [InlineKeyboardButton(text="💰 Balans", callback_data="balance")],
        [InlineKeyboardButton(text="🔗 Do'st taklif qilish", callback_data="referral")],
        [InlineKeyboardButton(text="📞 Yordam", callback_data="help")],
    ])


def back_to_main_kb() -> InlineKeyboardMarkup:
    """Orqaga — Asosiy menyu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")],
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    """Bekor qilish"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")],
    ])


def subscription_check_kb(channels: list, bot_url: str = None) -> InlineKeyboardMarkup:
    """Majburiy obuna tugmalari"""
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(
            text=f"📢 {ch['channel_name']}",
            url=ch['channel_url']
        )])
    buttons.append([InlineKeyboardButton(
        text="✅ Tekshirish", callback_data="check_subscription"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def template_select_kb() -> InlineKeyboardMarkup:
    """Shablon tanlash"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Quiz bot", callback_data="template_quiz")],
        [InlineKeyboardButton(text="🛒 Do'kon bot", callback_data="template_shop")],
        [InlineKeyboardButton(text="📢 Avto xabar bot", callback_data="template_broadcaster")],
        [InlineKeyboardButton(text="👥 Referral bot", callback_data="template_referral")],
        [InlineKeyboardButton(text="🎬 Kino bot", callback_data="template_kinobot")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")],
    ])


def confirm_kb(confirm_data: str, cancel_data: str = "main_menu") -> InlineKeyboardMarkup:
    """Tasdiqlash / Bekor qilish"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha", callback_data=confirm_data),
            InlineKeyboardButton(text="❌ Yo'q", callback_data=cancel_data),
        ]
    ])
