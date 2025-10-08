from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import threading
import webbrowser
from urllib.parse import urlparse, parse_qs
from dotenv import find_dotenv, load_dotenv
from requests_oauthlib import OAuth2Session
import json

_ = load_dotenv(find_dotenv())

# -- oauth_local_flow.py --
CLIENT_ID = os.environ.get("HUBSPOT_CLIENT_ID")
CLIENT_SECRET = os.environ.get("HUBSPOT_SECRET_KEY")

AUTHORIZATION_BASE_URL = "https://mcp.hubspot.com/oauth/authorize/user"
TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
SCOPE = []
REDIRECT_URI = "http://localhost:3000/oauth-callback"
# -------------


#####
# access token
#####

json_str_prd = """{
    'token_type': 'bearer',
    'refresh_token': 'eu1-6f86-4bdc-4ba9-8306-44633d553fd3',
    'access_token': 'CLT1gPmbMxIVQlNQMl8kQEwrAggACAkWPQEkSEcZGMmCqEUg8fTBDijhx4oKMhQof3h-XtnlA6Zq3dm5C0LXtVzpFzosQlNQMl8kQEwrAh8ACBkGcX49AQMBJgMBKQJadQEB6wFVBwkQHBcfHAIUHBhCFBckU0rdZdo92nTB8ZUcyNfmZR1_SgNldTFSAFoAYAFomaPRIXABeAA',
    'hub_id': 145359177,
    'scopes': ['crm.objects.deals.read', 'crm.objects.line_items.read', 'scope_mappings.container', 'crm.objects.companies.read', 'crm.objects.orders.read', 'oauth', 'crm.objects.products.read', 'crm.objects.contacts.read'],
    'user_id': 70537625,
    'expires_in': 1800,
    'expires_at': 1759848184
}"""
json_str_none = None
json_str_test = """{'token_type': 'bearer', 'refresh_token': 'eu1-b7b0-b09e-46a0-8238-0d66c17b8cbc', 'access_token': 'CI7-mKGcMxIVQlNQMl8kQEwrAggACAkWPQEkSEcZGJXEjEYgkte_Dijhx4oKMhSZmJvJDBUD4-zoGvr1SpNMLxe-WTpWQlNQMl8kQEwrAyUAABkfkAGOAssCzALPAtAC9gL5AvoCowOlA_8D9AT1BPYE4QbiBrcHvgfDB8cH1wfzB_8HigipCMUIxwjbCOQI5wj3CI8Jngn2kQVCFD6NO2nfhVmoJxcyqgGDUgk-RSDkSgNldTFSAFoAYAFomaPRIXABeAA', 'hub_id': 147005973, 'scopes': ['crm.objects.deals.read', 'crm.objects.line_items.read', 'scope_mappings.container', 'crm.objects.companies.read', 'crm.objects.orders.read', 'oauth', 'crm.objects.products.read', 'crm.objects.contacts.read'], 'user_id': 70537625, 'expires_in': 1800, 'expires_at': 1759932465}"""

json_str = json_str_test
# Correction des quotes simples en doubles quotes pour un JSON valide

if json_str is not None:
    json_str_corrected = json_str.replace("'", '"')
    # Conversion en dictionnaire Python
    _token = json.loads(json_str_corrected)  # pyright: ignore[reportUndefinedVariable]
else:   
    _token = None



# objet pour récupérer le code entre threads
auth_code = {"code": None}

event = threading.Event()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/oauth-callback":
            qs = parse_qs(parsed.query)
            code = qs.get("code")
            if code:
                auth_code["code"] = code[0]
                # envoyer une page simple à l'utilisateur
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h1>Authentification reussie. Vous pouvez fermer cette fenetre.</h1>")
                # signaler au thread principal
                event.set()
                return
        # default 404
        self.send_response(404)
        self.end_headers()

def run_local_server():
    server = HTTPServer(("localhost", 3000), Handler)
    # serveur bloquant dans un thread
    server.serve_forever()


async def oauth():

    if _token is None:
    
        # démarrer serveur local
        t = threading.Thread(target=run_local_server, daemon=True)
        t.start()

        # créer la session OAuth
        oauth = OAuth2Session(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)

        # obtenir l'URL d'autorisation et ouvrir dans le navigateur
        authorization_url, state = oauth.authorization_url(AUTHORIZATION_BASE_URL)
        print("Ouverture du navigateur pour l'authentification...")
        webbrowser.open(authorization_url)

        # attendre que le handler mette le code
        print("En attente du code d'autorisation (callback)...")
        event.wait(timeout=300)  # timeout facultatif

        if not auth_code["code"]:
            print("Aucun code reçu (timeout?).")
            return

        code = auth_code["code"]
        # échanger le code contre un token
        token = oauth.fetch_token(TOKEN_URL,
                                include_client_id=True,
                                client_secret=CLIENT_SECRET,
                                code=code)
        print("Token récupéré :")
        print(token)
    else:
        print("Token déjà récupéré :")
        token = _token
        print(token)

    return token