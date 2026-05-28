from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def my_bots_kb(bots: list) -> InlineKeyboardMarkup:
    """Foydalanuvchi botlari ro'yxati"""
    buttons = []
    for bot in bots:
        status = "✅" if bot['is_running'] else "❌"
        template_icons = {
            "quiz": "🎯",
            "shop": "🛒",
            "broadcaster": "📢",
            "referral": "👥",
            "kinobot": "🎬",
        }
        icon = template_icons.get(bot['template_type'], "🤖")
        buttons.append([InlineKeyboardButton(
            text=f"{status} {icon} @{bot['bot_username'] or 'bot'}",
            callback_data=f"bot_detail_{bot['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def bot_detail_kb(bot_id: int, is_running: bool) -> InlineKeyboardMarkup:
    """Bot detail sahifasi tugmalari"""
    toggle_text = "⏹ To'xtatish" if is_running else "▶️ Ishga tushirish"
    toggle_data = f"bot_stop_{bot_id}" if is_running else f"bot_start_{bot_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data=toggle_data)],
        [InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"bot_delete_{bot_id}")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="my_bots")],
    ])


def balance_kb() -> InlineKeyboardMarkup:
    """Balans sahifasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Balans to'ldirish", callback_data="topup_balance")],
        [InlineKeyboardButton(text="📋 To'lov tarixi", callback_data="payment_history")],
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")],
    ])


def topup_amounts_kb() -> InlineKeyboardMarkup:
    """Tez to'ldirish miqdorlari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="30,000 so'm", callback_data="topup_30000"),
            InlineKeyboardButton(text="50,000 so'm", callback_data="topup_50000"),
        ],
        [
            InlineKeyboardButton(text="100,000 so'm", callback_data="topup_100000"),
            InlineKeyboardButton(text="200,000 so'm", callback_data="topup_200000"),
        ],
        [InlineKeyboardButton(text="✏️ Boshqa miqdor", callback_data="topup_custom")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="balance")],
    ])


def after_topup_kb() -> InlineKeyboardMarkup:
    """Chek yuborilgandan keyin"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")],
    ])
