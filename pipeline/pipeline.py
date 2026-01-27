import json
import pandas as pd

# Chargement des données avec les bonnes colonnes
def load_eirel(filepath, config_path: str='pipeline/data/bronze/reference/eirel_columns.json'):
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

    return data

# Chargement des donnée 
def process_eirel(
    eirel_path: str = "pipeline/data/bronze/eirel/Eirel-testMunicipales-nov2025-1erTour.txt", 
    columns_repartition: str ="pipeline/data/bronze/reference/columns_repartition.json"):

    data = load_eirel(eirel_path)
    with open(columns_repartition) as config_cols:
        cols_used = json.load(config_cols)

    data[cols_used["metrics_bdv"]].to_csv("pipeline/data/silver/bdv_metrics.csv", index=False)
    data[cols_used["candidats_voix"]].to_csv("pipeline/data/silver/candidats_metrics.csv", index=False)



def enrich_eirel():
    # Données d'enrichissement --> 
    data = pd.read_csv("pipeline/data/silver/bdv_metrics.csv")
    data_candidates = pd.read_csv("pipeline/data/silver/candidats_metrics.csv")
    bdv = pd.read_csv(
        "https://data.meudon.fr/api/explore/v2.1/catalog/datasets/bureaux-de-vote-electoraux-2026/exports/csv", 
        sep=";",
        usecols=["num_bureau", "nom_bureau"]
    )

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


if __name__ == "__main__":
    process_eirel()
    enrich_eirel()
