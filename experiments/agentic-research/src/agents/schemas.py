from pydantic import BaseModel


class SearchItem(BaseModel):
    reason: str
    "Votre raisonnement pour pourquoi cette recherche est importante pour la requête."

    query: str
    "Le terme de recherche à utiliser pour la recherche." 


class SearchPlan(BaseModel):
    searches: list[SearchItem]
    """Une liste de recherches à effectuer pour mieux répondre à la requête."""



class FileSearchItem(SearchItem):
    pass


class WebSearchItem(SearchItem):
    pass


class FileSearchPlan(SearchPlan):
    pass


class WebSearchPlan(SearchPlan):
    pass
