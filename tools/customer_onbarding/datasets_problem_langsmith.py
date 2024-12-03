from dotenv import find_dotenv, load_dotenv
from langsmith import Client

_ = load_dotenv(find_dotenv())

client = Client()

DATASET_NAME = "PROBLEM-datasets-03-12-2024"
dataset = client.create_dataset(DATASET_NAME)
client.create_examples(
    inputs=[
            {
              "input": "Je ne reçois pas l'e-mail pour valider mon compte."
            },
            {
              "input": "Mon code SMS ne fonctionne pas pour me connecter."
            },
            {
              "input": "Erreur CONN-PASS-004 : impossible de réinitialiser mon mot de passe."
            },
            {
              "input": "Le formulaire rejette mon numéro de téléphone valide."
            },
            {
              "input": "L'application mobile plante dès que je l'ouvre."
            },
            {
              "input": "Je ne trouve pas votre application sur Google Play."
            },
            {
              "input": "Pourquoi l'application demande-t-elle l'accès à ma géolocalisation ?"
            },
            {
              "input": "Erreur FORM-SYS-010 : Le formulaire indique une erreur système."
            },
            {
              "input": "Impossible de télécharger mon justificatif de domicile."
            },
            {
              "input": "Mon mot de passe est rejeté, mais je ne comprends pas pourquoi."
            },
            {
              "input": "Erreur CONN-PASS-999 : code inconnu."
            },
            {
              "input": "Pouvez-vous me conseiller sur un prêt immobilier ?"
            },
            {
              "input": "Comment acheter des actions sur votre plateforme ?"
            },
            {
              "input": "Pourquoi les pizzas sont-elles meilleures à Naples qu'ailleurs ?"
            }
          ],
    outputs=[
            {
                "answer": "Vérifiez vos dossiers de courriers indésirables ou spam pour l'e-mail de validation. Si vous ne le recevez toujours pas, confirmez que l'adresse e-mail saisie est correcte et demandez à renvoyer l'e-mail."
            },
            {
                "answer": "Vérifiez si le code SMS est expiré (plus de 5 minutes). Demandez un nouveau code et assurez-vous d'utiliser le dernier reçu. Si le problème persiste, vérifiez la connectivité mobile ou contactez le support."
            },
            {
                "answer": "Vérifiez vos dossiers de spam ou indésirables pour l'e-mail de réinitialisation. Si le lien est expiré, demandez un nouveau lien ou contactez le support technique."
            },
            {
                "answer": "Assurez-vous que le format du numéro de téléphone est correct, incluant l'indicatif international. Si l'erreur persiste, cela pourrait être dû à une limitation côté serveur. Contactez le support."
            },
            {
                "answer": "Désinstallez et réinstallez l'application. Vérifiez également si votre appareil et l'application sont à jour. Si le problème persiste, redémarrez votre appareil."
            },
            {
                "answer": "Assurez-vous que votre appareil répond aux critères minimums de version iOS/Android. Cherchez l'application officielle avec son nom exact ou via le lien disponible sur notre site web."
            },
            {
                "answer": "Certaines fonctionnalités nécessitent des permissions spécifiques, comme la géolocalisation pour vérifier votre identité ou localisation. Vous pouvez ajuster ces permissions dans les paramètres de votre appareil."
            },
            {
                "answer": "Essayez de soumettre à nouveau après quelques minutes. Assurez-vous d'utiliser une connexion stable. Si l'erreur persiste, signalez-la au support technique."
            },
            {
                "answer": "Vérifiez que vos fichiers respectent les formats acceptés (PDF, JPG, PNG) et ne dépassent pas 5 Mo. Si nécessaire, essayez un autre navigateur ou appareil."
            },
            {
                "answer": "Votre mot de passe doit contenir au moins 8 caractères, un chiffre, et un caractère spécial. Exemple : `P@ssw0rd!`."
            },
            {
                "answer": "Le code CONN-PASS-999 n'est pas reconnu. Assurez-vous d'avoir saisi le bon code ou décrivez votre problème pour que nous puissions vous aider."
            },
            {
                "answer": "Je suis désolé, mais je ne peux pas fournir de conseils sur les prêts immobiliers."
            },
            {
                "answer": "Cette question semble être hors de la portée de notre assistance."
            },
            {
                "answer": "Je suis désolé, mais cette question est hors contexte pour notre assistance bancaire."
            }
        ],
    dataset_id=dataset.id,
)