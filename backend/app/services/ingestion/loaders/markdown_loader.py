import re
from pathlib import Path


class MarkdownLoader:
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

        if path.suffix.lower() not in {".md", ".markdown"}:
            raise ValueError(
                f"Expected a Markdown file: {file_path}"
            )

        markdown = path.read_text(
            encoding="utf-8"
        )

        return self._clean_markdown(markdown)

    def _clean_markdown(self, markdown: str) -> str:
        text = "\n".join(
            line.strip()
            for line in markdown.splitlines()
        )

        text = re.sub(
            r"```(?:[\w+-]+)?\s*\n(.*?)```",
            r"\1",
            text,
            flags=re.DOTALL,
        )

        text = re.sub(
            r"`([^`]+)`",
            r"\1",
            text,
        )

        text = re.sub(
            r"!\[([^\]]*)\]\([^)]+\)",
            r"\1",
            text,
        )

        text = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            text,
        )

        text = re.sub(
            r"^\s*#{1,6}\s+",
            "",
            text,
            flags=re.MULTILINE,
        )

        text = re.sub(
            r"^\s*>\s?",
            "",
            text,
            flags=re.MULTILINE,
        )

        text = re.sub(
            r"^\s*[-*+]\s+",
            "",
            text,
            flags=re.MULTILINE,
        )

        text = re.sub(
            r"^\s*\d+\.\s+",
            "",
            text,
            flags=re.MULTILINE,
        )

        text = re.sub(
            r"(\*\*|__)(.*?)\1",
            r"\2",
            text,
        )

        text = re.sub(
            r"(?<!\*)\*([^*]+)\*(?!\*)",
            r"\1",
            text,
        )

        text = re.sub(
            r"(?<!_)_([^_]+)_(?!_)",
            r"\1",
            text,
        )

        text = re.sub(
            r"~~([^~]+)~~",
            r"\1",
            text,
        )

        text = re.sub(
            r"^[-*_]{3,}\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        return "\n".join(lines)


markdown_loader = MarkdownLoader()