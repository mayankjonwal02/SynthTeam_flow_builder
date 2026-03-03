from app.ai.tools.registry import register_tool
from app.ai.tools.base import SynthTool


@register_tool("web_search")
class WebSearchTool(SynthTool):
    name: str = "web_search"
    description: str = "Search the web for current information. Input: search query string."
    api_key: str = ""

    def _run(self, query: str) -> str:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.api_key)
            results = client.search(query, max_results=5)
            return "\n\n".join(
                f"**{r['title']}**\n{r['content']}" for r in results.get("results", [])
            )
        except Exception as e:
            return f"Search failed: {e}"

    async def _arun(self, query: str) -> str:
        return self._run(query)
