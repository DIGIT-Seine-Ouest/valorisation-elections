import logging
from pathlib import Path
from datetime import datetime


def get_logger(
    name: str = __name__,
    log_dir: str = "logs",
    level: int = logging.INFO,
    max_logs: int = 2  # Garde seulement les 2 derniers fichiers
) -> logging.Logger:
    """
    Configure et retourne un logger centralisé.
    
    Crée un nouveau fichier de log à chaque exécution avec timestamp.
    Supprime automatiquement les vieux logs pour ne garder que les 2 derniers.
    
    Args:
        name: Nom du logger (généralement __name__ du module appelant)
        log_dir: Dossier où stocker les logs
        level: Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_logs: Nombre maximum de fichiers de log à conserver (défaut: 2)
    
    Returns:
        Logger configuré
    """
    # Créer le dossier logs s'il n'existe pas
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Nom du fichier avec timestamp unique
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = log_path / f"pipeline_{timestamp}.log"
    
    # Nettoyer les vieux logs (garder seulement les max_logs-1 plus récents)
    # On garde max_logs-1 car on va créer un nouveau fichier
    existing_logs = sorted(
        log_path.glob("pipeline_*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    # Supprimer les logs en trop (garder de la place pour le nouveau)
    for old_log in existing_logs[max_logs - 1:]:
        old_log.unlink()
    
    # Créer le logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Éviter les doublons si le logger existe déjà
    if logger.handlers:
        return logger
    
    # Désactiver la propagation pour éviter les logs en double
    logger.propagate = False
    
    # Format des logs
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S'
    )
    
    # Handler pour fichier (nouveau à chaque run)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Handler pour console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Ajouter les handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
    