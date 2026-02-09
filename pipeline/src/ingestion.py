import logging
import requests
from .utils import get_logger

logger = get_logger(__name__)

# Ingestion des données EIREL
def ingest_eirel(
    url: str = "https://data.meudon.fr/api/explore/v2.1/catalog/datasets/raw-eirel-municipale/exports/csv",
    api_key: str = ""
    ):

    headers = {
        "Authorization": f"Apikey {api_key}"
    }
    params = {
        "limit": -1,
        "delimiter": ";",
        "timezone": "Europe/Paris"
    }

    # Récupérer les données
    try:
        logging.info("Récupération des fichiers EIREL depuis data.meudon.fr")
        response = requests.get(url, headers=headers, params=params)
        with open("data/bronze/eirel/raw-eirel-municipale.txt", "w") as f:
            f.write(response.text)
        logger.info("Dossier chargé dans : data/bronze/eirel/raw-eirel-municipale.txt")
    except Exception as e:
        logger.warning(f"Erreur dans la récupération des données. Détail : {e}")
