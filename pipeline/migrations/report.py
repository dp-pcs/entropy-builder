"""Migration report writer.

After (or during dry-run of) `applier.apply(...)`, write a human-readable
markdown report to `<vault>/outputs/migration-report-vX.Y.Z.md` summarizing
what was applied, skipped, and what conflicts the applier preserved.

Schema: a list of `EntryResult` per change entry, grouped by version.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class EntryResult:
    """Outcome of one CHANGES entry on the vault."""

    version: str
    handler: str
    summary: str                   # one-line "added X" / "patched Y" / "conflict on Z"
    status: str                    # "applied" | "skipped" | "conflict" | "noop"
    details: list[str] = field(default_factory=list)
    links_rewritten: int = 0       # for rename: how many wikilinks were updated
    conflict_paths: list[str] = field(default_factory=list)


@dataclass
class MigrationReport:
    from_version: Optional[str]
    to_version: str
    results: list[EntryResult] = field(default_factory=list)
    dry_run: bool = False

    @property
    def applied(self) -> list[EntryResult]:
        return [r for r in self.results if r.status == "applied"]

    @property
    def skipped(self) -> list[EntryResult]:
        return [r for r in self.results if r.status == "skipped"]

    @property
    def noops(self) -> list[EntryResult]:
        return [r for r in self.results if r.status == "noop"]

    @property
    def conflicts(self) -> list[EntryResult]:
        return [r for r in self.results if r.status == "conflict"]

    @property
    def total_links_rewritten(self) -> int:
        return sum(r.links_rewritten for r in self.results)


def render_markdown(report: MigrationReport) -> str:
    lines: list[str] = []
    dry_tag = " (DRY-RUN)" if report.dry_run else ""
    lines.append(f"# Migration report — v{report.to_version}{dry_tag}")
    lines.append("")
    lines.append(f"- Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append(f"- From: {report.from_version or '(no prior version recorded)'}")
    lines.append(f"- To:   {report.to_version}")
    lines.append(
        f"- Totals: {len(report.applied)} applied · {len(report.noops)} no-op · "
        f"{len(report.skipped)} skipped · {len(report.conflicts)} conflicts · "
        f"{report.total_links_rewritten} wikilinks rewritten"
    )
    lines.append("")

    if report.conflicts:
        lines.append("## Conflicts (your local edits were preserved)")
        lines.append("")
        for r in report.conflicts:
            lines.append(f"- **{r.handler}** @ v{r.version} — {r.summary}")
            for p in r.conflict_paths:
                lines.append(f"  - `{p}`")
            for d in r.details:
                lines.append(f"  - {d}")
        lines.append("")

    if report.applied:
        lines.append("## Applied")
        lines.append("")
        for r in report.applied:
            extra = f" (rewrote {r.links_rewritten} wikilinks)" if r.links_rewritten else ""
            lines.append(f"- **{r.handler}** @ v{r.version} — {r.summary}{extra}")
            for d in r.details:
                lines.append(f"  - {d}")
        lines.append("")

    if report.noops:
        lines.append("## No-op (already current)")
        lines.append("")
        for r in report.noops:
            lines.append(f"- **{r.handler}** @ v{r.version} — {r.summary}")
        lines.append("")

    if report.skipped:
        lines.append("## Skipped")
        lines.append("")
        for r in report.skipped:
            lines.append(f"- **{r.handler}** @ v{r.version} — {r.summary}")
            for d in r.details:
                lines.append(f"  - {d}")
        lines.append("")

    return "\n".join(lines)


def write_report(vault_root: Path, report: MigrationReport) -> Path:
    """Write the report under `<vault>/outputs/` and return the written path."""
    outputs = vault_root / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    suffix = ".dry-run" if report.dry_run else ""
    path = outputs / f"migration-report-v{report.to_version}{suffix}.md"
    path.write_text(render_markdown(report))
    return path
