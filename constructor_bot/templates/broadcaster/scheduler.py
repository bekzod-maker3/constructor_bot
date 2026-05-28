from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from aiogram import Bot
from datetime import datetime
import logging

from database import pool

logger = logging.getLogger(__name__)

# Har bir bot uchun scheduler: {bot_id: AsyncIOScheduler}
bot_schedulers: dict = {}


async def send_scheduled_message(bot: Bot, msg_id: int):
    """Rejalashtirilgan xabarni yuborish"""
    async with database.pool.acquire() as conn:
        msg = await conn.fetchrow("""
            SELECT * FROM broadcaster_messages WHERE id = $1 AND is_active = TRUE
        """, msg_id)

    if not msg:
        return

    try:
        if msg['content_type'] == 'text':
            await bot.send_message(
                msg['channel_id'],
                msg['text'],
                parse_mode="HTML"
            )
        elif msg['content_type'] == 'photo':
            await bot.send_photo(
                msg['channel_id'],
                photo=msg['file_id'],
                caption=msg['text'],
                parse_mode="HTML"
            )
        elif msg['content_type'] == 'video':
            await bot.send_video(
                msg['channel_id'],
                video=msg['file_id'],
                caption=msg['text'],
                parse_mode="HTML"
            )

        # Oxirgi yuborilgan vaqtni yangilash
        async with database.pool.acquire() as conn:
            await conn.execute("""
                UPDATE broadcaster_messages SET last_sent_at = NOW() WHERE id = $1
            """, msg_id)

        # Bir martalik xabarni o'chirish
        if msg['schedule_type'] == 'once':
            async with database.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE broadcaster_messages SET is_active = FALSE WHERE id = $1
                """, msg_id)

        logger.info(f"✅ Xabar #{msg_id} yuborildi → {msg['channel_id']}")

    except Exception as e:
        logger.error(f"❌ Xabar #{msg_id} yuborilmadi: {e}")

        # Botni admin qilmagan bo'lsa xato logi
        async with database.pool.acquire() as conn:
            bot_row = await conn.fetchrow(
                "SELECT admin_id FROM bots WHERE id = $1", msg['bot_id']
            )
        if bot_row:
            try:
                await bot.send_message(
                    bot_row['admin_id'],
                    f"⚠️ Xabar #{msg_id} yuborilmadi!\n"
                    f"Kanal: {msg['channel_id']}\n"
                    f"Sabab: Bot kanalda admin emas yoki kanal topilmadi."
                )
            except Exception:
                pass


def get_cron_trigger(schedule_type: str, scheduled_at: datetime, weekday: int = None) -> CronTrigger | DateTrigger:
    """Schedule turiga qarab trigger yaratish"""
    if schedule_type == 'once':
        return DateTrigger(run_date=scheduled_at)

    elif schedule_type == 'daily':
        return CronTrigger(
            hour=scheduled_at.hour,
            minute=scheduled_at.minute,
            timezone="Asia/Tashkent"
        )

    elif schedule_type == 'weekly':
        return CronTrigger(
            day_of_week=weekday if weekday is not None else scheduled_at.weekday(),
            hour=scheduled_at.hour,
            minute=scheduled_at.minute,
            timezone="Asia/Tashkent"
        )

    elif schedule_type == 'monthly':
        return CronTrigger(
            day=scheduled_at.day,
            hour=scheduled_at.hour,
            minute=scheduled_at.minute,
            timezone="Asia/Tashkent"
        )


def get_or_create_scheduler(bot_id: int) -> AsyncIOScheduler:
    """Bot uchun scheduler olish yoki yaratish"""
    if bot_id not in bot_schedulers:
        scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
        scheduler.start()
        bot_schedulers[bot_id] = scheduler
    return bot_schedulers[bot_id]


async def schedule_message(bot: Bot, bot_id: int, msg_id: int,
                            schedule_type: str, scheduled_at: datetime,
                            weekday: int = None):
    """Xabarni rejalashtirishga qo'shish"""
    scheduler = get_or_create_scheduler(bot_id)

    trigger = get_cron_trigger(schedule_type, scheduled_at, weekday)

    scheduler.add_job(
        send_scheduled_message,
        trigger=trigger,
        args=[bot, msg_id],
        id=f"msg_{msg_id}",
        replace_existing=True,
        misfire_grace_time=300,
    )
    logger.info(f"📅 Xabar #{msg_id} rejalashtirildi ({schedule_type})")


async def cancel_scheduled_message(bot_id: int, msg_id: int):
    """Rejalashtirilgan xabarni bekor qilish"""
    scheduler = bot_schedulers.get(bot_id)
    if scheduler:
        try:
            scheduler.remove_job(f"msg_{msg_id}")
        except Exception:
            pass


async def startup_broadcaster_jobs(bot: Bot, bot_id: int):
    """Server qayta ishga tushganda barcha rejalashtirilganlarni yuklash"""
    async with database.pool.acquire() as conn:
        messages = await conn.fetch("""
            SELECT * FROM broadcaster_messages
            WHERE bot_id = $1 AND is_active = TRUE
        """, bot_id)

    for msg in messages:
        try:
            await schedule_message(
                bot, bot_id, msg['id'],
                msg['schedule_type'],
                msg['scheduled_at'],
            )
        except Exception as e:
            logger.error(f"Job yuklashda xato #{msg['id']}: {e}")

    logger.info(f"✅ Bot #{bot_id} uchun {len(messages)} ta job yuklandi")


def stop_bot_scheduler(bot_id: int):
    """Bot schedulerini to'xtatish"""
    scheduler = bot_schedulers.pop(bot_id, None)
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
