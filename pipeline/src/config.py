import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
def get_api_key():
    load_dotenv()
    apikey = os.getenv('api_key')
    
    return apikey