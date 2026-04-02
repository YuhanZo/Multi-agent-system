from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from app.core.config import settings


@tool
def read_file(file_path: str) -> str:
    """Read and return the content of a file.
    Supports: .txt, .csv, .json, .py, .md, .pdf, .xlsx, .xls"""
    import pathlib

    path = pathlib.Path(file_path)
    if not path.exists():
        return f"Error: file not found: {file_path}"

    suffix = path.suffix.lower()

    try:
        if suffix == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)

        elif suffix in (".xlsx", ".xls"):
            import pandas as pd
            df = pd.read_excel(file_path)
            return df.to_string(index=False)

        elif suffix == ".csv":
            import pandas as pd
            df = pd.read_csv(file_path)
            return df.to_string(index=False)

        else:
            # txt, json, py, md, etc.
            return path.read_text(encoding="utf-8", errors="ignore")

    except Exception as e:
        return f"Error reading file: {e}"


def get_tools():
    web_search = TavilySearch(
        max_results=5,
        tavily_api_key=settings.TAVILY_API_KEY,
    )
    return [web_search, read_file]


TOOLS = get_tools()
