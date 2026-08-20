from collections.abc import Iterable

from workforge.config import WorkspaceConfig
from workforge.models import Priority, Requirement, WorkTask


META_PREFIXES = {
    "source": "source",
    "priority": "priority",
    "labels": "labels",
    "namespace": "namespace",
    "milestone": "milestone",
}


def parse_markdown_requirements(content: str, config: WorkspaceConfig) -> list[Requirement]:
    sections = _split_h2_sections(content)
    return [_parse_section(title, lines, config) for title, lines in sections]


def _split_h2_sections(content: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in content.splitlines():
        if line.startswith("## "):
            if current_title:
                sections.append((current_title, current_lines))
            current_title = line.removeprefix("## ").strip()
            current_lines = []
        elif current_title:
            current_lines.append(line)

    if current_title:
        sections.append((current_title, current_lines))

    return sections


def _parse_section(title: str, lines: Iterable[str], config: WorkspaceConfig) -> Requirement:
    metadata: dict[str, str] = {}
    description_lines: list[str] = []
    tasks: list[WorkTask] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        key, value = _parse_metadata_line(stripped)
        if key:
            metadata[key] = value
            continue

        if stripped.startswith("- "):
            tasks.append(WorkTask(title=stripped.removeprefix("- ").strip()))
            continue

        description_lines.append(stripped)

    labels = _split_csv(metadata.get("labels", ""))
    priority = metadata.get("priority", "medium")

    return Requirement(
        title=title,
        description="\n".join(description_lines),
        source=metadata.get("source", config.defaults.source),
        namespace=metadata.get("namespace", config.defaults.namespace),
        priority=_normalize_priority(priority),
        milestone=metadata.get("milestone"),
        labels=labels,
        tasks=tasks,
    )


def _parse_metadata_line(line: str) -> tuple[str | None, str]:
    if ":" not in line:
        return None, ""

    raw_key, raw_value = line.split(":", 1)
    key = raw_key.strip().lower()
    if key not in META_PREFIXES:
        return None, ""

    return META_PREFIXES[key], raw_value.strip()


def _split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _normalize_priority(value: str) -> Priority:
    normalized = value.strip().lower()
    if normalized in {"low", "medium", "high", "urgent"}:
        return normalized  # type: ignore[return-value]
    return "medium"
