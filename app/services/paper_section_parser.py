"""Extract common scientific-paper sections from extracted text."""

import re

SECTION_ALIASES = {
    "methodology": {
        "method",
        "methods",
        "methodology",
        "materials and methods",
        "experimental setup",
        "proposed method",
        "approach",
    },
    "results": {
        "results",
        "experiments",
        "experimental results",
        "results and discussion",
        "evaluation",
        "experiments and results",
    },
    "conclusion": {
        "conclusion",
        "conclusions",
        "discussion and conclusion",
        "concluding remarks",
    },
}


def normalize_heading(line: str) -> str:
    """Remove common numbering and punctuation from a heading."""

    line = line.strip()
    line = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", line)
    line = re.sub(r"[:.\s]+$", "", line)

    return line.casefold().strip()


def extract_sections(full_text: str) -> dict[str, str]:
    """Extract recognized sections from plain text.

    This is a heuristic parser, not a complete scientific document parser.
    Unrecognized or absent sections return empty strings.
    """

    if not isinstance(full_text, str):
        raise TypeError("full_text must be a string.")

    if not full_text.strip():
        return {
            "methodology": "",
            "results": "",
            "conclusion": "",
        }

    # Map heading names to canonical field names.
    heading_to_field = {
        alias: field_name for field_name, aliases in SECTION_ALIASES.items() for alias in aliases
    }

    lines = full_text.splitlines()
    sections: dict[str, list[str]] = {}
    current_section: str | None = None

    for line in lines:
        normalized = normalize_heading(line)

        # A simple heuristic: recognize short, standalone headings.
        matched_field = None

        if len(normalized) <= 80:
            matched_field = heading_to_field.get(normalized)

        if matched_field:
            current_section = matched_field
            sections.setdefault(current_section, [])
            continue

        if current_section is not None:
            sections[current_section].append(line)

    return {
        field_name: "\n".join(sections.get(field_name, [])).strip()
        for field_name in SECTION_ALIASES
    }


if __name__ == "__main__":
    sample_text = """
1. Introduction
This paper explores a new model.

2. Methods
We trained a graph neural network on molecular data.

3. Results
The proposed model improved prediction performance.

4. Conclusion
The approach may support drug discovery.
"""

    extracted = extract_sections(sample_text)

    for section_name, section_text in extracted.items():
        print(f"\n{section_name.upper()}:\n{section_text}")
