import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(f"vehicle_ingestion_{str(int(time.time()))}.log"), logging.StreamHandler()])
LOGGER = logging.getLogger(__name__)
