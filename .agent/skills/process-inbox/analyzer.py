#!/usr/bin/env python3
"""
Inbox Analyzer - Analyzes unprocessed second brain items and generates proposals
"""
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict


@dataclass
class InboxItem:
    """Represents an unprocessed item in the inbox"""
    filename: str
    path: str
    content: str
    frontmatter: Dict
    word_count: int


@dataclass
class Relationship:
    """Represents a relationship between inbox item and brain content"""
    target_file: str
    target_type: str  # framework, moc, knowledge, source, person
    confidence: float  # 0.0 to 1.0
    reason: str
    key_insight: str


@dataclass
class ProposedAction:
    """Represents a proposed integration action"""
    action_type: str  # update, wikilink, create, delete
    target_file: str
    section: str  # which section to modify
    content: str  # the actual text to add/modify
    diff_preview: str  # git-style diff
    rationale: str


@dataclass
class ItemProposal:
    """Complete proposal for one inbox item"""
    item: InboxItem
    relationships: List[Relationship]
    actions: List[ProposedAction]
    recommendation: str  # process, skip, flag_for_review


class BrainAnalyzer:
    """Analyzes second brain structure"""

    def __init__(self, vault_path: str, llm_analyzer=None):
        self.vault_path = Path(vault_path)
        self.structure = self._load_brain_structure()
        self.llm_analyzer = llm_analyzer  # Optional LLM for semantic analysis

    def _load_brain_structure(self) -> Dict:
        """Load brain structure from TRAVERSAL-INDEX and filesystem"""
        structure = {
            'frameworks': {},
            'mocs': {},
            'knowledge': {},
            'sources': {},
            'people': {}
        }

        # Load frameworks
        frameworks_dir = self.vault_path / 'frameworks'
        if frameworks_dir.exists():
            for f in frameworks_dir.glob('*.md'):
                content = f.read_text(encoding='utf-8')
                frontmatter = self._extract_frontmatter(content)
                structure['frameworks'][f.stem] = {
                    'path': str(f),
                    'content': content,
                    'frontmatter': frontmatter
                }

        # Load MOCs
        mocs_dir = self.vault_path / 'mocs'
        if mocs_dir.exists():
            for f in mocs_dir.glob('*.md'):
                content = f.read_text(encoding='utf-8')
                frontmatter = self._extract_frontmatter(content)
                structure['mocs'][f.stem] = {
                    'path': str(f),
                    'content': content,
                    'frontmatter': frontmatter
                }

        # Load knowledge
        knowledge_dir = self.vault_path / 'knowledge'
        if knowledge_dir.exists():
            for f in knowledge_dir.glob('*.md'):
                content = f.read_text(encoding='utf-8')
                frontmatter = self._extract_frontmatter(content)
                structure['knowledge'][f.stem] = {
                    'path': str(f),
                    'content': content,
                    'frontmatter': frontmatter
                }

        return structure

    def _extract_frontmatter(self, content: str) -> Dict:
        """Extract YAML frontmatter from markdown"""
        match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if not match:
            return {}

        # Simple YAML parsing (handles basic cases)
        frontmatter = {}
        for line in match.group(1).split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip().strip('"\'')

        return frontmatter

    def find_relationships(self, item: InboxItem) -> List[Relationship]:
        """Find relationships between inbox item and existing brain content"""

        # Use LLM analysis if available
        if self.llm_analyzer:
            return self._find_relationships_with_llm(item)

        # Otherwise use keyword matching
        return self._find_relationships_keyword(item)

    def _find_relationships_with_llm(self, item: InboxItem) -> List[Relationship]:
        """Find relationships using LLM semantic analysis"""
        from llm_analyzer import LLMAnalysis

        # Get existing MOC and framework names
        moc_names = list(self.structure['mocs'].keys())
        framework_names = list(self.structure['frameworks'].keys())

        # Analyze item with LLM
        try:
            analysis = self.llm_analyzer.analyze_item(
                content=item.content,
                existing_mocs=moc_names,
                existing_frameworks=framework_names
            )
        except Exception as e:
            print(f"  ⚠️  LLM analysis failed, falling back to keywords: {e}")
            return self._find_relationships_keyword(item)

        relationships = []

        # Add suggested MOCs from LLM
        for moc_name in analysis.suggested_mocs:
            if moc_name in self.structure['mocs']:
                relationships.append(Relationship(
                    target_file=f"mocs/{moc_name}.md",
                    target_type="moc",
                    confidence=analysis.confidence,
                    reason=f"LLM detected: {analysis.reasoning}",
                    key_insight=analysis.key_insight
                ))

        # Add suggested frameworks from LLM
        for framework_name in analysis.suggested_frameworks:
            if framework_name in self.structure['frameworks']:
                relationships.append(Relationship(
                    target_file=f"frameworks/{framework_name}.md",
                    target_type="framework",
                    confidence=analysis.confidence,
                    reason=f"LLM detected: {analysis.reasoning}",
                    key_insight=analysis.key_insight
                ))

        # Sort by confidence
        relationships.sort(key=lambda r: r.confidence, reverse=True)

        return relationships[:5]  # Top 5

    def _find_relationships_keyword(self, item: InboxItem) -> List[Relationship]:
        """Find relationships using keyword matching (original method)"""
        relationships = []

        # Extract key concepts from item
        concepts = self._extract_concepts(item.content)

        # Check frameworks
        for name, framework in self.structure['frameworks'].items():
            score, reason = self._calculate_relevance(
                item.content,
                framework['content'],
                concepts
            )
            if score > 0.5:
                relationships.append(Relationship(
                    target_file=f"frameworks/{name}.md",
                    target_type="framework",
                    confidence=score,
                    reason=reason,
                    key_insight=self._extract_key_insight(item.content, framework['content'])
                ))

        # Check MOCs
        for name, moc in self.structure['mocs'].items():
            score, reason = self._calculate_relevance(
                item.content,
                moc['content'],
                concepts
            )
            if score > 0.5:
                relationships.append(Relationship(
                    target_file=f"mocs/{name}.md",
                    target_type="moc",
                    confidence=score,
                    reason=reason,
                    key_insight=self._extract_key_insight(item.content, moc['content'])
                ))

        # Sort by confidence
        relationships.sort(key=lambda r: r.confidence, reverse=True)

        return relationships[:5]  # Top 5 relationships

    def _extract_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content"""
        # Remove frontmatter
        content = re.sub(r'^---.*?---\n', '', content, flags=re.DOTALL)

        # Extract title
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        concepts = [title_match.group(1)] if title_match else []

        # Extract common technical terms (basic implementation)
        # This could be enhanced with NLP/embeddings
        tech_terms = re.findall(
            r'\b(OGP|federation|agent|AI|framework|protocol|architecture|API|MCP|OpenClaw|Hermes)\b',
            content,
            re.IGNORECASE
        )
        concepts.extend(set(tech_terms))

        return concepts

    def _calculate_relevance(self, content1: str, content2: str, concepts: List[str]) -> Tuple[float, str]:
        """Calculate relevance score between two pieces of content"""
        # Simple keyword-based scoring (could be enhanced with embeddings)
        matches = 0
        total = len(concepts)

        if total == 0:
            return 0.0, "No clear concepts identified"

        matching_concepts = []
        for concept in concepts:
            if concept.lower() in content2.lower():
                matches += 1
                matching_concepts.append(concept)

        score = matches / total

        if matching_concepts:
            reason = f"Shares concepts: {', '.join(matching_concepts[:3])}"
        else:
            reason = "No direct concept overlap"

        return score, reason

    def _extract_key_insight(self, item_content: str, target_content: str) -> str:
        """Extract the key insight from item that relates to target"""
        # Remove frontmatter first
        content = re.sub(r'^---.*?---\n', '', item_content, flags=re.DOTALL)

        # Remove title (first # heading)
        content = re.sub(r'^#\s+.+$', '', content, flags=re.MULTILINE)

        # Find first substantial paragraph in item
        paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 100]

        if paragraphs:
            # Return first paragraph, truncated to 250 chars
            insight = paragraphs[0][:250]
            if len(paragraphs[0]) > 250:
                insight += "..."
            return insight

        return "See full content for details"


class ProposalGenerator:
    """Generates integration proposals"""

    def __init__(self, analyzer: BrainAnalyzer):
        self.analyzer = analyzer

    def generate_proposals(self, item: InboxItem, relationships: List[Relationship]) -> ItemProposal:
        """Generate proposals for integrating an inbox item"""
        actions = []

        if not relationships:
            # No clear relationships - suggest archiving or manual review
            return ItemProposal(
                item=item,
                relationships=[],
                actions=[],
                recommendation="flag_for_review"
            )

        # Generate actions based on top relationships
        for rel in relationships[:3]:  # Top 3 relationships

            # ACTION 1: Update existing content
            if rel.target_type in ['framework', 'knowledge']:
                actions.append(self._create_update_action(item, rel))

            # ACTION 2: Add wikilink
            actions.append(self._create_wikilink_action(item, rel))

        # ACTION 3: Create new knowledge doc if highly relevant new content
        if relationships[0].confidence > 0.8:
            create_action = self._create_new_doc_action(item, relationships[0])
            if create_action:
                actions.append(create_action)

        return ItemProposal(
            item=item,
            relationships=relationships,
            actions=actions,
            recommendation="process"
        )

    def _create_update_action(self, item: InboxItem, rel: Relationship) -> ProposedAction:
        """Create action to update existing document"""
        # Extract a relevant quote or insight
        insight = rel.key_insight

        # Create diff
        addition = f"\n**From [[{item.filename.replace('.md', '')}]]:**\n{insight}\n"

        return ProposedAction(
            action_type="update",
            target_file=rel.target_file,
            section="Real World Examples" if rel.target_type == "framework" else "Related Content",
            content=addition,
            diff_preview=f"+ {addition}",
            rationale=f"Adds concrete example to {rel.target_file}"
        )

    def _create_wikilink_action(self, item: InboxItem, rel: Relationship) -> ProposedAction:
        """Create action to add wikilink"""
        link_text = f"[[{item.filename.replace('.md', '')}]]"

        return ProposedAction(
            action_type="wikilink",
            target_file=rel.target_file,
            section="Related Content",
            content=f"- {link_text}\n",
            diff_preview=f"+ - {link_text}",
            rationale=f"Cross-links related content ({int(rel.confidence * 100)}% confidence)"
        )

    def _create_new_doc_action(self, item: InboxItem, rel: Relationship) -> ProposedAction:
        """Create action to move clipping to knowledge base"""
        # Only suggest if item is substantial and highly relevant
        if item.word_count < 500 or rel.confidence < 0.85:
            return None

        new_filename = f"knowledge/{item.filename}"

        return ProposedAction(
            action_type="move_to_knowledge",
            target_file=new_filename,
            section="",
            content=item.content,
            diff_preview=f"+ Move to knowledge base: {new_filename}",
            rationale=f"Substantial reference material ({item.word_count} words, {int(rel.confidence * 100)}% confidence) worth preserving in knowledge base"
        )


def extract_topic_from_item(item: InboxItem) -> List[str]:
    """Extract potential topic keywords from an item

    Returns list of topic keywords sorted by relevance
    """
    # Extract from filename (usually most relevant)
    filename_clean = item.filename.replace('.md', '').replace('-', ' ').replace('_', ' ')

    # Extract from title in content
    title_match = re.search(r'^#\s+(.+)$', item.content, re.MULTILINE)
    title = title_match.group(1) if title_match else filename_clean

    # Common stop words to ignore
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'should', 'could', 'may', 'might', 'can', 'this', 'that', 'these',
        'those', 'what', 'which', 'who', 'how', 'why', 'when', 'where'
    }

    # Extract multi-word phrases (capitalized sequences, hyphenated terms)
    phrases = re.findall(r'(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+|[A-Z]{2,}|[a-z]+-[a-z]+)', title)

    # Extract significant words (3+ chars, not stop words)
    words = [w.lower() for w in re.findall(r'\b[A-Za-z]{3,}\b', title)
             if w.lower() not in stop_words]

    # Combine: phrases first (more specific), then words
    topics = []
    topics.extend(phrases)
    topics.extend([w for w in words if w not in ' '.join(phrases).lower()])

    return topics[:5]  # Top 5 most relevant


def detect_topic_clusters(items: List[InboxItem], min_cluster_size: int = 3) -> Dict[str, List[InboxItem]]:
    """Detect clusters of items that share topics

    Returns dict of {topic: [items]} for topics with min_cluster_size+ items
    """
    # Build topic -> items mapping
    topic_items = defaultdict(list)

    for item in items:
        topics = extract_topic_from_item(item)
        for topic in topics:
            topic_items[topic.lower()].append(item)

    # Filter to clusters with min_cluster_size+ items
    clusters = {
        topic: items
        for topic, items in topic_items.items()
        if len(items) >= min_cluster_size
    }

    # Sort by cluster size (largest first)
    clusters = dict(sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True))

    return clusters


def scan_inbox(vault_path: str, inbox_folders: List[str] = None) -> List[InboxItem]:
    """Scan inbox folders for unprocessed items

    Only scans top-level .md files in each folder.
    Subdirectories (like raw/assets/, raw/processed/) are ignored.
    """
    if inbox_folders is None:
        inbox_folders = ['00-Inbox', 'Clippings', 'raw']

    items = []
    vault = Path(vault_path)

    for folder in inbox_folders:
        folder_path = vault / folder
        if not folder_path.exists():
            continue

        # Only scan top-level .md files (ignores subdirectories like assets/, processed/)
        for md_file in folder_path.glob('*.md'):
            # Skip if it's actually in a subdirectory (extra safety)
            if md_file.parent != folder_path:
                continue

            content = md_file.read_text(encoding='utf-8')
            frontmatter = BrainAnalyzer(vault_path)._extract_frontmatter(content)
            word_count = len(content.split())

            items.append(InboxItem(
                filename=md_file.name,
                path=str(md_file),
                content=content,
                frontmatter=frontmatter,
                word_count=word_count
            ))

    return items


def generate_proposals_markdown(proposals: List[ItemProposal], clusters: Dict[str, List[InboxItem]] = None) -> str:
    """Generate proposals.md file content"""
    output = [
        "# Inbox Processing Proposals",
        f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Items Analyzed:** {len(proposals)}",
        "\n---\n"
    ]

    # Add MOC creation suggestions if clusters detected
    if clusters:
        output.append("\n## 🎯 Suggested New MOCs\n")
        output.append("**Topic clusters detected** - Consider creating MOCs for these topics:\n")

        for topic, cluster_items in clusters.items():
            # Clean up topic name for MOC title
            moc_name = topic.replace('-', ' ').title()
            moc_filename = f"{moc_name.replace(' ', '-')}-MOC.md"

            output.append(f"\n### MOC Suggestion: {moc_name}")
            output.append(f"**Items in cluster:** {len(cluster_items)}")
            output.append(f"**Detected topic:** {topic}")
            output.append("\n**Items:**")
            for item in cluster_items[:5]:  # Show first 5
                output.append(f"- {item.filename}")
            if len(cluster_items) > 5:
                output.append(f"- ... and {len(cluster_items) - 5} more")

            output.append("\n### ACTION: CREATE MOC")
            output.append(f"**Target:** `mocs/{moc_filename}`")
            output.append(f"**Rationale:** {len(cluster_items)} items about '{topic}' suggest new navigation hub")
            output.append("\n```diff")
            output.append(f"+ Create new MOC: {moc_name}")
            output.append(f"+ Links {len(cluster_items)} related items")
            output.append("```")
            output.append("\n[ACCEPT] [REJECT]\n")
            output.append("\n---\n")

        output.append("\n## 📋 Individual Item Proposals\n")

    for i, proposal in enumerate(proposals, 1):
        output.append(f"\n## Item {i}: {proposal.item.filename}\n")
        output.append(f"**Word Count:** {proposal.item.word_count}")
        output.append(f"**Path:** `{proposal.item.path}`")

        if proposal.relationships:
            output.append("\n**Relationships:**\n")
            for rel in proposal.relationships[:3]:
                output.append(f"- {rel.target_file} ({int(rel.confidence * 100)}% confidence)")
                output.append(f"  - {rel.reason}")
                output.append(f"  - Key insight: *{rel.key_insight[:100]}...*")

        if proposal.actions:
            output.append("\n**Proposed Actions:**\n")
            for j, action in enumerate(proposal.actions, 1):
                output.append(f"\n### ACTION {j}: {action.action_type.upper()}")
                output.append(f"**Target:** `{action.target_file}`")
                if action.section:
                    output.append(f"**Section:** {action.section}")
                output.append(f"**Rationale:** {action.rationale}")
                output.append("\n```diff")
                output.append(action.diff_preview)
                output.append("```")
                output.append("\n[ACCEPT] [REJECT] [EDIT]\n")
        else:
            output.append("\n**Recommendation:** FLAG FOR MANUAL REVIEW")
            output.append("No clear relationships found. Consider:\n")
            output.append("- Creating a new framework if this introduces new methodology")
            output.append("- Adding to knowledge/ if it's reference material")
            output.append("- Archiving if not relevant to current brain focus\n")

        output.append("\n---\n")

    return "\n".join(output)


def main():
    """Main entry point"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Generate proposals for inbox items')
    parser.add_argument('vault_path', nargs='?',
                       default=os.path.expanduser("~/David-Proctor-Second-Brain"),
                       help='Path to second brain vault (default: ~/David-Proctor-Second-Brain)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Only analyze first N items (for testing)')
    parser.add_argument('--use-ai', action='store_true',
                       help='Use LLM for semantic analysis (requires API key)')
    parser.add_argument('--provider', choices=['anthropic', 'openai'], default='anthropic',
                       help='LLM provider (default: anthropic)')
    parser.add_argument('--api-key', default=None,
                       help='API key (or set ANTHROPIC_API_KEY/OPENAI_API_KEY env var)')
    parser.add_argument('--model', default=None,
                       help='Override default model')

    args = parser.parse_args()
    vault_path = args.vault_path

    # Initialize LLM analyzer if requested
    llm_analyzer = None
    if args.use_ai:
        try:
            from llm_analyzer import LLMAnalyzer
            print(f"Initializing {args.provider} LLM analysis...")
            llm_analyzer = LLMAnalyzer(
                provider=args.provider,
                api_key=args.api_key,
                model=args.model
            )
            print(f"✅ LLM ready: {llm_analyzer.model}")
        except Exception as e:
            print(f"⚠️  LLM initialization failed: {e}")
            print("Falling back to keyword-based analysis\n")
            llm_analyzer = None

    print(f"Scanning inbox in: {vault_path}")

    # Scan inbox
    items = scan_inbox(vault_path)
    print(f"Found {len(items)} unprocessed items")

    if args.limit:
        items = items[:args.limit]
        print(f"⚠️  LIMIT: Only analyzing first {args.limit} items")

    if not items:
        print("Inbox is empty!")
        return

    # Analyze brain structure
    print("Analyzing brain structure...")
    analyzer = BrainAnalyzer(vault_path, llm_analyzer=llm_analyzer)
    generator = ProposalGenerator(analyzer)

    # Generate proposals
    print("Generating proposals...")
    proposals = []
    low_confidence_items = []  # Items with no strong relationships

    for item in items:
        relationships = analyzer.find_relationships(item)
        proposal = generator.generate_proposals(item, relationships)
        proposals.append(proposal)

        # Track items with weak/no relationships for cluster detection
        if not relationships or relationships[0].confidence < 0.6:
            low_confidence_items.append(item)

    # Detect topic clusters among unmatched items
    clusters = {}
    if low_confidence_items:
        print(f"Detecting topic clusters among {len(low_confidence_items)} unmatched items...")
        clusters = detect_topic_clusters(low_confidence_items, min_cluster_size=3)
        if clusters:
            print(f"✨ Found {len(clusters)} potential MOC topics!")
            for topic, cluster_items in list(clusters.items())[:3]:
                print(f"   - {topic}: {len(cluster_items)} items")

    # Generate proposals.md
    proposals_md = generate_proposals_markdown(proposals, clusters)

    # Write to file
    proposals_path = Path(vault_path) / "proposals.md"
    proposals_path.write_text(proposals_md, encoding='utf-8')

    print(f"\n✅ Proposals generated: {proposals_path}")
    print(f"\nNext steps:")
    print("1. Review proposals.md")
    print("2. Mark actions as [ACCEPT], [REJECT], or [EDIT]")
    if args.limit:
        print(f"3. Run: python3 apply.py --limit {args.limit} (to process same {args.limit} items)")
    else:
        print("3. Run: python3 apply.py to execute approved changes")


if __name__ == "__main__":
    main()
