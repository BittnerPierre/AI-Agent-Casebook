"""Gestionnaire thread-safe pour la base de connaissances locale."""

import json
import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import portalocker

from .models import KnowledgeDatabase, KnowledgeEntry

logger = logging.getLogger(__name__)


class KnowledgeDBManager:
    """Gestionnaire thread-safe pour la base de connaissances locale."""

    _instance = None
    _url_index = {}  # Index par URL (transient)
    _name_index = {}  # Index par nom de fichier (transient)

    def __new__(cls, db_path: Path = None):
        """Implémentation du pattern Singleton."""
        if cls._instance is None:
            cls._instance = super(KnowledgeDBManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Path = None):
        """Initialisation (une seule fois)."""
        if not hasattr(self, "_initialized") or not self._initialized:
            if db_path is None:
                try:
                    from ..config import get_config

                    config = get_config()
                    db_path = Path(config.data.knowledge_db_path)
                except Exception as e:
                    logger.warning(
                        f"Impossible de charger la config: {e}. Utilisation du chemin par défaut."
                    )
                    db_path = Path("data/knowledge_db.json")

            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._initialized = True
            self._build_indexes()

    def _build_indexes(self):
        """Construit les index en mémoire pour accès rapide."""
        try:
            db = self.get_all_entries()
            self._url_index = {str(entry.url): entry for entry in db.entries}
            self._name_index = {entry.filename: entry for entry in db.entries}
            logger.info(f"Index construits: {len(self._url_index)} entrées indexées")
        except Exception as e:
            logger.warning(f"Erreur lors de la construction des index: {e}")
            self._url_index = {}
            self._name_index = {}

    @contextmanager
    def _file_lock(self, mode="r+"):
        """Context manager pour verrouillage de fichier."""
        if not self.db_path.exists() and "r" in mode:
            # Créer le fichier vide si il n'existe pas
            self._initialize_empty_db()

        with open(self.db_path, mode, encoding="utf-8") as f:
            try:
                portalocker.lock(f, portalocker.LOCK_EX)
                yield f
            finally:
                portalocker.unlock(f)

    def _initialize_empty_db(self) -> None:
        """Initialise une base de données vide."""
        empty_db = KnowledgeDatabase()
        # S'assurer que le répertoire parent existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as f:
            f.write(empty_db.model_dump_json(indent=2))

    def lookup_url(self, url: str) -> KnowledgeEntry | None:
        """Recherche d'une URL dans la base de connaissances (via index)."""
        # Utiliser l'index en mémoire pour recherche rapide
        if url in self._url_index:
            return self._url_index[url]

        # Fallback sur recherche dans le fichier
        try:
            with self._file_lock("r") as f:
                data = json.load(f)
                db = KnowledgeDatabase(**data)
                entry = db.find_by_url(url)
                if entry:
                    # Mettre à jour l'index
                    self._url_index[url] = entry
                return entry
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Erreur lors de la lecture de la base: {e}")
            return None

    def find_by_name(self, filename: str) -> KnowledgeEntry | None:
        """Recherche d'une entrée par nom de fichier (via index)."""
        # Utiliser l'index en mémoire
        if filename in self._name_index:
            return self._name_index[filename]

        # Fallback sur recherche dans le fichier
        try:
            with self._file_lock("r") as f:
                data = json.load(f)
                db = KnowledgeDatabase(**data)
                entry = db.find_by_name(filename)
                if entry:
                    # Mettre à jour l'index
                    self._name_index[filename] = entry
                return entry
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Erreur lors de la recherche par nom: {e}")
            return None

    def add_entry(self, entry: KnowledgeEntry) -> None:
        """Ajout thread-safe d'une entrée (pattern: read -> merge -> write)."""
        with self._file_lock("r+") as f:
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

        # Mettre à jour les index
        self._url_index[str(entry.url)] = entry
        self._name_index[entry.filename] = entry

        logger.info(f"Entrée ajoutée à la base de connaissances: {entry.filename}")

    def update_openai_file_id(self, filename: str, openai_file_id: str) -> None:
        """Met à jour l'ID OpenAI Files d'une entrée de manière thread-safe."""
        with self._file_lock("r+") as f:
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

        # Mettre à jour l'entrée dans l'index
        if filename in self._name_index:
            self._name_index[filename].openai_file_id = openai_file_id
            self._name_index[filename].last_uploaded_at = datetime.now()

        logger.info(f"ID OpenAI mis à jour pour {filename}: {openai_file_id}")

    def get_all_entries_info(self) -> list[dict[str, Any]]:
        """Retourne la liste de toutes les entrées de la base de connaissances."""
        try:
            with self._file_lock("r") as f:
                data = json.load(f)
                db = KnowledgeDatabase(**data)

                entries_info = []
                for entry in db.entries:
                    entries_info.append(
                        {
                            "url": str(entry.url),
                            "filename": entry.filename,
                            "title": entry.title,
                            "keywords": entry.keywords,
                            "summary": entry.summary,
                            "openai_file_id": entry.openai_file_id,
                        }
                    )

                return entries_info

        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def get_all_entries(self) -> KnowledgeDatabase:
        """Récupération de toutes les entrées."""
        try:
            with self._file_lock("r") as f:
                data = json.load(f)
                return KnowledgeDatabase(**data)
        except (FileNotFoundError, json.JSONDecodeError):
            return KnowledgeDatabase()
