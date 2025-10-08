


import asyncio

from my_agents import run_onboarding_agent


########################################################
# Environment Variables
########################################################



async def async_main():
    conversation = [
        {"role": "user", "content": "Bonjour, je suis Marc Lefévre. J'essaye d'ouvrir un compte bancaire via l'application mobile."
        "Mais je ne recois pas l'email de confirmation. Mon email est 'marc.lefevre+test2@example.com'. Comment puis-je résoudre ce problème ?"}
    ]
    await run_onboarding_agent(conversation)


if __name__ == "__main__":
    asyncio.run(async_main())
