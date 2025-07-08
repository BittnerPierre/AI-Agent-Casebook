from dataclasses import dataclass
from pydantic import BaseModel
from typing import Generic, Optional, TypeVar, List


class SearchItem(BaseModel):
    reason: str
    "Votre raisonnement de pourquoi cette recherche est importante pour la requête et le résultat attendu."

    query: str
    "La requête à utiliser pour la recherche." 


T = TypeVar('T', bound=SearchItem)

class SearchPlan(BaseModel, Generic[T]):
    searches: List[T]
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


@dataclass
class ResearchInfo:  
    vector_store_name: str
    vector_store_id: str
    temp_dir: str