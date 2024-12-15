def extract_section_markdown(text: str, heading: str) -> str:
    """
    Extracts content from a markdown text under the specified heading.
    """
    lines = text.split("\n")
    content = []
    capture = False
    for line in lines:
        line = line.strip()
        if line.startswith(f"#{heading}"):
            capture = True
            continue
        if line.startswith("#"):
            capture = False
            continue
        if capture:
            content.append(line)
    return "\n".join(content).strip()
