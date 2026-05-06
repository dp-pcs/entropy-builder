#!/usr/bin/env python3
"""
Split Workflowy BrainLift export into individual markdown files

Takes a single Workflowy markdown export containing multiple BrainLifts
and splits it into separate files (one per BrainLift).
"""
import re
from pathlib import Path
from typing import List, Tuple
import sys


def clean_filename(title: str) -> str:
    """Convert BrainLift title to safe filename"""
    # Remove markdown links [text](url) -> text
    title = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', title)

    # Remove #tags
    title = re.sub(r'#\w+', '', title)

    # Remove special chars, keep alphanumeric, spaces, hyphens
    title = re.sub(r'[^\w\s-]', '', title)

    # Collapse multiple spaces
    title = re.sub(r'\s+', ' ', title)

    # Trim and limit length
    title = title.strip()[:100]

    return title


def split_brainlifts(input_file: Path) -> List[Tuple[str, str]]:
    """Split workflowy export into individual brainlifts

    Returns list of (title, content) tuples
    """
    content = input_file.read_text(encoding='utf-8')
    lines = content.split('\n')

    brainlifts = []
    current_title = None
    current_lines = []

    for i, line in enumerate(lines):
        # Check if this is a top-level bullet (new BrainLift)
        if line.startswith('- ') and not line.startswith('  '):
            # Save previous BrainLift if exists
            if current_title and current_lines:
                brainlift_content = '\n'.join(current_lines)
                brainlifts.append((current_title, brainlift_content))

            # Start new BrainLift
            current_title = line[2:].strip()  # Remove "- " prefix
            current_lines = [line]

        # Skip header lines and empty top-level content
        elif line.startswith('#') or (not line.strip() and not current_lines):
            continue

        # Add to current BrainLift
        elif current_title:
            current_lines.append(line)

    # Don't forget the last BrainLift
    if current_title and current_lines:
        brainlift_content = '\n'.join(current_lines)
        brainlifts.append((current_title, brainlift_content))

    return brainlifts


def write_brainlifts(brainlifts: List[Tuple[str, str]], output_dir: Path):
    """Write each brainlift to a separate file"""
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        'total': len(brainlifts),
        'written': 0,
        'skipped': 0,
        'files': []
    }

    for title, content in brainlifts:
        # Skip templates and empty
        if '#template' in title.lower() or len(content.strip()) < 100:
            print(f"  ⏭️  Skipping: {title[:60]}... (template or too short)")
            stats['skipped'] += 1
            continue

        # Clean filename
        filename = clean_filename(title)
        if not filename:
            filename = f"Untitled-BrainLift-{stats['written']}"

        # Add BrainLift prefix
        filename = f"BrainLift-{filename}.md"
        filepath = output_dir / filename

        # Add frontmatter
        frontmatter = f"""---
type: brainlift
title: "{title}"
source: workflowy
imported: 2026-05-04
---

"""
        full_content = frontmatter + content

        # Write file
        filepath.write_text(full_content, encoding='utf-8')
        print(f"  ✅ Created: {filename}")
        stats['written'] += 1
        stats['files'].append(str(filepath))

    return stats


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Split Workflowy BrainLift export')
    parser.add_argument('input_file',
                       help='Path to Workflowy markdown export')
    parser.add_argument('--output-dir',
                       default=None,
                       help='Output directory (default: same as input + "/brainlifts")')
    parser.add_argument('--preview',
                       action='store_true',
                       help='Preview what would be created without writing files')

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"❌ File not found: {input_path}")
        return 1

    # Default output dir
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = input_path.parent / 'brainlifts'

    print(f"Reading: {input_path}")
    print(f"Output:  {output_dir}\n")

    # Split
    brainlifts = split_brainlifts(input_path)
    print(f"Found {len(brainlifts)} BrainLifts\n")

    if args.preview:
        print("PREVIEW MODE - Would create:\n")
        for i, (title, content) in enumerate(brainlifts, 1):
            filename = clean_filename(title)
            word_count = len(content.split())
            skip_reason = ""

            if '#template' in title.lower():
                skip_reason = " [SKIP: template]"
            elif word_count < 50:
                skip_reason = f" [SKIP: too short - {word_count} words]"

            print(f"{i:2}. BrainLift-{filename}.md ({word_count:,} words){skip_reason}")

        print(f"\nRun without --preview to create files in: {output_dir}")
    else:
        # Write files
        print("Creating files...\n")
        stats = write_brainlifts(brainlifts, output_dir)

        print(f"\n{'='*60}")
        print(f"✅ Complete!")
        print(f"   Total found: {stats['total']}")
        print(f"   Written:     {stats['written']}")
        print(f"   Skipped:     {stats['skipped']}")
        print(f"\nFiles created in: {output_dir}")
        print(f"\nNext steps:")
        print(f"1. Review the files in {output_dir}")
        print(f"2. Move them to 00-Inbox/ to process with inbox analyzer")
        print(f"3. Run: python3 analyzer.py ~/David-Proctor-Second-Brain")


if __name__ == "__main__":
    sys.exit(main() or 0)
