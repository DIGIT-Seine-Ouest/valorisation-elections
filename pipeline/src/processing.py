import json
import pandas as pd
from .utils import get_logger

logger = get_logger(__name__)

# Chargement des données avec les bonnes colonnes
def load_eirel(filepath, config_path: str='data/bronze/reference/eirel_columns.json'):
    logger.info("Récupération des données EIREL...")
    with open(config_path, 'r') as f:
        config = json.load(f)

    colonnes = {int(k): v for k, v in config['fixed_columns'].items()}

    temp = pd.read_csv(filepath, sep=";", header=None, usecols=[17], nrows=1)
    nb_listes = temp.iloc[0, 0]

    start_idx = config['dynamic_columns']['start_index']
    for i in range(1, nb_listes + 1):
        colonnes[start_idx + 2*(i-1)] = f"code_liste_{i}"
        colonnes[start_idx + 2*(i-1) + 1] = f"voix_liste_{i}"

    data = pd.read_csv(filepath, sep=";", header=None)
    data.rename(columns=colonnes, inplace=True)
    logger.info(data.bureau_vote.nunique())
    logger.info("EIREL récupéré avec succès.")

    return data

# Chargement des données 
def process_eirel(
    eirel_path: str = "data/bronze/eirel/raw-eirel-municipale.txt", 
    columns_repartition: str ="data/bronze/reference/columns_repartition.json"):
    logger.info("Traitement EIREL...")
    data = load_eirel(eirel_path)
    with open(columns_repartition) as config_cols:
        cols_used = json.load(config_cols)

    data[cols_used["metrics_bdv"]].to_csv("data/silver/bdv_metrics.csv", index=False)
    data[cols_used["candidats_voix"]].to_csv("data/silver/candidats_metrics.csv", index=False)
    logger.info("EIREL traité avec succès.")
