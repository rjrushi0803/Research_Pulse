import os
from pathlib import Path

import requests
from dotenv import load_dotenv


def ingest_paper(api_url, paper_url: str, output_file: str = "output.md"):
    """Convert a paper URL to Markdown and save it to a file."""

    # api_url = "https://myrtle-income-sic-thus.trycloudflare.com/v1/convert/source"

    payload = {
        "sources": [{"kind": "http", "url": paper_url}],
        "options": {
            "to_formats": ["md", "json"],
            "do_picture_description": True,
            "picture_description_local": {
                "repo_id": "HuggingFaceTB/SmolVLM-256M-Instruct",
                "prompt": "Describe this image in detail.",
            },
            "include_images": True,
            "images_scale": 2.0,
        },
    }

    response = requests.post(api_url, json=payload, timeout=300)
    response.raise_for_status()

    markdown = response.json()["document"]["md_content"]

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    Path(output_file).write_text(markdown, encoding="utf-8")

    print(f"Paper saved to: {Path(output_file).resolve()}")


if __name__ == "__main__":
    ## loading the env variable
    load_dotenv()
    API_URL = os.getenv("DOCKLING_API_URL")

    ingest_paper(
        api_url=API_URL,
        paper_url="https://arxiv.org/pdf/1706.03762",
        output_file="data/papers/markdown/1706.03762.md",
    )
