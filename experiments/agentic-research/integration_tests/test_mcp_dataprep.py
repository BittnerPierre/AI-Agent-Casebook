"""Tests d'intégration pour le module MCP DataPrep."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
from pydantic import ValidationError

from src.dataprep.mcp_functions import download_and_store_url, upload_files_to_vectorstore, get_knowledge_entries
from src.dataprep.knowledge_db import KnowledgeDBManager
from src.dataprep.models import KnowledgeEntry, KnowledgeDatabase
from src.config import get_config


class TestMCPDataprepIntegration:
    
    @pytest.fixture
    def temp_config(self):
        """Configuration temporaire pour les tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config = get_config()
            config.data.knowledge_db_path = str(temp_path / "test_knowledge_db.json")
            config.data.local_storage_dir = str(temp_path / "data")
            yield config
    
    def test_knowledge_db_manager_basic_operations(self, temp_config):
        """Test des opérations basiques du KnowledgeDBManager."""
        db_manager = KnowledgeDBManager(temp_config.data.knowledge_db_path)
        
        # Test d'ajout d'une entrée
        entry = KnowledgeEntry(
            url="https://example.com/test",
            filename="test.md",
            title="Test Article",
            keywords=["test", "example"]
        )
        
        db_manager.add_entry(entry)
        
        # Test de recherche par URL
        found_entry = db_manager.lookup_url("https://example.com/test")
        assert found_entry is not None
        assert found_entry.filename == "test.md"
        assert found_entry.title == "Test Article"
        
        # Test de recherche par nom
        found_by_name = db_manager.find_by_name("test.md")
        assert found_by_name is not None
        assert str(found_by_name.url) == "https://example.com/test"
        
        # Test get_all_entries_info
        entries_info = db_manager.get_all_entries_info()
        assert len(entries_info) == 1
        assert entries_info[0]['filename'] == "test.md"
        assert entries_info[0]['url'] == "https://example.com/test"
    
    def test_get_knowledge_entries_empty(self, temp_config):
        """Test consultation d'une base de connaissances vide."""
        entries = get_knowledge_entries(temp_config)
        assert entries == []
    
    def test_get_knowledge_entries_with_data(self, temp_config):
        """Test consultation avec données existantes."""
        # Préparer des données de test
        db_manager = KnowledgeDBManager(temp_config.data.knowledge_db_path)
        
        entries_data = [
            KnowledgeEntry(
                url="https://example.com/ai-article",
                filename="ai_article.md",
                title="AI Article",
                keywords=["AI", "Machine Learning"],
                openai_file_id="file_123"
            ),
            KnowledgeEntry(
                url="https://example.com/python-guide",
                filename="python_guide.md", 
                title="Python Guide",
                keywords=["Python", "Programming"]
            )
        ]
        
        for entry in entries_data:
            db_manager.add_entry(entry)
        
        # Test
        entries = get_knowledge_entries(temp_config)
        
        assert len(entries) == 2
        
        # Vérifier les données
        ai_entry = next(e for e in entries if e['filename'] == 'ai_article.md')
        assert ai_entry['title'] == "AI Article"
        assert ai_entry['openai_file_id'] == "file_123"
        assert "AI" in ai_entry['keywords']
        
        python_entry = next(e for e in entries if e['filename'] == 'python_guide.md')
        assert python_entry['title'] == "Python Guide"
        assert python_entry['openai_file_id'] is None
    
    @patch('src.dataprep.mcp_functions.load_documents_from_urls')
    @patch('src.dataprep.mcp_functions._extract_keywords_with_llm')
    def test_download_and_store_url_new_document(self, mock_extract_llm, mock_load, temp_config):
        """Test téléchargement d'un nouveau document."""
        # Mock de l'extraction LLM
        mock_extract_llm.return_value = ["AI", "Machine Learning", "Neural Networks"]
        
        # Mock du téléchargement
        mock_doc = Mock()
        mock_doc.page_content = "Contenu de test sur l'intelligence artificielle"
        mock_doc.metadata = {'title': 'Test AI Article', 'source': 'https://example.com/test-article'}
        mock_load.return_value = [mock_doc]
        
        url = "https://example.com/test-article"
        filename = download_and_store_url(url, temp_config)
        
        # Vérifications
        assert filename.endswith('.md')
        assert 'Test_AI_Article' in filename
        
        # Vérifier que le fichier existe
        local_path = Path(temp_config.data.local_storage_dir) / filename
        assert local_path.exists()
        
        # Vérifier le contenu du fichier
        content = local_path.read_text(encoding='utf-8')
        assert "Test AI Article" in content
        assert "Contenu de test sur l'intelligence artificielle" in content
        
        # Vérifier l'entrée dans la base
        db_manager = KnowledgeDBManager(temp_config.data.knowledge_db_path)
        entry = db_manager.lookup_url(url)
        assert entry is not None
        assert entry.filename == filename
        assert entry.title == "Test AI Article"
        assert "AI" in entry.keywords
        assert "Machine Learning" in entry.keywords
    
    @patch('src.dataprep.mcp_functions.load_documents_from_urls')
    def test_download_and_store_url_existing_document(self, mock_load, temp_config):
        """Test lookup d'un document existant."""
        url = "https://example.com/existing-article"
        
        # Pré-remplir la base
        db_manager = KnowledgeDBManager(temp_config.data.knowledge_db_path)
        existing_entry = KnowledgeEntry(
            url=url,
            filename="existing_article.md",
            keywords=["test"],
            title="Existing Article"
        )
        db_manager.add_entry(existing_entry)
        
        # Créer le fichier correspondant
        local_dir = Path(temp_config.data.local_storage_dir)
        local_dir.mkdir(parents=True, exist_ok=True)
        (local_dir / "existing_article.md").write_text("Contenu existant")
        
        # Test - ne devrait pas appeler load_documents_from_urls
        filename = download_and_store_url(url, temp_config)
        
        # Vérification
        assert filename == "existing_article.md"
        mock_load.assert_not_called()  # Pas de nouveau téléchargement
    
    def test_knowledge_database_model_validation(self):
        """Test validation des modèles Pydantic."""
        # Test KnowledgeEntry valide
        entry = KnowledgeEntry(
            url="https://example.com/test",
            filename="test.md",
            keywords=["test"]
        )
        assert str(entry.url) == "https://example.com/test"
        assert entry.filename == "test.md"
        assert entry.keywords == ["test"]
        
        # Test KnowledgeEntry avec URL invalide
        with pytest.raises(ValidationError):
            KnowledgeEntry(
                url="invalid-url",
                filename="test.md"
            )
        
        # Test KnowledgeDatabase
        db = KnowledgeDatabase()
        assert len(db.entries) == 0
        assert db.version == "1.0"
        
        db.add_entry(entry)
        assert len(db.entries) == 1
        
        # Test find_by_url et find_by_name
        found = db.find_by_url("https://example.com/test")
        assert found is not None
        assert found.filename == "test.md"
        
        found_by_name = db.find_by_name("test.md")
        assert found_by_name is not None
        assert str(found_by_name.url) == "https://example.com/test"


if __name__ == "__main__":
    pytest.main([__file__]) 