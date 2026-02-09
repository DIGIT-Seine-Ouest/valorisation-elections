from src.utils import get_logger
from src.ingestion import ingest_eirel
from src.processing import process_eirel
from src.enrichment import enrich_eirel
from src.config import get_api_key

# Récupération du logger
logger = get_logger(__name__)

# Lancement de la pipeline
if __name__ == "__main__":
    logger.info("=== START PIPELINE ===")
    api_key = get_api_key()
    ingest_eirel(api_key=api_key)
    process_eirel()
    enrich_eirel()
    logger.info("=== END PIPELINE ===")
