import gzip
import logging
import re
import urllib.parse
import urllib.request
import zlib
from pathlib import Path

import chardet
import html2text
from bs4 import BeautifulSoup, Comment

from ..config import get_config

# Configuration du logger
logger = logging.getLogger(__name__)


class SmartWebParser:
    """Parser HTML intelligent utilisant BeautifulSoup4 pour extraire et formater le contenu."""

    def __init__(self):
        # Configuration de html2text pour une conversion markdown propre
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # Pas de wrap automatique
        self.h2t.unicode_snob = True
        self.h2t.skip_internal_links = True
        self.h2t.protect_links = True
        self.h2t.mark_code = True
        self.h2t.wrap_links = False

    def extract_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Extrait le contenu principal en supprimant navigation, sidebar, footer, etc.
        """
        # Supprimer les éléments indésirables
        unwanted_selectors = [
            "nav",
            "navigation",
            ".nav",
            ".navigation",
            "header",
            ".header",
            "footer",
            ".footer",
            "sidebar",
            ".sidebar",
            ".side-bar",
            ".menu",
            ".nav-menu",
            "aside",
            ".aside",
            ".breadcrumb",
            ".breadcrumbs",
            ".social",
            ".social-links",
            ".comments",
            ".comment-section",
            ".advertisement",
            ".ads",
            ".ad",
            ".search",
            ".search-box",
            ".pagination",
            "script",
            "style",
            "noscript",
            ".cookie-banner",
            ".cookie-notice",
            ".share",
            ".sharing",
            ".related-posts",
            ".sidebar-widget",
        ]

        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()

        # Supprimer les commentaires HTML
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Essayer de trouver le contenu principal par des sélecteurs communs
        main_content_selectors = [
            "main",
            ".main-content",
            ".content",
            ".post-content",
            ".article-content",
            "article",
            ".entry-content",
            "#content",
            "#main",
            ".post-body",
            ".blog-post",
            ".single-post",
        ]

        for selector in main_content_selectors:
            main_content = soup.select_one(selector)
            if main_content and len(main_content.get_text().strip()) > 200:
                logger.info(f"Contenu principal trouvé avec le sélecteur: {selector}")
                return main_content

        # Si aucun sélecteur spécifique ne fonctionne, essayer de nettoyer le body
        body = soup.find("body")
        if body:
            logger.info("Utilisation du body complet comme contenu principal")
            return body

        # Dernier recours : retourner le soup nettoyé
        logger.warning("Aucun contenu principal spécifique trouvé, utilisation de tout le document")
        return soup

    def fix_inline_lists(self, text: str) -> str:
        """
        Détecte et corrige les listes inline mal formatées.
        Utilise trailing whitespace pour les sauts de ligne.
        """
        lines = text.split("\n")
        fixed_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                fixed_lines.append("")
                continue

            # Détecter si la ligne contient plusieurs items de liste séparés par *
            if "*" in line and not line.startswith("*"):
                parts = line.split("*")
                if len(parts) > 2:  # Au moins 2 items de liste
                    # Première partie peut être un titre/contexte
                    first_part = parts[0].strip()
                    if first_part:
                        fixed_lines.append(first_part + "  ")  # Trailing whitespace
                        fixed_lines.append("")  # Ligne vide

                    # Convertir le reste en liste avec trailing whitespace
                    for i, part in enumerate(parts[1:]):
                        part = part.strip()
                        if part:
                            if i < len(parts[1:]) - 1:  # Pas le dernier item
                                fixed_lines.append(f"* {part}  ")  # Trailing whitespace
                            else:
                                fixed_lines.append(f"* {part}")  # Pas de trailing sur le dernier
                    continue

            # Ligne normale
            fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def fix_markdown_formatting(self, markdown_text: str) -> str:
        """
        Corrige le formatage markdown en ajoutant des sauts de ligne appropriés.
        """
        # D'abord corriger les listes inline
        markdown_text = self.fix_inline_lists(markdown_text)

        lines = markdown_text.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            line = line.rstrip()

            # Correction des titres mal formatés (enlever # en fin)
            if re.match(r"^#+\s+.*#\s*$", line):
                line = re.sub(r"#\s*$", "", line)

            # Correction des blocs de code
            if line.strip() == "[code]":
                line = "```"
            elif line.strip() == "[/code]":
                line = "```"

            # Détecter le type d'élément
            is_heading = bool(re.match(r"^#+\s+", line))
            is_list_item = bool(
                re.match(r"^[\s]*[\*\-\+]\s+", line) or re.match(r"^[\s]*\d+\.\s+", line)
            )
            is_blockquote = line.strip().startswith(">")
            is_code_block = line.strip() == "```"
            is_horizontal_rule = bool(re.match(r"^[\-\*_]{3,}$", line.strip()))
            is_empty = line.strip() == ""

            # Ignorer les lignes vides (on les gèrera nous-mêmes)
            if is_empty:
                continue

            # Vérifier le contexte précédent
            prev_line = fixed_lines[-1] if fixed_lines else ""
            needs_space_before = False

            # RÈGLES POUR AJOUTER UNE LIGNE VIDE AVANT
            if is_heading:
                # TOUJOURS une ligne vide avant les titres (sauf au début)
                needs_space_before = len(fixed_lines) > 0 and prev_line != ""
            elif is_list_item:
                # Ligne vide avant une liste si le précédent n'était pas une liste
                prev_was_list = bool(
                    re.match(r"^[\s]*[\*\-\+]\s+", prev_line)
                    or re.match(r"^[\s]*\d+\.\s+", prev_line)
                )
                needs_space_before = len(fixed_lines) > 0 and prev_line != "" and not prev_was_list
            elif is_blockquote:
                # Ligne vide avant une citation si le précédent n'était pas une citation
                prev_was_quote = prev_line.strip().startswith(">")
                needs_space_before = len(fixed_lines) > 0 and prev_line != "" and not prev_was_quote
            elif is_code_block:
                # Ligne vide avant un bloc de code
                needs_space_before = len(fixed_lines) > 0 and prev_line != ""
            elif is_horizontal_rule:
                # Ligne vide avant une règle horizontale
                needs_space_before = len(fixed_lines) > 0 and prev_line != ""
            else:
                # Paragraphe normal - ligne vide si on vient de certains éléments
                if len(fixed_lines) > 0 and prev_line != "":
                    prev_was_heading = bool(re.match(r"^#+\s+", prev_line))
                    prev_was_list = bool(
                        re.match(r"^[\s]*[\*\-\+]\s+", prev_line)
                        or re.match(r"^[\s]*\d+\.\s+", prev_line)
                    )
                    prev_was_quote = prev_line.strip().startswith(">")
                    prev_was_code = prev_line.strip() == "```"

                    if prev_was_heading or prev_was_list or prev_was_quote or prev_was_code:
                        needs_space_before = True

            # Ajouter ligne vide avant si nécessaire
            if needs_space_before:
                fixed_lines.append("")

            # Ajouter la ligne actuelle
            fixed_lines.append(line)

            # RÈGLES POUR AJOUTER UNE LIGNE VIDE APRÈS
            needs_space_after = False

            # Regarder la ligne suivante
            next_line = ""
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # Ignorer les lignes vides pour trouver le prochain élément réel
                j = i + 1
                while j < len(lines) and not next_line:
                    j += 1
                    if j < len(lines):
                        next_line = lines[j].strip()

            if next_line:  # S'il y a encore du contenu après
                next_is_heading = bool(re.match(r"^#+\s+", next_line))
                next_is_list = bool(
                    re.match(r"^[\s]*[\*\-\+]\s+", next_line)
                    or re.match(r"^[\s]*\d+\.\s+", next_line)
                )
                next_is_quote = next_line.startswith(">")
                next_is_code = next_line == "```" or next_line == "[code]" or next_line == "[/code]"

                if is_heading:
                    # Ligne vide après tous les titres
                    needs_space_after = True
                elif is_code_block:
                    # Ligne vide après un bloc de code fermant
                    needs_space_after = True
                elif is_horizontal_rule:
                    # Ligne vide après une règle horizontale
                    needs_space_after = True
                elif is_list_item and not next_is_list:
                    # Ligne vide après une liste si l'élément suivant n'est pas une liste
                    needs_space_after = True
                elif is_blockquote and not next_is_quote:
                    # Ligne vide après une citation si l'élément suivant n'est pas une citation
                    needs_space_after = True

            # Ajouter ligne vide après si nécessaire
            if needs_space_after:
                fixed_lines.append("")

        # Nettoyer les lignes vides multiples (garder maximum 1)
        final_lines = []
        for line in fixed_lines:
            if line == "":
                if not final_lines or final_lines[-1] != "":
                    final_lines.append("")
            else:
                final_lines.append(line)

        # Enlever les lignes vides en fin
        while final_lines and final_lines[-1] == "":
            final_lines.pop()

        return "\n".join(final_lines)

    def parse_html(self, html_content: str, url: str) -> tuple[str, str]:
        """
        Parse le HTML et extrait le contenu principal en markdown.

        Returns:
            tuple: (title, markdown_content)
        """
        try:
            # Parser le HTML avec BeautifulSoup
            soup = BeautifulSoup(html_content, "lxml")

            # Extraire le titre
            title_element = soup.find("title")
            title = title_element.get_text().strip() if title_element else ""

            # Nettoyer le titre (enlever les suffixes communs)
            if title:
                # Supprimer les parties communes comme " | Site Name", " - Blog"
                title = re.sub(r"\s*[\|\-]\s*[^|]*$", "", title)
                title = title.strip()

            # Si pas de titre dans <title>, essayer h1
            if not title:
                h1 = soup.find("h1")
                title = h1.get_text().strip() if h1 else self._extract_title_from_url(url)

            # Extraire le contenu principal
            main_content = self.extract_main_content(soup)

            # Convertir en markdown
            markdown_content = self.h2t.handle(str(main_content))

            # Corriger le formatage markdown
            markdown_content = self.fix_markdown_formatting(markdown_content)

            # Nettoyage final
            markdown_content = self._clean_markdown(markdown_content)

            logger.info(
                f"Contenu parsé avec succès: {len(markdown_content)} caractères de markdown"
            )
            return title, markdown_content

        except Exception as e:
            logger.error(f"Erreur lors du parsing HTML: {e}")
            raise

    def _clean_markdown(self, markdown_text: str) -> str:
        """Nettoyage final du markdown."""
        # Nettoyer les espaces en fin de ligne
        lines = [line.rstrip() for line in markdown_text.split("\n")]

        # Supprimer les lignes avec seulement des caractères répétitifs
        cleaned_lines = []
        for line in lines:
            # Ignorer les lignes avec seulement des caractères de séparation faibles
            if re.match(r"^[\s\-_=\*\.]{0,5}$", line):
                continue
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def _extract_title_from_url(self, url: str) -> str:
        """Extrait un titre approximatif depuis l'URL."""
        path = urllib.parse.urlparse(url).path
        if path and path != "/":
            title = path.split("/")[-1]
            title = re.sub(r"[^a-zA-Z0-9\s-]", " ", title)
            title = " ".join(title.split())
            return title or "Document Web"
        return "Document Web"


class WebDocument:
    """Classe pour représenter un document web avec contenu markdown structuré."""

    def __init__(self, content: str, url: str, title: str = "", raw_html: str = ""):
        self.page_content = content
        self.raw_html = raw_html  # Stockage du HTML brut pour debug
        self.metadata = {
            "source": url,
            "title": title,
            "content_type": "markdown",
            "content_length": len(content),
            "html_length": len(raw_html),
        }


def decompress_response(data: bytes, encoding: str) -> bytes:
    """
    Décompresse les données si elles sont compressées.

    Args:
        data: Données brutes de la réponse
        encoding: Type d'encodage de compression

    Returns:
        Données décompressées
    """
    if encoding == "gzip":
        try:
            return gzip.decompress(data)
        except Exception as e:
            logger.warning(f"Erreur de décompression gzip: {e}")
            return data
    elif encoding == "deflate":
        try:
            return zlib.decompress(data)
        except Exception:
            # Essayer avec un header zlib
            try:
                return zlib.decompress(data, -zlib.MAX_WBITS)
            except Exception as e:
                logger.warning(f"Erreur de décompression deflate: {e}")
                return data
    elif encoding == "br":
        try:
            import brotli

            return brotli.decompress(data)
        except ImportError:
            logger.warning("Module brotli non disponible pour la décompression")
            return data
        except Exception as e:
            logger.warning(f"Erreur de décompression brotli: {e}")
            return data

    return data


def detect_encoding(data: bytes, content_type_header: str = "") -> str:
    """
    Détecte l'encodage du contenu.

    Args:
        data: Données brutes
        content_type_header: Header Content-Type de la réponse

    Returns:
        Nom de l'encodage détecté
    """
    # Essayer d'extraire l'encodage du header Content-Type
    if "charset=" in content_type_header:
        charset = content_type_header.split("charset=")[1].split(";")[0].strip()
        return charset

    # Utiliser chardet pour détecter l'encodage
    try:
        detected = chardet.detect(data[:10000])  # Analyser seulement les premiers 10KB
        if detected and detected["encoding"] and detected["confidence"] > 0.7:
            return detected["encoding"]
    except Exception as e:
        logger.warning(f"Erreur de détection d'encodage: {e}")

    # Fallback sur utf-8
    return "utf-8"


def save_html_debug(html_content: str, url: str, debug_dir: Path) -> Path | None:
    """
    Sauvegarde le HTML brut en mode debug.

    Args:
        html_content: Contenu HTML brut
        url: URL source
        debug_dir: Dossier de debug

    Returns:
        Chemin du fichier HTML sauvegardé
    """
    try:
        # Générer un nom de fichier à partir de l'URL
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc.replace(".", "_")
        path = parsed_url.path.strip("/").replace("/", "_")

        if path:
            filename = f"{domain}_{path}.html"
        else:
            filename = f"{domain}_index.html"

        # Nettoyer le nom de fichier
        filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
        filename = re.sub(r"_+", "_", filename)  # Supprimer les underscores multiples

        # Créer le sous-dossier html_raw
        html_debug_dir = debug_dir / "html_raw"
        html_debug_dir.mkdir(exist_ok=True)

        file_path = html_debug_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"HTML brut sauvegardé: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde HTML pour {url}: {e}")
        return None


def fetch_web_content_improved(url: str, timeout: int = 30) -> WebDocument | None:
    """
    Récupère le contenu d'une URL et l'analyse avec BeautifulSoup4.

    Args:
        url: URL à récupérer
        timeout: Timeout en secondes

    Returns:
        WebDocument ou None en cas d'erreur
    """
    try:
        logger.info(f"Récupération du contenu de: {url}")

        # Headers pour simuler un navigateur
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            "Connection": "close",  # Éviter les problèmes de connexion persistante
            "Cache-Control": "no-cache",
        }

        request = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                logger.error(f"Erreur HTTP {response.status} pour {url}")
                return None

            # Lire le contenu brut
            raw_data = response.read()

            # Vérifier si le contenu est compressé via les headers
            content_encoding = response.headers.get("Content-Encoding", "").lower()
            if content_encoding:
                logger.info(f"Décompression du contenu ({content_encoding})")
                raw_data = decompress_response(raw_data, content_encoding)

            # Détecter l'encodage
            content_type = response.headers.get("Content-Type", "")
            encoding = detect_encoding(raw_data, content_type)
            logger.info(f"Encodage détecté: {encoding}")

            # Décoder le contenu
            try:
                html_content = raw_data.decode(encoding)
            except UnicodeDecodeError as e:
                logger.warning(f"Erreur de décodage avec {encoding}: {e}")
                # Essayer avec utf-8 en mode remplaçant
                try:
                    html_content = raw_data.decode("utf-8", errors="replace")
                    encoding = "utf-8 (avec remplacement)"
                except Exception:
                    # Dernière tentative avec latin1 qui peut décoder n'importe quoi
                    html_content = raw_data.decode("latin1", errors="replace")
                    encoding = "latin1 (avec remplacement)"

        # Vérifier que nous avons bien du HTML
        if not html_content.strip().startswith("<") and "<html" not in html_content.lower():
            logger.error("Le contenu récupéré ne semble pas être du HTML valide")
            logger.debug(f"Début du contenu: {html_content[:200]}")
            return None

        # Sauvegarder le HTML brut en mode debug
        config = get_config()
        if config.debug.enabled:
            debug_dir = Path(config.debug.output_dir)
            save_html_debug(html_content, url, debug_dir)

        # Parser avec notre nouveau parser intelligent
        parser = SmartWebParser()
        title, markdown_content = parser.parse_html(html_content, url)

        if not markdown_content.strip():
            logger.warning(f"Aucun contenu textuel extrait de {url}")
            return None

        logger.info(f"Contenu extrait avec succès de {url} ({len(markdown_content)} caractères)")

        # Créer le WebDocument avec le HTML brut pour debug
        return WebDocument(
            content=markdown_content,
            url=url,
            title=title,
            raw_html=html_content if config.debug.enabled else "",
        )

    except urllib.error.URLError as e:
        logger.error(f"Erreur de connexion pour {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de {url}: {e}")
        logger.exception("Détails de l'erreur:")
        return None


def load_documents_from_urls_improved(urls: list[str]) -> list[WebDocument]:
    """
    Charge des documents depuis une liste d'URLs avec parsing amélioré.

    Args:
        urls: Liste des URLs à charger

    Returns:
        Liste des documents chargés avec succès
    """
    documents = []

    for url in urls:
        doc = fetch_web_content_improved(url)
        if doc:
            documents.append(doc)
        else:
            logger.warning(f"Impossible de charger le document de {url}")

    return documents


# Compatibilité avec l'API existante
def load_documents_from_urls(urls: list[str]) -> list[WebDocument]:
    """Wrapper pour compatibilité avec l'API existante."""
    return load_documents_from_urls_improved(urls)


def fetch_web_content(url: str, timeout: int = 30) -> WebDocument | None:
    """Wrapper pour compatibilité avec l'API existante."""
    return fetch_web_content_improved(url, timeout)
