#!/usr/bin/env python3
"""
Setup script for inbox processing system

Creates necessary directories and provides configuration guidance
"""
from pathlib import Path
import sys


def setup_inbox_structure(vault_path: Path):
    """Create all necessary directories for inbox processing"""

    directories = [
        # Inbox folders (where unprocessed items go)
        '00-Inbox',
        'Clippings',
        'raw',
        'raw/assets',           # For Karpathy pattern: downloaded images/media
        'raw/processed',        # Archive for processed items

        # Core brain structure (if they don't exist)
        'frameworks',
        'mocs',
        'knowledge',
        'sources',
        'people',
    ]

    created = []
    existed = []

    for dir_name in directories:
        dir_path = vault_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_name)
        else:
            existed.append(dir_name)

    return created, existed


def create_gitignore(vault_path: Path):
    """Create .gitignore for raw/assets if needed"""
    gitignore_path = vault_path / 'raw' / '.gitignore'

    if not gitignore_path.exists():
        content = """# Ignore downloaded assets (large files, copyrighted images, etc.)
assets/*

# Keep processed markdown
!processed/
"""
        gitignore_path.write_text(content, encoding='utf-8')
        return True
    return False


def create_readme(vault_path: Path):
    """Create README in raw/ folder explaining the structure"""
    readme_path = vault_path / 'raw' / 'README.md'

    if not readme_path.exists():
        content = """# Raw Folder - Inbox Processing

This folder follows the Karpathy LLM Wiki pattern for managing unprocessed content.

## Structure

- **`/raw/*.md`** - Unprocessed markdown files (articles, notes, clippings)
- **`/raw/assets/`** - Downloaded images, PDFs, media referenced by markdown files
- **`/raw/processed/YYYY-MM-DD/`** - Archive of processed items by date

## Workflow

1. **Capture** - Drop files here (manually or via Obsidian clipper)
2. **Analyze** - Run inbox analyzer to generate proposals
3. **Review** - Mark proposals as ACCEPT/REJECT/EDIT
4. **Apply** - Execute approved changes, files move to processed/

## Obsidian Clipper Setup

1. Install "Web Clipper" plugin in Obsidian
2. Configure clipper settings:
   - **Save location:** `Clippings/` (or `raw/`)
   - **Download images:** Yes
   - **Image folder:** `raw/assets/`
   - **Template:** Use frontmatter template

3. When clipping articles:
   - Images download to `raw/assets/`
   - Markdown references: `![](raw/assets/image-name.jpg)`
   - When file moves to knowledge/, links stay intact

## BrainLift Imports

If importing structured research (BrainLifts) from Workflowy:

1. Export BrainLifts section from Workflowy → one big .md file
2. Run `split-brainlifts.py` → creates individual BrainLift-*.md in 00-Inbox/
3. Run `process-brainlifts.py` → extracts SPOVs, creates sources/frameworks

See: `process-inbox` skill documentation for details
"""
        readme_path.write_text(content, encoding='utf-8')
        return True
    return False


def print_clipper_instructions():
    """Print Obsidian clipper setup instructions"""
    return """
📎 Obsidian Web Clipper Setup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Install "Web Clipper" plugin:
   Settings → Community Plugins → Browse → Search "Web Clipper"

2. Configure clipper:
   Settings → Web Clipper → Options:

   ✓ Save location: Clippings/
   ✓ Download images: ON
   ✓ Image save location: raw/assets/
   ✓ Add frontmatter: ON

   Frontmatter template:
   ```yaml
   ---
   type: clipping
   source: {{url}}
   author: {{author}}
   date_clipped: {{date}}
   ---
   ```

3. Browser extension:
   - Chrome: Install from Chrome Web Store
   - Firefox: Install from Firefox Add-ons
   - Safari: Install from App Store

4. Test it:
   - Browse to any article
   - Click clipper extension
   - Choose "Save to Obsidian"
   - File appears in Clippings/
   - Images appear in raw/assets/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Next: Add items to inbox, then run:
  python3 .agent/skills/process-inbox/analyzer.py ~/your-vault
"""


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Setup inbox processing structure')
    parser.add_argument('vault_path',
                       help='Path to your second brain vault')

    args = parser.parse_args()
    vault_path = Path(args.vault_path)

    if not vault_path.exists():
        print(f"❌ Vault not found: {vault_path}")
        print("Create your vault first or provide correct path")
        return 1

    print(f"Setting up inbox processing in: {vault_path}\n")

    # Create directories
    created, existed = setup_inbox_structure(vault_path)

    if created:
        print("✅ Created directories:")
        for d in created:
            print(f"   - {d}/")

    if existed:
        print("\n✓ Already existed:")
        for d in existed:
            print(f"   - {d}/")

    # Create supporting files
    print()
    if create_gitignore(vault_path):
        print("✅ Created raw/.gitignore (excludes assets from git)")

    if create_readme(vault_path):
        print("✅ Created raw/README.md (workflow documentation)")

    # Print clipper instructions
    print(print_clipper_instructions())

    print("✅ Setup complete!")
    print(f"\nYour vault is ready for inbox processing.")
    print(f"\nNext steps:")
    print(f"1. Configure Obsidian clipper (see instructions above)")
    print(f"2. Add items to inbox (00-Inbox/, Clippings/, or raw/)")
    print(f"3. Run analyzer: python3 .agent/skills/process-inbox/analyzer.py {vault_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
