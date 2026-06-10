from pathlib import Path


ROOT = Path(__file__).resolve().parent / "extracted_data"


def keep_head_conflict_block(text: str) -> str:
    while "<<<<<<< HEAD\n" in text and "\n=======\n" in text and "\n>>>>>>>" in text:
        start = text.index("<<<<<<< HEAD\n")
        mid = text.index("\n=======\n", start)
        end = text.index("\n>>>>>>>", mid)
        head = text[start + len("<<<<<<< HEAD\n") : mid]
        suffix = text[end:].split("\n", 1)
        text = text[:start] + head + (suffix[1] if len(suffix) > 1 else "")
    return text


def remove_trailing_conflict_markers(text: str) -> str:
    cleaned_lines = []
    for line in text.splitlines():
        if ">>>>>>>" in line:
            line = line.split(">>>>>>>", 1)[0]
        if line.startswith(">>>>>>> "):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines) + "\n"


def main() -> None:
    for path in ROOT.glob("*.json"):
        original = path.read_text(encoding="utf-8")
        cleaned = keep_head_conflict_block(original)
        cleaned = remove_trailing_conflict_markers(cleaned)
        if cleaned != original:
            path.write_text(cleaned, encoding="utf-8")
            print(f"cleaned {path.name}")


if __name__ == "__main__":
    main()
