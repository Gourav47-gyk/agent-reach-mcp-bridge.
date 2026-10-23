import hmac
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import os
import httpx
import feedparser

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "Agent Reach Bridge",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "10000")),
    stateless_http=True,
)

@mcp.tool()
async def read_webpage(url: str) -> str:
    """Read a public webpage and return its text as Markdown."""
    if not url.startswith(("https://", "http://")):
        return "Error: only HTTP and HTTPS URLs are supported."

    async with httpx.AsyncClient(
        timeout=30, follow_redirects=True
    ) as client:
        response = await client.get(
            "https://r.jina.ai/" + url
        )
        response.raise_for_status()
        return response.text[:20000]


@mcp.tool()
async def search_github_repositories(query: str) -> str:
    """Search public GitHub repositories."""
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "per_page": 10},
            headers={"Accept": "application/vnd.github+json"},
        )
        response.raise_for_status()
        data = response.json()

    results = []
    for repo in data.get("items", []):
        results.append(
            f"{repo['full_name']}: {repo.get('description')}\n"
            f"Stars: {repo['stargazers_count']}\n"
            f"{repo['html_url']}"
        )
    return "\n\n".join(results) or "No repositories found."


@mcp.tool()
async def read_rss_feed(url: str) -> str:
    """Read recent entries from a public RSS or Atom feed."""
    if not url.startswith(("https://", "http://")):
        return "Error: only HTTP and HTTPS URLs are supported."

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url)
        response.raise_for_status()

    feed = feedparser.parse(response.text)
    results = []
    for entry in feed.entries[:10]:
        results.append(
            f"{entry.get('title', 'Untitled')}\n"
            f"{entry.get('link', '')}\n"
            f"{entry.get('summary', '')[:1000]}"
        )
    return "\n\n".join(results) or "No feed entries found."

class TokenAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path == "/health":
            return JSONResponse({"status": "ok"})

        expected = os.environ.get("MCP_ACCESS_TOKEN", "")
        supplied = request.headers.get("Authorization", "")

        if not expected:
            return JSONResponse(
                {"error": "Server token is not configured"},
                status_code=503,
            )

        if not hmac.compare_digest(
            supplied, f"Bearer {expected}"
        ):
            return JSONResponse(
                {"error": "Unauthorized"},
                status_code=401,
            )

        return await call_next(request)
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
  
