#!/bin/bash
# Script simplifié pour inspecter le vector store

set -e  # Exit on error

echo "🔍 Vector Store Inspector"
echo "========================"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "config.yaml" ]; then
    echo "❌ Erreur: Lancez ce script depuis le dossier agentic-research"
    exit 1
fi

# Vérifier que OPENAI_API_KEY est définie
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Erreur: La variable OPENAI_API_KEY n'est pas définie"
    echo "   Ajoutez: export OPENAI_API_KEY=your_api_key"
    exit 1
fi

# Créer le dossier scripts s'il n'existe pas
mkdir -p scripts

# Fonction d'aide
show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  list        Lister les fichiers du vector store seulement"
    echo "  download    Télécharger tout le contenu (défaut)"
    echo "  help        Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0                    # Télécharger tout"
    echo "  $0 list              # Lister seulement"
    echo "  $0 download          # Télécharger tout"
}

# Parser les arguments
case "${1:-download}" in
    "list")
        echo "📋 Listing files only..."
        poetry run inspect_vector_store --list-only
        ;;
    "download")
        echo "⬇️  Downloading vector store content..."
        poetry run inspect_vector_store
        echo ""
        echo "✅ Inspection terminée! Vérifiez le dossier debug_output/"
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "❌ Option inconnue: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 