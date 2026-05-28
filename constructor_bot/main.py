import logging
import sys
import uvicorn

# 1. Logging sozlash (Har doim eng tepada turishi kerak)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

# 2. Server va konfiguratsiyani import qilish
from webhook.server import app
from config import WEBHOOK_PORT

# 3. Serverni ishga tushirish
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=WEBHOOK_PORT,
        log_level="info",
    )
