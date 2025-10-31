🎥 Plan REX structuré façon Duarte — « MCP en vrai : pas si simple »

⸻

🎬 INTRO – L’USB-C des LLMs (la promesse du MCP)

What is (présent) :
• MCP, c’est la promesse d’un accès universel aux données et outils pour les LLMs.
“Un protocole unique pour que les agents puissent se brancher à tout — un peu comme l’USB-C de l’IA.”
• En théorie, il simplifie tout : fini les API clients, fini les wrappers custom, fini les clés dans les prompts.

What could be (futur souhaité) :
• Un monde où tout agent IA peut dialoguer avec n’importe quel service sans friction : ton CRM, tes fichiers, ton cloud.
“Un seul protocole, une infinité de connecteurs.”

Tension :
• Sauf que dans la vraie vie… la simplicité n’est qu’apparente.
• Chaque serveur MCP a ses propres règles, ses propres contraintes réseau, son propre comportement OAuth.

Resolution (annonce du plan) :
• J’ai testé les deux extrêmes : 1. HubSpot (cloud officiel, hébergé) 2. Evernote (local, self-hosted en Docker)
• Deux mondes différents, deux architectures, deux complexités.
“Et dans les deux cas, ce n’était pas du plug-and-play.”

Call to action :

“Alors dans ce REX, je vais vous montrer ce qu’on ne vous dit pas dans les tutos — et surtout, comment éviter de perdre quatre jours à déboguer vos MCP.”

⸻

🧱 CHAPITRE 1 – HubSpot Cloud : le mirage du “connecteur officiel”

What is :
• Un connecteur officiel, hébergé, prêt à l’emploi ? Pas vraiment.
• Pour l’utiliser, il faut créer et publier une app dans la marketplace HubSpot, configurer les scopes, gérer l’OAuth et héberger une app TypeScript.

What could be :
• Un bouton “Connecter HubSpot” dans ton agent, et tout marche.
“Un OAuth centralisé, un token stable, et des serveurs MCP qui se rafraîchissent tout seuls.”

Tension :
• Le MCP HubSpot ne gère pas l’OAuth côté serveur : c’est à toi de coder les 286 lignes d’authentification.
• Le token expire, la connexion tombe, l’agent doit se recréer à chaque interaction.
• Même les champs custom du CRM ne sont pas visibles sans documentation manuelle.
“Hébergé, oui. Facile, non.”

Resolution :
• MCP Cloud = cycle de vie court, logique stateless, serverless-friendly.
• Il faut accepter cette éphémérité, encapsuler la logique OAuth, et factoriser le code d’auth.
• Et comprendre qu’un connecteur officiel reste souvent lecture seule.
“En pratique, tu dois souvent le customiser, voire le réécrire.”

Call to action :

“Si vous utilisez un MCP cloud, préparez-vous à gérer vos propres tokens — et à documenter vos champs custom. Ce n’est pas magique, mais c’est industrialisable.”

⸻

🧩 CHAPITRE 2 – Evernote Local : la liberté sous Docker

What is :
• Pas d’API publique moderne, pas de connecteur officiel.
• Solution : serveur MCP communautaire TypeScript, déployé en Docker, communication stdio.
• OAuth géré par le serveur, aucun code d’auth côté client.

What could be :
• Un environnement local simple, sécurisé, extensible — où ton agent peut fouiller tes notes sans dépendre du cloud.
“Ton agent, ton réseau, ton contrôle.”

Tension :
• L’architecture est 1-pour-1 : un conteneur = un utilisateur.
• Si ton agent est hébergé dans le cloud, il ne peut pas accéder au serveur MCP local sans ouvrir des routes réseau.
• Et les logs ? stderr pour le debug, stdout pour le protocole — facile à dire, mais en production, ça devient vite le chaos.

Resolution :
• Solution : centraliser les déploiements via le Docker MCP Catalog.
→ Standardise, isole, et simplifie la distribution des serveurs MCP.
• Structurer les logs dès le départ (stderr = debug, stdout = protocole).
• Et garder le client MCP long-lived, stable sur la session.
“Self-hosting = autonomie, mais pas sans discipline.”

Call to action :

“Si vos services sont internes ou sensibles, l’option locale reste la meilleure — à condition de soigner la mise en réseau et les logs.”

⸻

🧠 CHAPITRE 3 – Résoudre la tension : comment industrialiser vos MCP

What is :
• Deux mondes coexistent :
• Les MCP cloud, difficiles d’accès depuis un environnement local.
• Les MCP locaux, invisibles pour les agents cloud.
• Aucun standard sur la durée de vie des clients, ni sur l’OAuth.

What could be :
• Un écosystème MCP unifié, avec gestion d’auth standard, tokens durables, logs structurés, et catalogues de déploiement prêts à l’emploi.
“Un vrai USB universel entre ton LLM et ton entreprise.”

Tension :
• Chaque framework agentique gère l’OAuth différemment : OpenAI Agents SDK, LangGraph, CrewAI, Anthropic…
• LangChain vient d’annoncer LangChain Auth, preuve que même les grands acteurs peinent à unifier cette couche.
• Sans normes communes, chaque projet doit réinventer la roue.

Resolution :
• Industrialiser le MCP, c’est : 1. Factoriser le code d’OAuth et le cycle de vie client. 2. Adopter des patterns standard (async with, short-lived cloud / long-lived local). 3. Utiliser les catalogues Docker MCP pour le déploiement interne. 4. Documenter explicitement les champs, logs et dépendances.
• Et surtout : ne pas confondre simplicité apparente et robustesse réelle.

Call to action (conclusion forte) :

“MCP n’est pas encore universel, mais il nous en rapproche.
Si vous préparez vos propres connecteurs — je peux vous aider à les concevoir, les déployer et les sécuriser.”

⸻

🏁 CONCLUSION – “Faire passer le courant sans faire sauter le disjoncteur”
• MCP promet l’universalité. En pratique, c’est encore deux mondes à relier.
• Le protocole résout la complexité technique, mais pas l’intégration opérationnelle.
• L’avenir ? Des connecteurs plus ouverts, des catalogues standardisés et une auth unifiée.
• Et d’ici là : savoir naviguer entre le cloud éphémère et le local persistant.

🎯 “Comprendre les limites, c’est déjà maîtriser le terrain.
Et maintenant que vous savez où sont les pièges, vous pouvez bâtir les vôtres — proprement.”
