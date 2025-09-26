from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel


class SearchItem(BaseModel):
    reason: str
    "Votre raisonnement de pourquoi cette recherche est importante pour la requête et le résultat attendu."

    query: str
    "La requête à utiliser pour la recherche."


T = TypeVar("T", bound=SearchItem)


class SearchPlan(BaseModel, Generic[T]):
    searches: list[T]
    """Une liste de recherches à effectuer pour mieux répondre à la requête."""


class FileSearchItem(SearchItem):
    pass
    # filename: Optional[str] = None
    # "Le nom du fichier à rechercher dans la base de connaissances."


class WebSearchItem(SearchItem):
    pass


class FileSearchPlan(SearchPlan[FileSearchItem]):
    pass


class WebSearchPlan(SearchPlan[WebSearchItem]):
    pass


class FileSearchResult(BaseModel):
    file_name: str
    "Le nom du fichier contenant les résultats de la recherche."


class FileFinalReport(BaseModel):
    absolute_file_path: str
    "Le chemin absolu du fichier contenant le rapport final."

    short_summary: str
    "Le résumé court du rapport final."

    follow_up_questions: list[str]
    "Les questions suivantes à explorer."


from dataclasses import field


@dataclass
class ResearchInfo:
    temp_dir: str
    output_dir: str
    max_search_plan: str = "1"
    vector_store_name: str | None = None
    vector_store_id: str | None = None
    search_results: list[str] = field(default_factory=list)
    """List of filenames resulting from research (e.g., .txt, .md, .pdf files)."""


class ReportData(BaseModel):
    file_name: str
    """The name of the file containing the final report."""

    research_topic: str
    """The main research topic following naming rules : no space (use `_` instead) or special caracter)."""

    short_summary: str
    """A short 2-3 sentence summary of the findings."""

    markdown_report: str
    """The final report"""

    follow_up_questions: list[str]
    """Suggested topics to research further"""
