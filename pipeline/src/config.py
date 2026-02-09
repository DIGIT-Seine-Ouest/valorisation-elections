import os
from dotenv import load_dotenv

# Charger .env seulement en local (pas en CI/CD car GitHub Secrets est utilisé)
if os.path.exists('.env'):
    load_dotenv()


def get_api_key() -> str:
    """
    Récupère l'API key depuis les variables d'environnement.
    
    En local : lit depuis .env
    En CI/CD : lit depuis GitHub Secrets (variable d'environnement API_KEY)
    
    Returns:
        str: L'API key
        
    Raises:
        ValueError: Si l'API key n'est pas définie
    """
    api_key = os.getenv('API_KEY')
    
    if not api_key:
        raise ValueError(
            "❌ API_KEY manquante!\n"
            "- En local : créez un fichier .env avec API_KEY=votre_clé\n"
            "- En CI/CD : ajoutez API_KEY dans GitHub Secrets"
        )
    
    return api_key


def get_config() -> dict:
    """
    Retourne la configuration complète de l'application.
    
    Returns:
        dict: Configuration avec toutes les variables d'environnement
    """
    return {
        'api_key': get_api_key(),
        'base_url': os.getenv('BASE_URL', 'https://data.meudon.fr/api/explore/v2.1'),
        'timezone': os.getenv('TIMEZONE', 'Europe/Paris'),
    }
