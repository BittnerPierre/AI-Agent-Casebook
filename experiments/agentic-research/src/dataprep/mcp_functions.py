"""Fonctions MCP pour la gestion de la base de connaissances et upload vers vector store."""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI
from datetime import datetime

from .knowledge_db import KnowledgeDBManager
from .models import KnowledgeEntry, UploadResult
from .web_loader_improved import load_documents_from_urls
from ..vector_store_manager import VectorStoreManager
from ..config import get_config

logger = logging.getLogger(__name__)


def download_and_store_url(url: str, config) -> str:
    """
    MCP Function 1: Téléchargement et stockage avec lookup dans la base de connaissances
    
    Args:
        url: URL à télécharger
        config: Configuration du système
        
    Returns:
        str: Nom du fichier local (.md)
    """
    # 1. Lookup dans knowledge_db.json
    db_manager = KnowledgeDBManager(config.data.knowledge_db_path)
    existing_entry = db_manager.lookup_url(url)
    
    if existing_entry:
        logger.info(f"URL trouvée dans la base de connaissances: {existing_entry.filename}")
        # Vérifier que le fichier existe encore
        local_path = Path(config.data.local_storage_dir) / existing_entry.filename
        if local_path.exists():
            return existing_entry.filename
        else:
            logger.warning(f"Fichier manquant, re-téléchargement: {existing_entry.filename}")
    
    # 2. Télécharger et convertir
    logger.info(f"Téléchargement de l'URL: {url}")
    docs_list = load_documents_from_urls([url])
    
    if not docs_list:
        raise ValueError(f"Impossible de télécharger le contenu de: {url}")
    
    doc = docs_list[0]
    
    # 3. Générer nom de fichier unique
    title = doc.metadata.get('title', 'document')
    safe_title = re.sub(r'[^a-zA-Z0-9_.-]', '_', title[:50])
    filename = f"{safe_title}.md"
    
    # Éviter les collisions de noms
    local_dir = Path(config.data.local_storage_dir)
    local_dir.mkdir(parents=True, exist_ok=True)
    counter = 1
    original_filename = filename
    while (local_dir / filename).exists():
        name, ext = original_filename.rsplit('.', 1)
        filename = f"{name}_{counter}.{ext}"
        counter += 1
    
    # 4. Sauvegarder le fichier .md
    local_path = local_dir / filename
    markdown_content = _format_document_as_markdown(doc)
    
    with open(local_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    # 5. Extraire mots-clés avec LLM
    keywords = _extract_keywords_with_llm(doc, config)
    
    # 6. Ajouter à la base de connaissances
    entry = KnowledgeEntry(
        url=url,
        filename=filename,
        keywords=keywords,
        title=doc.metadata.get('title'),
        content_length=len(doc.page_content)
        # openai_file_id sera ajouté lors de l'upload
    )
    
    db_manager.add_entry(entry)
    
    logger.info(f"Document sauvegardé: {filename}")
    return filename


def upload_files_to_vectorstore(
    inputs: List[str], 
    config, 
    vectorstore_name: str
) -> UploadResult:
    """
    MCP Function 2: Upload optimisé vers vector store OpenAI
    
    Logic:
    - Si input est URL -> lookup par URL
    - Si input est filename -> lookup par nom
    - Si entrée a déjà openai_file_id -> réutiliser
    - Sinon -> upload vers Files API puis sauvegarder l'ID
    
    Args:
        inputs: Liste d'URLs ou noms de fichiers
        config: Configuration
        vectorstore_name: Nom du vector store
        
    Returns:
        UploadResult: Résultat détaillé de l'opération
    """
    db_manager = KnowledgeDBManager(config.data.knowledge_db_path)
    local_dir = Path(config.data.local_storage_dir)
    client = OpenAI()
    
    # 1. Résolution inputs → KnowledgeEntry
    entries_to_process = []
    
    for input_item in inputs:
        entry = None
        
        if input_item.startswith(('http://', 'https://')):
            # C'est une URL
            entry = db_manager.lookup_url(input_item)
            if not entry:
                raise ValueError(f"URL non trouvée dans la base de connaissances: {input_item}")
        else:
            # C'est un nom de fichier
            entry = db_manager.find_by_name(input_item)
            if not entry:
                raise ValueError(f"Fichier non trouvé dans la base de connaissances: {input_item}")
        
        # Vérifier que le fichier local existe
        file_path = local_dir / entry.filename
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier local non trouvé: {file_path}")
        
        entries_to_process.append((entry, file_path))
    
    # 2. Créer vector store avec expiration 1 jour
    vector_store_response = client.vector_stores.create(
        name=vectorstore_name,
        expires_after={"anchor": "last_active_at", "days": 1}
    )
    
    vectorstore_id = vector_store_response.id
    logger.info(f"Vector store créé: {vectorstore_id}")
    
    # 3. Traitement des fichiers (upload si nécessaire)
    files_uploaded = []
    files_to_attach = []  # (file_id, filename)
    upload_count = 0
    reuse_count = 0
    
    for entry, file_path in entries_to_process:
        if entry.openai_file_id:
            # Fichier déjà uploadé, réutiliser
            logger.info(f"Réutilisation du fichier OpenAI existant: {entry.filename} -> {entry.openai_file_id}")
            files_uploaded.append({
                'filename': entry.filename,
                'file_id': entry.openai_file_id,
                'status': 'reused'
            })
            files_to_attach.append((entry.openai_file_id, entry.filename))
            reuse_count += 1
        else:
            # Nouveau fichier, upload nécessaire
            try:
                logger.info(f"Upload du nouveau fichier: {entry.filename}")
                with open(file_path, 'rb') as file:
                    file_upload_response = client.files.create(
                        file=file,
                        purpose='user_data'
                    )
                
                file_id = file_upload_response.id
                
                # Mettre à jour la base de connaissances avec l'ID OpenAI
                db_manager.update_openai_file_id(entry.filename, file_id)
                
                files_uploaded.append({
                    'filename': entry.filename,
                    'file_id': file_id,
                    'status': 'uploaded'
                })
                files_to_attach.append((file_id, entry.filename))
                upload_count += 1
                
            except Exception as e:
                logger.error(f"Erreur upload {entry.filename}: {e}")
                files_uploaded.append({
                    'filename': entry.filename,
                    'error': str(e),
                    'status': 'failed'
                })
    
    # 4. Attachement au vector store
    files_attached = []
    attach_success_count = 0
    attach_failure_count = 0
    
    for file_id, filename in files_to_attach:
        try:
            vector_store_file = client.vector_stores.files.create(
                vector_store_id=vectorstore_id,
                file_id=file_id
            )
            
            # Attendre traitement
            while vector_store_file.status == 'in_progress':
                import time
                time.sleep(1)
                vector_store_file = client.vector_stores.files.retrieve(
                    vector_store_id=vectorstore_id,
                    file_id=file_id
                )
            
            if vector_store_file.status == 'completed':
                files_attached.append({
                    'filename': filename,
                    'file_id': file_id,
                    'vector_store_file_id': vector_store_file.id,
                    'status': 'attached'
                })
                attach_success_count += 1
                logger.info(f"Fichier attaché avec succès: {filename}")
            else:
                raise Exception(f"Échec de l'attachement. Status: {vector_store_file.status}")
                
        except Exception as e:
            logger.error(f"Erreur attachement {filename}: {e}")
            files_attached.append({
                'filename': filename,
                'file_id': file_id,
                'error': str(e),
                'status': 'attach_failed'
            })
            attach_failure_count += 1
    
    return UploadResult(
        vectorstore_id=vectorstore_id,
        files_uploaded=files_uploaded,
        files_attached=files_attached,
        total_files_requested=len(inputs),
        upload_count=upload_count,
        reuse_count=reuse_count,
        attach_success_count=attach_success_count,
        attach_failure_count=attach_failure_count
    )


def get_knowledge_entries(config) -> List[Dict[str, Any]]:
    """
    MCP Function 3: Accès à l'index de la base de connaissances
    
    Args:
        config: Configuration du système
        
    Returns:
        List[Dict]: Liste des entrées disponibles
    """
    db_manager = KnowledgeDBManager(config.data.knowledge_db_path)
    return db_manager.get_all_entries_info()


def _extract_keywords_with_llm(doc, config) -> List[str]:
    """Extraction de mots-clés intelligente avec LLM."""
    client = OpenAI()
    
    # Limiter le contenu pour l'analyse
    content_preview = doc.page_content[:2000] + "..." if len(doc.page_content) > 2000 else doc.page_content
    title = doc.metadata.get('title', 'Document sans titre')
    
    prompt = f"""Analyse ce document et extrais 5-10 mots-clés pertinents qui résument le contenu principal.

Titre: {title}

Contenu:
{content_preview}

Retourne uniquement une liste de mots-clés séparés par des virgules, sans numérotation ni explication.
Concentre-toi sur les concepts techniques, les noms propres, et les thèmes principaux."""
    
    try:
        response = client.chat.completions.create(
            model=config.openai.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        keywords_text = response.choices[0].message.content.strip()
        keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
        
        logger.info(f"Mots-clés extraits par LLM: {keywords}")
        return keywords[:10]  # Limiter à 10 mots-clés
        
    except Exception as e:
        logger.error(f"Erreur extraction mots-clés LLM: {e}")
        # Fallback sur extraction basique
        return _extract_keywords_basic(doc)


def _extract_keywords_basic(doc) -> List[str]:
    """Extraction basique de mots-clés (fallback)."""
    keywords = []
    
    # Titre
    if doc.metadata.get('title'):
        keywords.append(doc.metadata['title'])
    
    # Premiers mots du contenu
    words = doc.page_content.split()[:50]
    # Filtrer et garder mots significatifs (longueur > 3)
    significant_words = [w.strip('.,!?;:') for w in words if len(w) > 3]
    keywords.extend(significant_words[:10])
    
    return list(set(keywords))  # Dédupliquer


def _format_document_as_markdown(doc) -> str:
    """Formate un document en markdown avec métadonnées."""
    # Réutiliser la logique existante de core.py
    from .core import format_document_as_markdown
    return format_document_as_markdown(doc) 