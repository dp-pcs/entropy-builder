#!/usr/bin/env python3
"""
Apply approved proposals from proposals.md
"""
import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple


class ProposalApplicator:
    """Applies approved changes from proposals.md"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.stats = {
            'accepted': 0,
            'rejected': 0,
            'edited': 0,
            'files_modified': set(),
            'items_processed': set(),
            'items_reviewed': set()  # All items seen in proposals (accept OR reject)
        }

    def parse_proposals(self, proposals_content: str) -> List[Dict]:
        """Parse proposals.md and extract approved actions"""
        approved_actions = []

        # First, parse MOC suggestions (if any)
        moc_section_match = re.search(
            r'## 🎯 Suggested New MOCs\n(.+?)(?=\n## 📋 Individual Item Proposals|\n## Item|$)',
            proposals_content,
            re.DOTALL
        )

        if moc_section_match:
            moc_section = moc_section_match.group(1)
            # Split by MOC suggestions
            moc_suggestions = re.split(r'^### MOC Suggestion:', moc_section, flags=re.MULTILINE)[1:]

            for moc_text in moc_suggestions:
                # Find CREATE MOC action
                action_match = re.search(r'### ACTION: CREATE MOC(.+?)(?=\n###|$)', moc_text, re.DOTALL)
                if not action_match:
                    continue

                action_text = action_match.group(1)

                # Check approval status
                if '[ACCEPT]' in action_text:
                    target_match = re.search(r'\*\*Target:\*\*\s*`([^`]+)`', action_text)
                    if target_match:
                        target_file = target_match.group(1)

                        # Extract MOC name from target path
                        moc_name = target_file.replace('mocs/', '').replace('-MOC.md', '').replace('-', ' ')

                        # Extract cluster items
                        items_match = re.search(r'\*\*Items:\*\*\n(.+?)(?=\n### ACTION)', moc_text, re.DOTALL)
                        cluster_items = []
                        if items_match:
                            item_lines = items_match.group(1).strip().split('\n')
                            for line in item_lines:
                                if line.startswith('- ') and not line.startswith('- ...'):
                                    cluster_items.append(line[2:].strip())

                        approved_actions.append({
                            'source_item': 'MOC_CLUSTER',
                            'action_type': 'create_moc',
                            'target_file': target_file,
                            'moc_name': moc_name,
                            'cluster_items': cluster_items,
                            'content': '',  # Will be generated
                            'section': None,
                            'status': 'accept'
                        })
                        self.stats['accepted'] += 1
                elif '[REJECT]' in action_text:
                    self.stats['rejected'] += 1

        # Then parse individual item proposals
        items = re.split(r'^## Item \d+:', proposals_content, flags=re.MULTILINE)[1:]

        for item_text in items:
            # Extract item filename
            filename_match = re.search(r'^(.+\.md)', item_text)
            if not filename_match:
                continue

            filename = filename_match.group(1).strip()

            # Track that we reviewed this item (regardless of accept/reject)
            self.stats['items_reviewed'].add(filename)

            # Find all actions in this item
            actions = re.split(r'^### ACTION \d+:', item_text, flags=re.MULTILINE)[1:]

            for action_text in actions:
                # Check approval status
                if '[ACCEPT]' in action_text:
                    status = 'accept'
                    self.stats['accepted'] += 1
                elif '[EDIT]' in action_text:
                    status = 'edit'
                    self.stats['edited'] += 1
                elif '[REJECT]' in action_text:
                    self.stats['rejected'] += 1
                    continue
                else:
                    # No marker, skip
                    continue

                # Extract action details
                action_type_match = re.search(r'^\s*(\w+)', action_text)
                target_match = re.search(r'\*\*Target:\*\*\s*`([^`]+)`', action_text)
                section_match = re.search(r'\*\*Section:\*\*\s*([^\n]+)', action_text)

                if not action_type_match or not target_match:
                    continue

                action_type = action_type_match.group(1).lower()
                target_file = target_match.group(1)
                section = section_match.group(1).strip() if section_match else None

                # Extract content
                if status == 'edit':
                    # User modified the diff - extract their version
                    diff_match = re.search(r'```diff\n(.+?)\n```', action_text, re.DOTALL)
                    if diff_match:
                        content = diff_match.group(1).replace('+ ', '').replace('+', '')
                    else:
                        continue
                else:
                    # Use original proposed content
                    diff_match = re.search(r'```diff\n(.+?)\n```', action_text, re.DOTALL)
                    if diff_match:
                        content = diff_match.group(1).replace('+ ', '').replace('+', '')
                    else:
                        continue

                approved_actions.append({
                    'source_item': filename,
                    'action_type': action_type,
                    'target_file': target_file,
                    'section': section,
                    'content': content.strip(),
                    'status': status
                })

        return approved_actions

    def apply_action(self, action: Dict):
        """Apply a single action"""
        target_path = self.vault_path / action['target_file']

        if action['action_type'] == 'create_moc':
            self._create_moc(target_path, action['moc_name'], action['cluster_items'])
        elif action['action_type'] in ['create', 'move_to_knowledge']:
            self._create_file(target_path, action['content'])
        elif action['action_type'] in ['update', 'wikilink']:
            self._update_file(target_path, action['content'], action['section'])

        self.stats['files_modified'].add(action['target_file'])
        if action['source_item'] != 'MOC_CLUSTER':
            self.stats['items_processed'].add(action['source_item'])

    def _create_moc(self, path: Path, moc_name: str, cluster_items: List[str]):
        """Create a new MOC file from topic cluster"""
        # Generate MOC content
        content = f"""---
type: moc
name: "{moc_name}"
description: "Navigation hub for {moc_name.lower()} resources"
tags: ["moc", "auto-generated"]
created: {datetime.now().strftime('%Y-%m-%d')}
---

# {moc_name}

> **Auto-generated MOC** - Created from topic cluster detection

## Overview

This MOC was automatically created because multiple inbox items shared the topic "{moc_name.lower()}". Review and expand as needed.

## Related Content

"""
        # Add wikilinks to all cluster items
        for item in cluster_items:
            item_name = item.replace('.md', '')
            content += f"- [[{item_name}]]\n"

        content += """
## Key Concepts

<!-- Add key concepts here -->

## Frameworks

<!-- Link to related frameworks here -->

## People

<!-- Link to relevant experts here -->

---

*This MOC was auto-generated by inbox processing. Edit to add structure and context.*
"""

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        print(f"  ✨ Created MOC: {path}")
        print(f"     Links {len(cluster_items)} related items")

    def _create_file(self, path: Path, content: str):
        """Create a new file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        print(f"  ✅ Created: {path}")

    def _update_file(self, path: Path, content: str, section: str = None):
        """Update an existing file"""
        if not path.exists():
            print(f"  ⚠️  File not found: {path}, skipping")
            return

        existing_content = path.read_text(encoding='utf-8')

        if section:
            # Try to insert in specific section
            section_pattern = f"## {re.escape(section)}"
            if re.search(section_pattern, existing_content):
                # Insert after section header
                updated_content = re.sub(
                    f"({section_pattern}.*?\n)",
                    f"\\1\n{content}\n",
                    existing_content,
                    count=1,
                    flags=re.DOTALL
                )
            else:
                # Section doesn't exist, create it at end
                updated_content = existing_content.rstrip() + f"\n\n## {section}\n\n{content}\n"
        else:
            # Append at end
            updated_content = existing_content.rstrip() + f"\n\n{content}\n"

        path.write_text(updated_content, encoding='utf-8')
        print(f"  ✅ Updated: {path}")

    def archive_processed_items(self):
        """Move processed items to archive"""
        archive_dir = self.vault_path / 'raw' / 'processed' / datetime.now().strftime('%Y-%m-%d')
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Find items to archive (all reviewed items, not just accepted ones)
        inbox_folders = ['00-Inbox', 'Clippings', 'raw']

        for filename in self.stats['items_reviewed']:
            for folder in inbox_folders:
                source_path = self.vault_path / folder / filename
                if source_path.exists():
                    dest_path = archive_dir / filename
                    shutil.move(str(source_path), str(dest_path))
                    print(f"  📦 Archived: {filename} → {dest_path}")
                    break

    def update_traversal_index(self):
        """Update TRAVERSAL-INDEX.md with new file count"""
        index_path = self.vault_path / 'TRAVERSAL-INDEX.md'
        if not index_path.exists():
            return

        content = index_path.read_text(encoding='utf-8')

        # Count total .md files (excluding index and proposals)
        total_files = len(list(self.vault_path.rglob('*.md'))) - 2  # Exclude index and proposals

        # Update total nodes count
        updated_content = re.sub(
            r'\*\*Total Nodes\*\*:\s*\d+',
            f'**Total Nodes**: {total_files}',
            content
        )

        # Update last updated date
        updated_content = re.sub(
            r'\*\*Last Updated\*\*:\s*[\d-]+',
            f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}",
            updated_content
        )

        index_path.write_text(updated_content, encoding='utf-8')
        print(f"  ✅ Updated TRAVERSAL-INDEX.md")

    def generate_summary(self) -> str:
        """Generate processing summary"""
        summary = [
            "# Processing Summary",
            f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"\n## Statistics",
            f"- ✅ Actions accepted: {self.stats['accepted']}",
            f"- ✏️  Actions edited: {self.stats['edited']}",
            f"- ❌ Actions rejected: {self.stats['rejected']}",
            f"- 📝 Files modified: {len(self.stats['files_modified'])}",
            f"- 📦 Items archived: {len(self.stats['items_reviewed'])}",
            f"\n## Modified Files",
        ]

        for filename in sorted(self.stats['files_modified']):
            summary.append(f"- {filename}")

        summary.append("\n## Archived Items")
        for filename in sorted(self.stats['items_reviewed']):
            summary.append(f"- {filename}")

        summary.append("\n---")
        summary.append("\n✅ **Inbox processing complete!**")
        summary.append(f"\nProcessed items moved to: `raw/processed/{datetime.now().strftime('%Y-%m-%d')}/`")

        return "\n".join(summary)


def main():
    """Main entry point"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Apply approved proposals from proposals.md')
    parser.add_argument('vault_path', nargs='?',
                       default=os.path.expanduser("~/David-Proctor-Second-Brain"),
                       help='Path to second brain vault (default: ~/David-Proctor-Second-Brain)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Only process first N items (for testing)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')

    args = parser.parse_args()

    vault_path = args.vault_path
    proposals_path = Path(vault_path) / "proposals.md"

    if not proposals_path.exists():
        print("❌ proposals.md not found. Run analyzer.py first.")
        return

    print(f"Applying approved proposals from: {proposals_path}")
    if args.limit:
        print(f"⚠️  LIMIT: Only processing first {args.limit} items\n")
    if args.dry_run:
        print("⚠️  DRY RUN: No changes will be made\n")
    else:
        print()

    # Read proposals
    proposals_content = proposals_path.read_text(encoding='utf-8')

    # Parse and apply
    applicator = ProposalApplicator(vault_path)
    actions = applicator.parse_proposals(proposals_content)

    # Apply limit if specified
    if args.limit:
        # Group actions by item number
        items_processed = set()
        limited_actions = []
        for action in actions:
            # Extract item number from source_item if we haven't hit limit
            if len(items_processed) < args.limit:
                items_processed.add(action['source_item'])
                limited_actions.append(action)
            elif action['source_item'] in items_processed:
                # Include remaining actions from already-processed items
                limited_actions.append(action)

        actions = limited_actions
        print(f"Limited to {len(items_processed)} items, {len(actions)} actions\n")

    if not actions:
        print("No actions marked as [ACCEPT] or [EDIT].")
        # Still check if there are items to archive (all rejected)
        if applicator.stats['items_reviewed']:
            print(f"Found {len(applicator.stats['items_reviewed'])} reviewed item(s) to archive.\n")
            if not args.dry_run:
                print("Archiving reviewed items...")
                applicator.archive_processed_items()
                print(f"\n✅ Archived {len(applicator.stats['items_reviewed'])} item(s) to raw/processed/")
            else:
                print("DRY RUN - Would archive these items:")
                for filename in sorted(applicator.stats['items_reviewed']):
                    print(f"  📦 {filename}")
        else:
            print("Nothing to do.")
        return

    print(f"Found {len(actions)} approved actions\n")

    if args.dry_run:
        print("DRY RUN - Would apply these changes:")
        for i, action in enumerate(actions, 1):
            print(f"\n{i}. {action['action_type'].upper()}: {action['target_file']}")
            if action.get('section'):
                print(f"   Section: {action['section']}")
        print("\n✅ Dry run complete. Run without --dry-run to apply changes.")
        return

    print("Applying changes...")

    for action in actions:
        applicator.apply_action(action)

    # Archive processed items
    print("\nArchiving processed items...")
    applicator.archive_processed_items()

    # Update TRAVERSAL-INDEX
    print("\nUpdating TRAVERSAL-INDEX...")
    applicator.update_traversal_index()

    # Generate summary
    summary = applicator.generate_summary()
    summary_path = Path(vault_path) / "processing-summary.md"
    summary_path.write_text(summary, encoding='utf-8')

    print(f"\n{summary}")
    print(f"\n📄 Full summary: {summary_path}")


if __name__ == "__main__":
    main()
