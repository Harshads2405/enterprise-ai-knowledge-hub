from pathlib import Path

from bs4 import BeautifulSoup


class HTMLLoader:
    def load(self, file_path: str) -> str:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Path is not a file: {file_path}"
            )

        if path.suffix.lower() not in {".html", ".htm"}:
            raise ValueError(
                f"Expected an HTML file: {file_path}"
            )

        html = path.read_text(
            encoding="utf-8"
        )

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        for element in soup(
            ["script", "style", "noscript"]
        ):
            element.decompose()

        return soup.get_text(
            separator="\n",
            strip=True,
        )


html_loader = HTMLLoader()