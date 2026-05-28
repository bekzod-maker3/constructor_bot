from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi xabar", callback_data="bc_new")],
        [InlineKeyboardButton(text="📋 Rejalashtirilganlar", callback_data="bc_scheduled")],
        [InlineKeyboardButton(text="📢 Kanallar", callback_data="bc_channels")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="bc_stats")],
    ])


def back_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Asosiy menyu", callback_data="bc_main")],
    ])


def content_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Matn", callback_data="bc_type_text")],
        [InlineKeyboardButton(text="🖼️ Rasm + matn", callback_data="bc_type_photo")],
        [InlineKeyboardButton(text="🎥 Video + matn", callback_data="bc_type_video")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="bc_main")],
    ])


def schedule_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1️⃣ Bir martalik", callback_data="bc_sched_once")],
        [InlineKeyboardButton(text="📅 Har kuni", callback_data="bc_sched_daily")],
        [InlineKeyboardButton(text="📆 Har hafta", callback_data="bc_sched_weekly")],
        [InlineKeyboardButton(text="🗓️ Har oy", callback_data="bc_sched_monthly")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="bc_main")],
    ])


def weekday_kb() -> InlineKeyboardMarkup:
    days = [
        ("Du", "1"), ("Se", "2"), ("Ch", "3"),
        ("Pa", "4"), ("Ju", "5"), ("Sh", "6"), ("Ya", "0"),
    ]
    buttons = []
    row = []
    for name, val in days:
        row.append(InlineKeyboardButton(text=name, callback_data=f"bc_day_{val}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="bc_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def channels_select_kb(channels: list, selected: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        check = "✅" if ch['id'] in selected else "☐"
        buttons.append([InlineKeyboardButton(
            text=f"{check} {ch['channel_name']}",
            callback_data=f"bc_sel_ch_{ch['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="bc_confirm_channels")])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="bc_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def scheduled_list_kb(messages: list) -> InlineKeyboardMarkup:
    buttons = []
    sched_icons = {
        "once": "1️⃣", "daily": "📅",
        "weekly": "📆", "monthly": "🗓️"
    }
    for m in messages:
        icon = sched_icons.get(m['schedule_type'], "📌")
        buttons.append([InlineKeyboardButton(
            text=f"{icon} #{m['id']} — {m['channel_id']}",
            callback_data=f"bc_msg_{m['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="bc_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def message_detail_kb(msg_id: int, is_active: bool) -> InlineKeyboardMarkup:
    toggle_text = "⏸ To'xtatish" if is_active else "▶️ Faollashtirish"
    toggle_data = f"bc_pause_{msg_id}" if is_active else f"bc_resume_{msg_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data=toggle_data)],
        [InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"bc_del_msg_{msg_id}")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="bc_scheduled")],
    ])


def channels_manage_kb(channels: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(
            text=f"❌ {ch['channel_name']}",
            callback_data=f"bc_del_ch_{ch['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="bc_add_ch")])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="bc_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
