#!/usr/bin/env python3
"""
BrainLift Processor - Extracts SPOVs, insights, experts from BrainLifts
and integrates them into second brain structure

BrainLifts are structured research artifacts with:
- DOK 4: Spiky Points of View (SPOVs) - your strongest claims
- DOK 3: Insights - key findings
- DOK 2: Knowledge Tree - categorized sources
- DOK 1: Facts - raw data
- Experts: People who influenced this work
- Purpose: What the research is about
"""
import re
from pathlib import Path
from typing import List, Dict
import sys


class BrainLift:
    """Represents a parsed BrainLift"""

    def __init__(self, path: Path):
        self.path = path
        self.title = ""
        self.owner = ""
        self.purpose = ""
        self.spovs = []
        self.insights = []
        self.experts = []
        self.content = path.read_text(encoding='utf-8')
        self._parse()

    def _parse(self):
        """Extract structured sections from BrainLift"""
        # Extract title from frontmatter
        title_match = re.search(r'title:\s*"([^"]+)"', self.content)
        if title_match:
            self.title = title_match.group(1)
            # Clean [link](url) format from title
            self.title = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', self.title)

        # Extract Purpose
        purpose_match = re.search(
            r'Purpose of this BrainLift:(.+?)(?:\n  - |\n- |$)',
            self.content,
            re.DOTALL
        )
        if purpose_match:
            self.purpose = purpose_match.group(1).strip()

        # Extract SPOVs
        spov_section = re.search(
            r'  - DOK[- ]?4.*?(?:SPOV|Spiky).+?\n(.+?)(?=\n  - DOK|$)',
            self.content,
            re.DOTALL | re.IGNORECASE
        )
        if spov_section:
            spov_text = spov_section.group(1)
            # Each SPOV can be in one of two formats:
            # Format 1: "    - **1. Title**" (GEPA style)
            # Format 2: "    - Spiky POV #1: Title" (OGP style)

            # Try format 1 first
            spov_blocks = re.findall(
                r'    - \*\*(\d+)\.\s*([^*]+)\*\*\s*\n(.+?)(?=\n    - \*\*\d+\.|$)',
                spov_text,
                re.DOTALL
            )

            # If format 1 didn't match, try format 2
            if not spov_blocks:
                spov_blocks = re.findall(
                    r'    - Spiky POV #(\d+):\s*(.+?)\n(.+?)(?=\n    - Spiky POV #\d+:|$)',
                    spov_text,
                    re.DOTALL
                )

            for num, title, content in spov_blocks:
                self.spovs.append({
                    'number': int(num),
                    'title': title.strip(),
                    'content': content.strip()
                })

        # Extract Insights
        insights_section = re.search(
            r'  - DOK[- ]?3.*?Insight.+?\n(.+?)(?=\n  - Experts|\n  - DOK|$)',
            self.content,
            re.DOTALL | re.IGNORECASE
        )
        if insights_section:
            insights_text = insights_section.group(1)
            # Each insight starts with 4+ spaces, then **number. title**
            insight_blocks = re.findall(
                r'    - \*\*(\d+)\.\s*([^*]+)\*\*\s*\n(.+?)(?=\n    - \*\*\d+\.|$)',
                insights_text,
                re.DOTALL
            )
            for num, title, content in insight_blocks:
                self.insights.append({
                    'number': int(num),
                    'title': title.strip(),
                    'content': content.strip()
                })

        # Extract Experts
        experts_section = re.search(
            r'  - Experts\s*\n(.+?)(?:\n  - DOK|$)',
            self.content,
            re.DOTALL
        )
        if experts_section:
            experts_text = experts_section.group(1)
            # Experts are either direct or in subcategories
            # Look for pattern: "      - number. Name – Organization"
            expert_blocks = re.findall(
                r'      - (\d+)\.\s*([^–\n]+)\s*[–—-]\s*([^\n]+)',
                experts_text
            )
            for num, name, org in expert_blocks:
                self.experts.append({
                    'number': int(num),
                    'name': name.strip(),
                    'organization': org.strip()
                })


def categorize_brainlift(brainlift: BrainLift) -> str:
    """Determine where this BrainLift should go

    Returns: 'source' | 'framework' | 'knowledge'
    """
    title_lower = brainlift.title.lower()
    purpose_lower = brainlift.purpose.lower()

    # Published research/papers → sources (your own work)
    if any(word in title_lower for word in ['gepa', 'expertise inflation', 'quantifying']):
        return 'source'

    # Protocols/architectures you built → frameworks
    if any(word in title_lower for word in ['ogp', 'open gateway', 'a2a', 'protocol']):
        return 'framework'

    # Multi-tenant, CI/CD, platform design → frameworks
    if any(word in title_lower for word in ['multi-tenant', 'ci/cd', 'gateway architecture']):
        return 'framework'

    # Technology deep-dives → knowledge
    if any(word in title_lower for word in ['mcp', 'ai vision', 'browser', 'video generation']):
        return 'knowledge'

    # Default: if it has 3+ SPOVs, it's probably a framework (strong opinions = methodology)
    if len(brainlift.spovs) >= 3:
        return 'framework'

    # Otherwise, knowledge base
    return 'knowledge'


def generate_source_file(brainlift: BrainLift, vault_path: Path) -> str:
    """Convert BrainLift to source file (your published work)"""
    filename = f"{brainlift.title.replace(':', ' -').replace('/', '-')}.md"
    filepath = vault_path / 'sources' / filename

    content = f"""---
type: source
name: "{brainlift.title}"
author: "David Proctor"
source_type: research
date_published: 2026-05-04
relevance: "{brainlift.purpose[:200]}..."
tags: ["brainlift", "research", "published"]
is_shareable: true
last_updated: 2026-05-04
---

# {brainlift.title}

**Your Published Research**

## Purpose

{brainlift.purpose}

## Key Spiky POVs

"""

    for spov in brainlift.spovs[:3]:  # Top 3 SPOVs
        content += f"\n### SPOV {spov['number']}: {spov['title']}\n\n"
        # Extract first paragraph
        first_para = spov['content'].split('\n')[0]
        content += f"{first_para}\n"

    content += f"\n## Key Insights\n\n"

    for insight in brainlift.insights[:5]:  # Top 5 insights
        content += f"- **{insight['title']}**\n"

    if brainlift.experts:
        content += f"\n## Key Experts Referenced\n\n"
        for expert in brainlift.experts[:5]:
            content += f"- {expert['name']} ({expert['organization']})\n"

    content += f"\n## Full BrainLift\n\n"
    content += f"See: [[BrainLift-{brainlift.title}]] for complete structured research\n"

    return filepath, content


def generate_framework_file(brainlift: BrainLift, vault_path: Path) -> str:
    """Convert BrainLift to framework file"""
    filename = f"{brainlift.title.replace(':', ' -').replace('/', '-')} Framework.md"
    filepath = vault_path / 'frameworks' / filename

    content = f"""---
type: framework
name: "{brainlift.title} Framework"
description: "{brainlift.purpose[:100]}..."
when_to_use: "When working with {brainlift.title.lower()}"
tags: ["brainlift", "framework"]
is_shareable: true
last_updated: 2026-05-04
---

# {brainlift.title} Framework

## Purpose

{brainlift.purpose}

## Core Principles (SPOVs)

"""

    for spov in brainlift.spovs:
        content += f"\n### Principle {spov['number']}: {spov['title']}\n\n"
        content += f"{spov['content'][:300]}...\n"

    content += f"\n## Key Insights for Application\n\n"

    for insight in brainlift.insights:
        content += f"### {insight['title']}\n\n"
        # Extract first sentence or paragraph
        first_part = insight['content'].split('.')[0] + '.'
        content += f"{first_part}\n\n"

    content += f"\n## Related Experts\n\n"
    for expert in brainlift.experts[:5]:
        content += f"- [[{expert['name']}]]\n"

    content += f"\n## Full Research\n\n"
    content += f"See: [[BrainLift-{brainlift.title}]] for complete structured research\n"

    return filepath, content


def extract_spovs_for_profile(brainlifts: List[BrainLift]) -> List[str]:
    """Extract top SPOVs to add to profile"""
    all_spovs = []

    for brainlift in brainlifts:
        for spov in brainlift.spovs:
            # Get first sentence as the SPOV
            first_sentence = spov['title']
            if len(first_sentence) > 150:
                first_sentence = first_sentence[:150] + "..."

            all_spovs.append({
                'text': first_sentence,
                'source': brainlift.title,
                'spov_num': spov['number']
            })

    return all_spovs


def extract_experts_for_people(brainlifts: List[BrainLift]) -> List[Dict]:
    """Extract unique experts to create people/ entries"""
    experts_map = {}

    for brainlift in brainlifts:
        for expert in brainlift.experts:
            name = expert['name']
            if name not in experts_map:
                experts_map[name] = {
                    'name': name,
                    'organization': expert['organization'],
                    'mentioned_in': [brainlift.title]
                }
            else:
                experts_map[name]['mentioned_in'].append(brainlift.title)

    return list(experts_map.values())


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Process BrainLifts')
    parser.add_argument('vault_path',
                       help='Path to second brain vault')
    parser.add_argument('--preview', action='store_true',
                       help='Preview what would be created')

    args = parser.parse_args()
    vault_path = Path(args.vault_path)

    # Find all BrainLifts in 00-Inbox
    inbox = vault_path / '00-Inbox'
    brainlift_files = list(inbox.glob('BrainLift-*.md'))

    if not brainlift_files:
        print("No BrainLift files found in 00-Inbox/")
        return 1

    print(f"Found {len(brainlift_files)} BrainLifts\n")

    # Parse all BrainLifts
    brainlifts = [BrainLift(f) for f in brainlift_files]

    # Categorize them
    sources = [bl for bl in brainlifts if categorize_brainlift(bl) == 'source']
    frameworks = [bl for bl in brainlifts if categorize_brainlift(bl) == 'framework']
    knowledge = [bl for bl in brainlifts if categorize_brainlift(bl) == 'knowledge']

    print("Categorization:")
    print(f"  Sources (your published work): {len(sources)}")
    for bl in sources:
        print(f"    - {bl.title}")
    print(f"\n  Frameworks (your methodologies): {len(frameworks)}")
    for bl in frameworks:
        print(f"    - {bl.title}")
    print(f"\n  Knowledge (reference material): {len(knowledge)}")
    for bl in knowledge:
        print(f"    - {bl.title}")

    # Extract SPOVs for profile
    spovs = extract_spovs_for_profile(brainlifts)
    print(f"\n  Total SPOVs extracted: {len(spovs)}")
    print(f"  Top 3 to consider adding to profile:")
    for spov in spovs[:3]:
        print(f"    - {spov['text'][:80]}... (from {spov['source']})")

    # Extract experts for people/
    experts = extract_experts_for_people(brainlifts)
    print(f"\n  Unique experts to create people/ entries: {len(experts)}")
    print(f"  Top 5:")
    for expert in experts[:5]:
        print(f"    - {expert['name']} - mentioned in {len(expert['mentioned_in'])} BrainLifts")

    if args.preview:
        print("\n=== PREVIEW MODE ===")
        print("Run without --preview to create files")
        return 0

    # Create files
    print("\n\nCreating files...\n")

    created = {
        'sources': 0,
        'frameworks': 0,
        'knowledge': 0,
        'moved_originals': 0
    }

    # Process sources
    for bl in sources:
        filepath, content = generate_source_file(bl, vault_path)
        filepath.write_text(content, encoding='utf-8')
        print(f"✅ Created source: {filepath.name}")
        created['sources'] += 1

    # Process frameworks
    for bl in frameworks:
        filepath, content = generate_framework_file(bl, vault_path)
        filepath.write_text(content, encoding='utf-8')
        print(f"✅ Created framework: {filepath.name}")
        created['frameworks'] += 1

    # Move originals to knowledge base (full BrainLifts preserved)
    knowledge_dir = vault_path / 'knowledge'
    for brainlift_file in brainlift_files:
        dest = knowledge_dir / brainlift_file.name
        brainlift_file.rename(dest)
        print(f"📦 Moved to knowledge: {brainlift_file.name}")
        created['moved_originals'] += 1

    print(f"\n{'='*60}")
    print(f"✅ Complete!")
    print(f"  Created {created['sources']} sources")
    print(f"  Created {created['frameworks']} frameworks")
    print(f"  Moved {created['moved_originals']} original BrainLifts to knowledge/")
    print(f"\n  Total SPOVs available: {len(spovs)}")
    print(f"  Total experts identified: {len(experts)}")
    print(f"\nNext steps:")
    print(f"1. Review new sources/ and frameworks/ files")
    print(f"2. Consider adding top SPOVs to David-Proctor-Profile.md")
    print(f"3. Create people/ entries for key experts")
    print(f"4. Update TRAVERSAL-INDEX.md")


if __name__ == "__main__":
    sys.exit(main() or 0)
