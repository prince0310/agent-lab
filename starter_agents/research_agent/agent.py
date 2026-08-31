from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.websearch import WebSearchTools


def create_research_agent(api_key):

    model = Gemini(
        id="gemini-3.6-flash",
        api_key=api_key,
    )

    agent = Agent(
        name="Research Agent",
        model=model,
        tools=[WebSearchTools()],
        instructions=[
            "You are a research agent.",
            "Research the given topic using the available web search tools.",
            "Provide a clear and well-structured research report.",
        ],
    )

    return agent