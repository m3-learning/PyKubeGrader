from typing import Optional

import panel as pn


def process_questions_and_codes(
    titles: str | list[str],
) -> tuple[list[str], list[Optional[pn.pane.Markdown]]]:
    # Ensure titles is a list
    if isinstance(titles, str):
        titles = [titles]

    processed_titles: list[str] = []
    code_blocks: list[Optional[pn.pane.Markdown]] = []

    for title in titles:
        # Split the title at the "```python" delimiter
        parts = title.split("```python", maxsplit=1)

        # First part is the title, stripped of leading/trailing whitespace
        title_without_code = parts[0].strip()

        # Remove aberrant ** from the beginning or end of the title
        if title_without_code.startswith("**"):
            title_without_code = title_without_code[2:]
        if title_without_code.endswith("**"):
            title_without_code = title_without_code[:-2]

        # Second part (if exists) contains the code block; split at closing ```
        code = parts[1].split("```", maxsplit=1)[0].strip() if len(parts) > 1 else ""

        # Append processed title
        processed_titles.append(title_without_code)

        # Append code block as Markdown if it exists
        if code:
            code_blocks.append(pn.pane.Markdown(f"```python\n{code}\n```"))
        else:
            code_blocks.append(None)

    return processed_titles, code_blocks
