import asyncio
import json
import os
import time
import threading
import webbrowser
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

import requests
from dotenv import find_dotenv, load_dotenv
from requests_oauthlib import OAuth2Session

_ = load_dotenv(find_dotenv())

# Configuration OAuth HubSpot
CLIENT_ID = os.environ.get("HUBSPOT_CLIENT_ID")
CLIENT_SECRET = os.environ.get("HUBSPOT_SECRET_KEY")
AUTHORIZATION_BASE_URL = "https://app.hubspot.com/oauth/authorize"
TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
SCOPE = ["crm.objects.contacts.read", "crm.objects.companies.read", "crm.objects.deals.read", "oauth"]
REDIRECT_URI = "http://localhost:3000/oauth-callback"

# Fichier de stockage du token (non-commitable)
TOKEN_FILE = Path(".hubspot_token.json")

html_response = """
<html>
<head><title>Authentification HubSpot</title></head>
<body>
    <h1>Authentification réussie</h1>
    <p>Vous pouvez fermer cette fenêtre.</p>
    <script>
        // Optionnel : fermer automatiquement après 3 secondes
        setTimeout(() => window.close(), 3000);
    </script>
</body>
</html>
"""

class OAuthHandler(BaseHTTPRequestHandler):
    """Handler HTTP pour le callback OAuth."""
    
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/oauth-callback":
            qs = parse_qs(parsed.query)
            code = qs.get("code")
            if code:
                # Stocker le code dans l'instance du serveur
                self.server.auth_code = code[0]
                # Réponse à l'utilisateur
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html_response.encode('utf-8'))
                # Signaler que le code est reçu
                self.server.auth_event.set()
                return
        
        # 404 pour les autres chemins
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        # Supprimer les logs HTTP pour plus de propreté
        pass


class OAuthManager:
    """Gestionnaire OAuth thread-safe avec persistance et refresh automatique."""
    
    def __init__(self):
        self._token: Optional[Dict[str, Any]] = None
        self._lock = asyncio.Lock()
        self._server: Optional[HTTPServer] = None
        self._server_thread: Optional[threading.Thread] = None
        
    async def get_token(self) -> Dict[str, Any]:
        """
        Obtient un token OAuth valide.
        Charge depuis le fichier, refresh si nécessaire, ou crée un nouveau token.
        """
        async with self._lock:
            # 1. Essayer de charger depuis le fichier
            if self._token is None:
                self._token = self._load_token_from_file()
            
            # 2. Vérifier si le token est valide
            if self._token and self._is_token_valid(self._token):
                # print("✅ Token valide trouvé")
                return self._token
            
            # 3. Essayer de refresh le token
            if self._token and self._token.get("refresh_token"):
                print("🔄 Tentative de refresh du token...")
                try:
                    self._token = await self._refresh_token(self._token["refresh_token"])
                    self._save_token_to_file(self._token)
                    print("✅ Token refreshé avec succès")
                    return self._token
                except Exception as e:
                    print(f"❌ Échec du refresh: {e}")
            
            # 4. Créer un nouveau token via OAuth flow
            print("🔐 Création d'un nouveau token OAuth...")
            self._token = await self._do_oauth_flow()
            self._save_token_to_file(self._token)
            print("✅ Nouveau token créé et sauvegardé")
            return self._token
    
    def _load_token_from_file(self) -> Optional[Dict[str, Any]]:
        """Charge le token depuis le fichier local."""
        try:
            if TOKEN_FILE.exists():
                with open(TOKEN_FILE, 'r') as f:
                    token = json.load(f)
                print(f"📁 Token chargé depuis {TOKEN_FILE}")
                return token
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement du token: {e}")
        return None
    
    def _save_token_to_file(self, token: Dict[str, Any]) -> None:
        """Sauvegarde le token dans le fichier local."""
        try:
            with open(TOKEN_FILE, 'w') as f:
                json.dump(token, f, indent=2)
            print(f"💾 Token sauvegardé dans {TOKEN_FILE}")
        except Exception as e:
            print(f"⚠️ Erreur lors de la sauvegarde: {e}")
    
    def _is_token_valid(self, token: Dict[str, Any]) -> bool:
        """Vérifie si le token est encore valide (avec marge de 5 minutes)."""
        if not token.get("access_token"):
            return False
        
        expires_at = token.get("expires_at")
        if not expires_at:
            return False
        
        # Marge de sécurité de 5 minutes
        margin = 5 * 60
        return time.time() < (expires_at - margin)
    
    async def _refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh le token en utilisant le refresh_token."""
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        
        response = requests.post(TOKEN_URL, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        
        # Ajouter l'expiration calculée
        if 'expires_in' in token_data:
            token_data['expires_at'] = time.time() + token_data['expires_in']
        
        return token_data
    
    async def _do_oauth_flow(self) -> Dict[str, Any]:
        """Effectue le flow OAuth complet."""
        # Démarrer le serveur local
        await self._start_local_server()
        
        try:
            # Créer la session OAuth
            oauth_session = OAuth2Session(
                client_id=CLIENT_ID,
                redirect_uri=REDIRECT_URI,
                scope=SCOPE
            )
            
            # Obtenir l'URL d'autorisation
            authorization_url, state = oauth_session.authorization_url(AUTHORIZATION_BASE_URL)
            
            print("🌐 Ouverture du navigateur pour l'authentification...")
            webbrowser.open(authorization_url)
            
            # Attendre le callback (timeout de 5 minutes)
            print("⏳ En attente du code d'autorisation...")
            if not self._server.auth_event.wait(timeout=300):
                raise TimeoutError("Timeout lors de l'attente du code d'autorisation")
            
            if not hasattr(self._server, 'auth_code'):
                raise ValueError("Aucun code d'autorisation reçu")
            
            code = self._server.auth_code
            print(f"✅ Code d'autorisation reçu: {code[:10]}...")
            
            # Échanger le code contre un token
            token = oauth_session.fetch_token(
                TOKEN_URL,
                code=code,
                client_secret=CLIENT_SECRET,
                include_client_id=True
            )
            
            # Ajouter l'expiration calculée
            if 'expires_in' in token:
                token['expires_at'] = time.time() + token['expires_in']
            
            return token
            
        finally:
            await self._stop_local_server()
    
    async def _start_local_server(self) -> None:
        """Démarre le serveur local pour le callback OAuth."""
        if self._server is not None:
            return  # Serveur déjà démarré
        
        # Essayer plusieurs ports si 3000 est occupé
        for port in range(3000, 3010):
            try:
                self._server = HTTPServer(("localhost", port), OAuthHandler)
                self._server.auth_code = None
                self._server.auth_event = threading.Event()
                
                # Mettre à jour l'URI de redirection si le port change
                if port != 3000:
                    global REDIRECT_URI
                    REDIRECT_URI = f"http://localhost:{port}/oauth-callback"
                
                # Démarrer le serveur dans un thread
                self._server_thread = threading.Thread(
                    target=self._server.serve_forever,
                    daemon=True
                )
                self._server_thread.start()
                
                print(f"🚀 Serveur OAuth démarré sur le port {port}")
                return
                
            except OSError as e:
                if e.errno == 48:  # Address already in use
                    print(f"⚠️ Port {port} occupé, essai du port suivant...")
                    continue
                else:
                    raise
        
        raise RuntimeError("Impossible de démarrer le serveur OAuth (tous les ports occupés)")
    
    async def _stop_local_server(self) -> None:
        """Arrête le serveur local."""
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        
        if self._server_thread:
            self._server_thread.join(timeout=1)
            self._server_thread = None
        
        print("🛑 Serveur OAuth arrêté")
    
    def invalidate_token(self) -> None:
        """Force la création d'un nouveau token au prochain appel."""
        self._token = None
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
            print("🗑️ Token invalidé et fichier supprimé")


# Instance globale (singleton)
oauth_manager = OAuthManager()


# Interface publique (compatible avec l'ancien code)
async def oauth() -> Dict[str, Any]:
    """Interface publique pour obtenir un token OAuth."""
    return await oauth_manager.get_token()


# Fonction utilitaire pour invalider le token
def invalidate_oauth_token() -> None:
    """Invalide le token actuel et force une nouvelle authentification."""
    oauth_manager.invalidate_token()