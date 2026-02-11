import json
import pandas as pd
from .utils import get_logger

logger = get_logger(__name__)

def enrich_eirel():
    logger.info("Enrichissement des données...")
    data = pd.read_csv("data/silver/bdv_metrics.csv")
    data_candidates = pd.read_csv("data/silver/candidats_metrics.csv")
    bdv = pd.read_csv(
        "https://data.meudon.fr/api/explore/v2.1/catalog/datasets/bureaux-de-vote-electoraux-2026/exports/csv", 
        sep=";",
        usecols=["num_bureau", "nom_bureau"]
    )
    quartier = pd.read_csv("data/bronze/reference/join_cq.csv")

    logger.info("Jointure avec les bureaux de vote...")
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
    
    merged_data = merged_data.merge(
        quartier,
        left_on="bureau_vote",
        right_on="num_bureau",
        how="left"
    )

    merged_data["num_bureau"] = merged_data["num_bureau_x"]
    merged_data.drop(columns=['num_bureau_x', 'num_bureau_y'], inplace=True)


    # Ajouter les noms de candidats
    logger.info("Ajout des noms de candidat")
    with open("data/bronze/reference/nom_candidat.json") as config_cols:
        candidate_map = json.load(config_cols)
    
    merged_data = merged_data.rename(columns=candidate_map)


    merged_data.to_csv("data/gold/election_2026.csv", index=False)
    logger.info("Enrichissement fait avec succès.")
