"""Shared wikilink helpers used by both the wiki generator (pipeline/kimi.py)
and the vault assembler (pipeline/vault_builder.py).

Centralizing the link logic keeps the dangling-link sweep consistent between
LLM-generated wiki content and the skill templates we copy from Jay's repo.
"""
import re

WIKILINK_RE = re.compile(r"\[\[([^\[\]\|\n]+?)(\|[^\[\]\n]+)?\]\]")


def path_set_for_links(paths) -> set[str]:
    """Build the set of acceptable wikilink targets from a collection of paths.

    Includes the full path, the path without .md, and the bare basename so
    [[Foo]], [[Books/Foo]], and [[Books/Foo.md]] all resolve to Books/Foo.md.
    """
    targets: set[str] = set()
    for path in paths:
        targets.add(path)
        if path.endswith(".md"):
            targets.add(path[:-3])
            targets.add(path.rsplit("/", 1)[-1][:-3])
    return targets


def strip_dangling_wikilinks(content: str, valid_targets: set[str]) -> tuple[str, int]:
    """Replace [[wikilinks]] whose targets aren't in valid_targets with bold
    text. Returns (new_content, number_of_links_replaced).

    Preserves alias text when present: [[Foo|the foo]] → **the foo**.
    """
    replaced = [0]

    def _repair(match: re.Match) -> str:
        target = match.group(1).strip()
        alias = match.group(2)
        bare = target.split("#", 1)[0]
        if bare in valid_targets or bare.lstrip("/") in valid_targets:
            return match.group(0)
        replaced[0] += 1
        visible = alias[1:].strip() if alias else target.rsplit("/", 1)[-1]
        return f"**{visible}**"

    new_content = WIKILINK_RE.sub(_repair, content)
    return new_content, replaced[0]
