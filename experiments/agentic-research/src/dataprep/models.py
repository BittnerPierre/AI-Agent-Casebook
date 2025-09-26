"""Modèles de données pour la base de connaissances locale."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_serializer


class KnowledgeEntry(BaseModel):
    """Entrée dans la base de connaissances."""

    url: HttpUrl = Field(..., description="URL source du document")
    filename: str = Field(..., description="Nom du fichier .md stocké localement")
    keywords: list[str] = Field(default_factory=list, description="Mots-clés extraits par LLM")
    summary: str | None = Field(None, description="Résumé du document généré par LLM")
    title: str | None = Field(None, description="Titre du document")
    content_length: int = Field(0, description="Taille du contenu en caractères")
    openai_file_id: str | None = Field(None, description="ID du fichier dans OpenAI Files API")
    created_at: datetime = Field(default_factory=datetime.now)
    last_uploaded_at: datetime | None = Field(
        None, description="Dernière date d'upload vers OpenAI"
    )

    # Serializers Pydantic v2 pour remplacer json_encoders
    @field_serializer("created_at", "last_uploaded_at")
    def serialize_datetime(self, dt: datetime | None) -> str | None:
        return dt.isoformat() if dt else None

    @field_serializer("url")
    def serialize_url(self, url: HttpUrl) -> str:
        return str(url)


class KnowledgeDatabase(BaseModel):
    """Structure de la base de connaissances complète."""

    entries: list[KnowledgeEntry] = Field(default_factory=list)
    version: str = Field(default="1.0")
    last_updated: datetime = Field(default_factory=datetime.now)

    # Serializer pour last_updated
    @field_serializer("last_updated")
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()

    def find_by_url(self, url: str) -> KnowledgeEntry | None:
        """Recherche d'une entrée par URL."""
        for entry in self.entries:
            if str(entry.url) == url:
                return entry
        return None

    def find_by_name(self, filename: str) -> KnowledgeEntry | None:
        """Recherche d'une entrée par nom de fichier."""
        for entry in self.entries:
            if entry.filename == filename:
                return entry
        return None

    def add_entry(self, entry: KnowledgeEntry) -> None:
        """Ajout d'une nouvelle entrée."""
        # Supprimer l'ancienne entrée si elle existe
        self.entries = [e for e in self.entries if str(e.url) != str(entry.url)]
        self.entries.append(entry)
        self.last_updated = datetime.now()

    def update_openai_file_id(self, filename: str, openai_file_id: str) -> None:
        """Met à jour l'ID OpenAI d'une entrée."""
        for entry in self.entries:
            if entry.filename == filename:
                entry.openai_file_id = openai_file_id
                entry.last_uploaded_at = datetime.now()
                self.last_updated = datetime.now()
                break


class UploadResult(BaseModel):
    """Résultat d'upload vers vector store."""

    vectorstore_id: str = Field(..., description="ID du vector store OpenAI")
    files_uploaded: list[dict] = Field(..., description="Fichiers uploadés vers OpenAI Files API")
    files_attached: list[dict] = Field(..., description="Fichiers attachés au vector store")
    total_files_requested: int = Field(..., description="Nombre total de fichiers demandés")
    upload_count: int = Field(default=0, description="Nombre de nouveaux uploads vers Files API")
    reuse_count: int = Field(
        default=0, description="Nombre de fichiers réutilisés (déjà sur OpenAI)"
    )
    attach_success_count: int = Field(
        default=0, description="Nombre de fichiers attachés avec succès"
    )
    attach_failure_count: int = Field(default=0, description="Nombre d'échecs d'attachement")
