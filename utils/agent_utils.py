import os
import re
from typing import Any
from pydantic_ai.mcp import MCPServerStreamableHTTP, MCPServerStdio
from pydantic_ai import Agent
from pydantic_ai.toolsets import WrapperToolset
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from pydantic_ai.models.instrumented import InstrumentationSettings

from .logging_config import get_logger

logger = get_logger(__name__)


def extract_web_content(text):
    """
    Aggressively remove all lines containing any markdown, HTML, or link syntax.
    """

    # Remove URLs first
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"www\.\S+", "", text)
    text = text.replace("--", "")

    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Remove ANY line containing brackets (link artifacts)
        if re.search(r"[\[\]]", stripped):
            continue


        # Remove lines with HTML/XML tags
        if re.search(r"<[^>]*>", stripped):
            continue

        # Remove lines starting with # (headers)
        # if stripped.startswith('#'):
        #     continue

        # Remove lines with markdown emphasis markers
        # if re.search(r'[\*_]{1,3}\S', stripped):
        #     continue

        # Remove lines with backticks (code)
        if "`" in stripped:
            continue

        # Remove lines that are only dashes/asterisks/underscores (horizontal rules)
        if re.match(r"^[\-\*_\s]{3,}$", stripped):
            continue

        # Keep the line
        cleaned_lines.append(stripped)

    # Join and clean up
    result = "\n".join(cleaned_lines)
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip()


class SearxngLimitingToolset(WrapperToolset):
    """Custom wrapper toolset to limit SearXNG search results."""

    def __init__(self, wrapped, max_results: int = 5):
        """Initialize with configurable result limit.

        Args:
            wrapped: The underlying toolset to wrap
            max_results: Maximum number of search results to return (default: 5)
        """
        super().__init__(wrapped)
        self.max_results = max_results

    async def call_tool(self, name: str, tool_args: dict[str, Any], ctx, tool) -> Any:
        """Intercept tool calls and limit SearXNG results."""
        # Call the original tool first
        result = await super().call_tool(name, tool_args, ctx, tool)

        # If this is a SearXNG search tool, limit results
        if name == "searxng_web_search":
            result_list = result.split("\n\n")
            logger.info(
                f"Limiting SearXNG results from {len(result_list)} to {self.max_results}"
            )
            # Return only the first max_results results
            return "\n\n".join(result_list[: self.max_results])
        elif name == "web_url_read":
            result = extract_web_content(result)

        return result


def get_searxng_mcp() -> MCPServerStreamableHTTP | MCPServerStdio:
    # Create MCP server connection - use environment variable or fallback to stdio
    MCP_SEARXNG_SERVER_URL = os.getenv("MCP_SEARXNG_SERVER_URL")
    if MCP_SEARXNG_SERVER_URL:
        logger.info(f"Using MCP server URL from environment: {MCP_SEARXNG_SERVER_URL}")
        return MCPServerStreamableHTTP(MCP_SEARXNG_SERVER_URL)
    else:
        logger.info(
            "ENV MCP_SEARXNG_SERVER_URL not found, falling back to MCPServerStdio"
        )
        SEARXNG_URL = os.getenv("SEARXNG_URL")
        if SEARXNG_URL:
            return MCPServerStdio(
                "npx", args=["-y", "mcp-searxng"], env={"SEARXNG_URL": SEARXNG_URL}
            )
        else:
            logger.error(
                "SEARXNG_URL environment variable is required when MCP_SEARXNG_SERVER_URL is not set"
            )
            raise ValueError(
                "MCP_SEARXNG_SERVER_URL or SEARXNG_URL environment variable is required"
            )


def prepare_agent(
    base_url: str,
    api_key: str,
    model: str,
    provider_kwargs: dict = None,
    modelsettings_kwargs: dict = None,
    chatmodel_kwargs: dict = None,
    **agent_kwargs,
) -> Agent:
    """
    Prepare a Pydantic AI Agent with OpenAI provider and model.
    Args:
        base_url (str): Base URL for the OpenAI API
        api_key (str): API key for authentication
        model (str): Model name to use for generation
        provider_kwargs (dict): Additional keyword arguments for OpenAIProvider
        modelsettings_kwargs (dict): Additional keyword arguments for ModelSettings
        chatmodel_kwargs (dict): Additional keyword arguments for OpenAIChatModel
        **agent_kwargs: Additional keyword arguments for Agent

    Returns:
        Agent: Configured Pydantic AI Agent instance
    """
    # Initialize mutable defaults to avoid shared state issues
    if provider_kwargs is None:
        provider_kwargs = {}
    if modelsettings_kwargs is None:
        modelsettings_kwargs = {}
    if chatmodel_kwargs is None:
        chatmodel_kwargs = {}

    # Create OpenAI provider with custom configuration
    openai_provider = OpenAIProvider(
        base_url=base_url, api_key=api_key, **provider_kwargs
    )
    
    # Set default max_tokens to avoid wasting tokens if model hallucination occurs
    if "max_tokens" not in modelsettings_kwargs:
        modelsettings_kwargs["max_tokens"] = 10000

    settings = ModelSettings(**modelsettings_kwargs)

    # Create OpenAI model with the provider
    openai_model = OpenAIChatModel(
        model, provider=openai_provider, settings=settings, **chatmodel_kwargs
    )

    instrumentation_settings = InstrumentationSettings(include_content=True)

    # Create Pydantic AI agent
    return Agent(
        openai_model, instrument=instrumentation_settings, retries=3, **agent_kwargs
    )
