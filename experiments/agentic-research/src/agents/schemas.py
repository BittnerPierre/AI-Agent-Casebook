from pydantic import BaseModel
from typing import Generic, TypeVar, List


class SearchItem(BaseModel):
    reason: str
    "Votre raisonnement pour pourquoi cette recherche est importante pour la requête."

    query: str
    "La requête à utiliser pour la recherche." 

T = TypeVar('T', bound=SearchItem)

class SearchPlan(BaseModel, Generic[T]):
    searches: List[T]
    """Une liste de recherches à effectuer pour mieux répondre à la requête."""


class FileSearchItem(SearchItem):
    filename: str
    "Le nom du fichier à rechercher dans la base de connaissances."


class WebSearchItem(SearchItem):
    pass


class FileSearchPlan(SearchPlan[FileSearchItem]):
    pass


class WebSearchPlan(SearchPlan[WebSearchItem]):
    pass
