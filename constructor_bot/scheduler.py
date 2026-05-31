from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
import logging
import database
from database import pool

from utils.billing import process_daily_charges
from utils.notifications import notify_stopped_bots

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")


async def daily_charge_job(bot: Bot):
    """
    Har kecha 00:00 da ishlaydigan kunlik yechish.
    Balansi yetarli bo'lmagan botlar to'xtatiladi.
    """
    logger.info("💰 Kunlik yechish boshlanmoqda...")

    try:
        stopped_bots = await process_daily_charges()

        # To'xtatilgan botlar egalariga xabar yuborish
        if stopped_bots:
            await notify_stopped_bots(bot, stopped_bots)
            logger.info(f"⏹ {len(stopped_bots)} ta bot to'xtatildi")

        logger.info("✅ Kunlik yechish tugadi")

    except Exception as e:
        logger.error(f"Kunlik yechishda xato: {e}")


async def start_scheduler(bot: Bot):
    """Schedulerni ishga tushirish"""
    # Har kecha 00:00 da (Toshkent vaqti)
    scheduler.add_job(
        daily_charge_job,
        trigger=CronTrigger(hour=0, minute=0),
        args=[bot],
        id="daily_charge",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.start()
    logger.info("✅ Scheduler ishga tushdi (kunlik yechish: 00:00)")


async def stop_scheduler():
    """Schedulerni to'xtatish"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("⏹ Scheduler to'xtatildi")
