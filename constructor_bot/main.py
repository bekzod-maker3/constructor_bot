import uvicorn
import logging
import sys

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

from webhook.server import app
from config import WEBHOOK_PORT


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=WEBHOOK_PORT,
        log_level="info",
    )
from aiogram import Dispatcher, Router
from handlers import start, bot_create, my_bots, balance, referral, admin

router = Router()
router.include_router(start.router)
router.include_router(bot_create.router)
router.include_router(my_bots.router)
router.include_router(balance.router)
router.include_router(referral.router)
router.include_router(admin.router)

dp = Dispatcher()
dp.include_router(router)
