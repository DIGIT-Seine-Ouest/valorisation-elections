import os
import json
import logging
import requests
import pandas as pd
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()
apikey = os.getenv('api_key')

# Gestion des logs
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="log_recuperation_election.log", 
    encoding="utf-8", 
    level=logging.INFO, 
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt='%d/%m/%Y %H:%M:%S'
)

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
        with open("pipeline/data/bronze/eirel/raw-eirel-municipale.txt", "w") as f:
            f.write(response.text)
        logging.info("Dossier chargé dans : data/bronze/eirel/raw-eirel-municipale.txt")
    except Exception as e:
        logging.warning(f"Erreur dans la récupération des données. Détail : {e}")


# Chargement des données avec les bonnes colonnes
def load_eirel(filepath, config_path: str='pipeline/data/bronze/reference/eirel_columns.json'):
    logging.info("Récupération des données EIREL...")
    with open(config_path, 'r') as f:
        config = json.load(f)

    colonnes = {int(k): v for k, v in config['fixed_columns'].items()}

    temp = pd.read_csv(filepath, sep=";", skiprows=2, header=None, usecols=[17], nrows=1)
    nb_listes = temp.iloc[0, 0]

    start_idx = config['dynamic_columns']['start_index']
    for i in range(1, nb_listes + 1):
        colonnes[start_idx + 2*(i-1)] = f"code_liste_{i}"
        colonnes[start_idx + 2*(i-1) + 1] = f"voix_liste_{i}"

    data = pd.read_csv(filepath, sep=";", skiprows=2, header=None)
    data.rename(columns=colonnes, inplace=True)
    logging.info("EIREL récupéré avec succès.")

    return data

# Chargement des donnée 
def process_eirel(
    eirel_path: str = "pipeline/data/bronze/eirel/raw-eirel-municipale.txt", 
    columns_repartition: str ="pipeline/data/bronze/reference/columns_repartition.json"):
    logging.info("Traitement EIREL...")
    data = load_eirel(eirel_path)
    with open(columns_repartition) as config_cols:
        cols_used = json.load(config_cols)

    data[cols_used["metrics_bdv"]].to_csv("pipeline/data/silver/bdv_metrics.csv", index=False)
    data[cols_used["candidats_voix"]].to_csv("pipeline/data/silver/candidats_metrics.csv", index=False)
    logging.info("EIREL traité avec succès.")



def enrich_eirel():
    logging.info("Enrichissement des données...")
    data = pd.read_csv("pipeline/data/silver/bdv_metrics.csv")
    data_candidates = pd.read_csv("pipeline/data/silver/candidats_metrics.csv")
    bdv = pd.read_csv(
        "https://data.meudon.fr/api/explore/v2.1/catalog/datasets/bureaux-de-vote-electoraux-2026/exports/csv", 
        sep=";",
        usecols=["num_bureau", "nom_bureau"]
    )

    logging.info("Jointure avec les bureaux de vote...")
    nom_bureau = data.merge(
        bdv, 
        left_on="bureau_vote", 
        right_on="num_bureau", 
        how="left"
    )

    merged_data = nom_bureau.merge(
        data_candidates,
        left_on="bureau_vote",
        right_on="bureau_vote",
        how="left"
    )

    merged_data.to_csv("pipeline/data/gold/election_2025.csv", index=False)
    logging.info("Enrichissement fait avec succès.")

# Lancement de la pipeline
if __name__ == "__main__":
    logger.info("=== START PIPELINE ===")
    ingest_eirel(api_key=apikey)
    process_eirel()
    enrich_eirel()
    logger.info("=== END PIPELINE ===")
