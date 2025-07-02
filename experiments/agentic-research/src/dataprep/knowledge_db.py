"""Gestionnaire thread-safe pour la base de connaissances locale."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import portalocker
from contextlib import contextmanager

from .models import KnowledgeDatabase, KnowledgeEntry

logger = logging.getLogger(__name__)


class KnowledgeDBManager:
    """Gestionnaire thread-safe pour la base de connaissances locale."""
    
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    @contextmanager
    def _file_lock(self, mode='r+'):
        """Context manager pour verrouillage de fichier."""
        if not self.db_path.exists() and 'r' in mode:
            # Créer le fichier vide si il n'existe pas
            self._initialize_empty_db()
            
        with open(self.db_path, mode, encoding='utf-8') as f:
            try:
                portalocker.lock(f, portalocker.LOCK_EX)
                yield f
            finally:
                portalocker.unlock(f)
    
    def _initialize_empty_db(self) -> None:
        """Initialise une base de données vide."""
        empty_db = KnowledgeDatabase()
        with open(self.db_path, 'w', encoding='utf-8') as f:
            f.write(empty_db.model_dump_json(indent=2))
    
    def lookup_url(self, url: str) -> Optional[KnowledgeEntry]:
        """Recherche d'une URL dans la base de connaissances."""
        try:
            with self._file_lock('r') as f:
                data = json.load(f)
                db = KnowledgeDatabase(**data)
                return db.find_by_url(url)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Erreur lors de la lecture de la base: {e}")
            return None
    
    def find_by_name(self, filename: str) -> Optional[KnowledgeEntry]:
        """Recherche d'une entrée par nom de fichier."""
        try:
            with self._file_lock('r') as f:
                data = json.load(f)
                db = KnowledgeDatabase(**data)
                return db.find_by_name(filename)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Erreur lors de la recherche par nom: {e}")
            return None
    
    def add_entry(self, entry: KnowledgeEntry) -> None:
        """Ajout thread-safe d'une entrée (pattern: read -> merge -> write)."""
        with self._file_lock('r+') as f:
            try:
                # Lecture
                f.seek(0)
                data = json.load(f)
                db = KnowledgeDatabase(**data)
            except (json.JSONDecodeError, ValueError):
                # Fichier corrompu, créer nouveau
                db = KnowledgeDatabase()
            
            # Merge
            db.add_entry(entry)
            
            # Write
            f.seek(0)
            f.truncate()
            f.write(db.model_dump_json(indent=2))
            
        logger.info(f"Entrée ajoutée à la base de connaissances: {entry.filename}")
    
    def update_openai_file_id(self, filename: str, openai_file_id: str) -> None:
        """Met à jour l'ID OpenAI Files d'une entrée de manière thread-safe."""
        with self._file_lock('r+') as f:
            try:
                f.seek(0)
                data = json.load(f)
                db = KnowledgeDatabase(**data)
            except (json.JSONDecodeError, ValueError):
                logger.error(f"Impossible de lire la base pour mise à jour: {filename}")
                return
            
            # Mise à jour
            db.update_openai_file_id(filename, openai_file_id)
            
            # Write
            f.seek(0)
            f.truncate()
            f.write(db.model_dump_json(indent=2))
            
        logger.info(f"ID OpenAI mis à jour pour {filename}: {openai_file_id}")
    
    def get_all_entries_info(self) -> List[Dict[str, Any]]:
        """Retourne la liste de toutes les entrées de la base de connaissances."""
        try:
            with self._file_lock('r') as f:
                data = json.load(f)
                db = KnowledgeDatabase(**data)
                
                entries_info = []
                for entry in db.entries:
                    entries_info.append({
                        "url": str(entry.url),
                        "filename": entry.filename,
                        "title": entry.title,
                        "keywords": entry.keywords,
                        "openai_file_id": entry.openai_file_id
                    })
                
                return entries_info
                
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def get_all_entries(self) -> KnowledgeDatabase:
        """Récupération de toutes les entrées."""
        try:
            with self._file_lock('r') as f:
                data = json.load(f)
                return KnowledgeDatabase(**data)
        except (FileNotFoundError, json.JSONDecodeError):
            return KnowledgeDatabase() 