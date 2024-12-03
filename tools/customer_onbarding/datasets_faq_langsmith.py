from dotenv import find_dotenv, load_dotenv
from langsmith import Client

_ = load_dotenv(find_dotenv())

client = Client()

DATASET_NAME = "FAQ-datasets-25-11-2024"
dataset = client.create_dataset(DATASET_NAME)
client.create_examples(
    inputs=[
            {
                "question": "Comment effectuer un changement de carte ?"
            },
            {
                "question": "Pouvez-vous me dire si vous avez des garnitures disponibles pour les pizzas ?"
            },
            {
                "question": "Comment vous contacter si je ne suis plus client ?"
            },
            {
                "question": "Quel est le meilleur investissement immobilier pour cette année ?"
            },
            {
                "question": "Est-il possible de commander des espèces (euros ou devises) ?"
            },
            {
                "question": "Pouvez-vous m'expliquer les tendances actuelles du marché boursier mondial ?"
            },
            {
                "question": "Quel est le meilleur fournisseur d'assurance santé pour ma famille ?"
            },
            {
                "question": "Comment puis-je récupérer mon mot de passe oublié ?"
            },
            {
                "question": "Comment puis-je vérifier mes transactions récentes ?"
            },
        ],
    outputs=[
            {
                "answer": "Pour demander un changement de gamme, respectez ces conditions :\nCarte BOIS (une par titulaire) :\n\nD\u00e9bit imm\u00e9diat :\u00a00 \u20ac d'encours\nD\u00e9bit diff\u00e9r\u00e9 :\u00a010 000 \u20ac d'encours (20 000 \u20ac pour 2 titulaires)\n\nCarte Ultim :\n\nD\u00e9bit imm\u00e9diat :\u00a00 \u20ac d'encours\nD\u00e9bit diff\u00e9r\u00e9 :\u00a06 000 \u20ac d'encours (12 000 \u20ac pour 2 titulaires)\n\nCarte Bienvenue (d\u00e9bit imm\u00e9diat uniquement) :\n\n0 \u20ac d'encours\n\nConsultez notre Brochure Tarifaire pour les d\u00e9tails de facturation.\nSi vous avez les encours requis, changez de carte via \"Cartes\", \"Changer ma carte\", puis \"Changer de type de carte\".\nSi les crit\u00e8res ne sont pas respect\u00e9s, vous ne pourrez pas commander une nouvelle carte.\nPour plusieurs cartes, les conditions se cumulent. Par exemple, pour passer d'une Visa Ultim \u00e0 une BOIS, vous aurez besoin de 350 \u20ac d'encours (300 \u20ac pour BOIS + 50 \u20ac pour Visa Welcome).\nAttention :\n\nUn seul changement de type de carte par mois.\nLes plafonds de votre carte actuelle ne sont pas transf\u00e9r\u00e9s sur la nouvelle carte."
            },
            {
                "answer": "Je suis désolé, mais je ne peux pas fournir d'informations sur les garnitures de pizzas sans contexte approprié."
            },
            {
                "answer": "Si vous avez cl\u00f4tur\u00e9 vos comptes et que vous ne disposez plus de votre Espace Client pour nous contacter, vous pouvez nous contacter en\u00a0cliquant ici.\nVotre Service Commercial est ouvert du lundi au vendredi de 09h00 \u00e0 20h00 et le samedi de 08h45 \u00e0 16h30 (sauf jours f\u00e9ri\u00e9s).\nImportant\u00a0: il n'est pas possible de prendre rendez-vous pour \u00eatre rappel\u00e9 par un conseiller du Service Client."
            },
            {
                "answer": "Je suis désolé, mais je ne peux pas donner de recommandations sur les investissements immobiliers."
            },
            {
                "answer": "Nous ne proposons pas de livraisons d'esp\u00e8ces.\nVous devez effectuer un retrait important ? Vous pouvez \u00e0 tout moment demander un retrait exceptionnel sous r\u00e9serve d'encours suffisants. Pour ce faire :\n\nConnectez-vous \u00e0 votre Application ;\nCliquez sur \"Cartes\" ;\nS\u00e9lectionnez \"Modifier\" dans la partie\u00a0Plafonds puis l'onglet \"Retraits\" ;\u00a0\nEt enfin\u00a0\"Retrait exceptionnel\"\n\nVous avez besoin de devises \u00e9trang\u00e8res ? Votre carte vous permet d'effectuer des retraits et des paiements partout dans le monde.\u00a0\nNous vous invitons \u00e0 vous reporter \u00e0 notre Brochure tarifaire afin de prendre connaissance des frais sp\u00e9cifiques li\u00e9s aux op\u00e9rations r\u00e9alis\u00e9es en devises \u00e9trang\u00e8res."
            },
            {
                "answer": "Je suis désolé, mais je ne peux pas fournir d'explications sur les tendances du marché boursier."
            },
            {
                "answer": "Je suis désolé, mais je ne peux pas recommander de fournisseur d'assurance santé."
            },
            {
                "answer": "Vous pouvez récupérer votre mot de passe en cliquant sur 'Mot de passe oublié' sur la page de connexion. Suivez les étapes pour recevoir un lien de réinitialisation par email ou SMS."
            },
            {
                "answer": "Connectez-vous à votre espace client et accédez à la section 'Mes comptes'. Vous y trouverez l'historique détaillé de vos transactions récentes."
            }
        ],
    dataset_id=dataset.id,
)