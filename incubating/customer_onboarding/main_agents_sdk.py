import asyncio

from agents import gen_trace_id, trace
from agents.mcp import MCPServerStreamableHttp

from my_agents import oauth
from my_agents import run_onboarding_agent_with_mcp, run_onboarding_agent


########################################################
# Environment Variables
########################################################


async def async_main_with_server():
    
    # Faire l'OAuth une seule fois
    token = await oauth()
    
    # Créer le serveur MCP une seule fois
    mcp_hubspot_server = MCPServerStreamableHttp(
        name="Streamable HTTP Python Server",
        params={
            "url": "https://mcp.hubspot.com",
            "headers": {"Authorization": f"Bearer {token['access_token']}"},
            "timeout": 10
        },
        cache_tools_list=True,
        max_retry_attempts=3,
    )
    
    async with mcp_hubspot_server as server:
        trace_id = gen_trace_id()
        with trace("Customer Onboarding", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            # Premier appel
            conversation = [
                {"role": "user", "content": "Bonjour, je suis Marc Lefévre. J'essaye d'ouvrir un compte bancaire via l'application mobile."
                "Mais je ne recois pas l'email de confirmation. Mon email est 'marc.lefevre+test2@example.com'. Comment puis-je résoudre ce problème ?"}
            ]
            print(f"➡️: {conversation[0]["content"]}")
            result = await run_onboarding_agent(server, conversation)
            print(f"⬅️: {result.final_output}")
            
            # Second appel avec le même serveur
            response = "Oui, mon compte est en France et j'en suis le titulaire. Je suis Français."
            conversation=result.to_input_list() + [
                {"role": "user", "content": response}
            ]
            print(f"➡️: {response}")
            result = await run_onboarding_agent(server, conversation)
            print(f"⬅️: {result.final_output}")


if __name__ == "__main__":
    asyncio.run(async_main_with_server())

