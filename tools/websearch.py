from __future__ import annotations

from typing import List


class WebSearchTool:
    """Simple stub for web search integration.

    Replace `search` implementation with Tavily/SerpAPI/Bing API when deploying.
    """

    def search(self, query: str, max_results: int = 3) -> List[str]:
        return [
            f"[MockSearch] {query} - result {i + 1}"
            for i in range(max_results)
        ]
