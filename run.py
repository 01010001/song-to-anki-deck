import os
import logging
from app import create_app

app = create_app()
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    logger.info("Sunucu başlatılıyor: http://127.0.0.1:%s", port)
    logger.info("Komut satırında [DEBUG] satırlarını takip edin.")
    app.run(debug=True, port=port, use_reloader=True)
