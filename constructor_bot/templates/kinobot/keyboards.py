from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def subscription_kb(channels: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(
            text=f"📢 {ch['channel_name']}",
            url=ch['channel_url']
        )])
    buttons.append([InlineKeyboardButton(
        text="✅ Tekshirish",
        callback_data="kino_check_sub"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Kino qo'shish", callback_data="kino_add")],
        [InlineKeyboardButton(text="🗑️ Kino o'chirish", callback_data="kino_delete")],
        [InlineKeyboardButton(text="📋 Kinolar ro'yxati", callback_data="kino_list")],
        [InlineKeyboardButton(text="📣 Xabar yuborish", callback_data="kino_broadcast")],
        [InlineKeyboardButton(text="📢 Majburiy kanallar", callback_data="kino_channels")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="kino_stats")],
    ])


def admin_channels_kb(channels: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(
            text=f"❌ {ch['channel_name']}",
            callback_data=f"kino_del_ch_{ch['id']}"
        )])
    buttons.append([InlineKeyboardButton(
        text="➕ Kanal qo'shish", callback_data="kino_add_ch"
    )])
    buttons.append([InlineKeyboardButton(
        text="◀️ Orqaga", callback_data="kino_admin"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Admin panel", callback_data="kino_admin")],
    ])
