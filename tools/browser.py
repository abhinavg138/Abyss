from tools.base import BaseTool
from urllib.request import Request, urlopen
from urllib.parse import urlparse


class BrowserTool(BaseTool):
    """Lightweight URL fetcher for public web pages."""

    def execute(self, url, max_chars=12000):
        url = str(url).strip()
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return "Invalid URL. Use http:// or https://."

        request = Request(url, headers={"User-Agent": "Abyss/0.3 (+personal-assistant)"})
        try:
            with urlopen(request, timeout=15) as response:
                content_type = response.headers.get("Content-Type", "")
                raw = response.read(2_000_000)
                charset = response.headers.get_content_charset() or "utf-8"
                text = raw.decode(charset, errors="ignore")
        except Exception as e:
            return f"Web fetch failed: {e}"

        if "text" not in content_type and "json" not in content_type and "xml" not in content_type:
            return f"Fetched {url}\nContent-Type: {content_type}\n(Binary content not displayed.)"

        return text[:max_chars]
