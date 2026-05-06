#!/usr/bin/env python3
"""
Demo: Topic cluster detection for MOC suggestions

Shows how the analyzer detects topic clusters and suggests MOCs
"""
import sys
sys.path.insert(0, '/Users/davidproctor/Documents/GitHub/entropy/.agent/skills/process-inbox')

from analyzer import InboxItem, extract_topic_from_item, detect_topic_clusters

# Simulate inbox items on different topics
test_items = [
    InboxItem(
        filename="RAG Architecture Patterns.md",
        path="/test/RAG Architecture Patterns.md",
        content="# RAG Architecture Patterns\n\nRetrievalaugmented generation...",
        frontmatter={},
        word_count=500
    ),
    InboxItem(
        filename="Vector Database Comparison.md",
        path="/test/Vector Database Comparison.md",
        content="# Vector Database Comparison\n\nComparing Pinecone, Weaviate, and Qdrant...",
        frontmatter={},
        word_count=600
    ),
    InboxItem(
        filename="RAG vs Fine-tuning.md",
        path="/test/RAG vs Fine-tuning.md",
        content="# RAG vs Fine-tuning\n\nWhen to use retrieval vs training...",
        frontmatter={},
        word_count=450
    ),
    InboxItem(
        filename="Embedding Models for RAG.md",
        path="/test/Embedding Models for RAG.md",
        content="# Embedding Models for RAG\n\nComparing OpenAI, Cohere, and open-source...",
        frontmatter={},
        word_count=550
    ),
    InboxItem(
        filename="Agent Communication Protocols.md",
        path="/test/Agent Communication Protocols.md",
        content="# Agent Communication Protocols\n\nHTTP vs WebSocket vs gRPC...",
        frontmatter={},
        word_count=400
    ),
    InboxItem(
        filename="Multi-Agent Orchestration.md",
        path="/test/Multi-Agent Orchestration.md",
        content="# Multi-Agent Orchestration\n\nCoordinating multiple AI agents...",
        frontmatter={},
        word_count=500
    ),
    InboxItem(
        filename="Agent Identity and Trust.md",
        path="/test/Agent Identity and Trust.md",
        content="# Agent Identity and Trust\n\nCryptographic identity for AI agents...",
        frontmatter={},
        word_count=480
    ),
]

print("=" * 60)
print("TOPIC CLUSTER DETECTION DEMO")
print("=" * 60)

print(f"\nTest inbox: {len(test_items)} items")
print("\nItems:")
for item in test_items:
    print(f"  - {item.filename}")

print("\n" + "=" * 60)
print("EXTRACTING TOPICS")
print("=" * 60)

for item in test_items:
    topics = extract_topic_from_item(item)
    print(f"\n{item.filename}")
    print(f"  Topics: {', '.join(topics[:3])}")

print("\n" + "=" * 60)
print("DETECTING CLUSTERS (min 3 items)")
print("=" * 60)

clusters = detect_topic_clusters(test_items, min_cluster_size=3)

if clusters:
    print(f"\n✨ Found {len(clusters)} potential MOCs!\n")
    for topic, cluster_items in clusters.items():
        print(f"📁 MOC Suggestion: {topic.title()}")
        print(f"   Items: {len(cluster_items)}")
        for item in cluster_items:
            print(f"   - {item.filename}")
        print()
else:
    print("\nNo clusters found (need 3+ items on same topic)")

print("=" * 60)
print("WHAT WOULD APPEAR IN PROPOSALS.MD")
print("=" * 60)

if clusters:
    print("""
## 🎯 Suggested New MOCs

**Topic clusters detected** - Consider creating MOCs for these topics:
""")
    for topic, cluster_items in list(clusters.items())[:2]:  # Show first 2
        moc_name = topic.replace('-', ' ').title()
        print(f"\n### MOC Suggestion: {moc_name}")
        print(f"**Items in cluster:** {len(cluster_items)}")
        print(f"**Detected topic:** {topic}\n")
        print("**Items:**")
        for item in cluster_items:
            print(f"- {item.filename}")

        print(f"\n### ACTION: CREATE MOC")
        print(f"**Target:** `mocs/{moc_name.replace(' ', '-')}-MOC.md`")
        print(f"**Rationale:** {len(cluster_items)} items about '{topic}' suggest new navigation hub")
        print("\n[ACCEPT] [REJECT]\n")
        print("---")

print("\n✅ Demo complete!")
print("\nIn production:")
print("1. Analyzer detects clusters automatically")
print("2. Suggests MOC creation at top of proposals.md")
print("3. User marks [ACCEPT] or [REJECT]")
print("4. Apply creates MOC with all cluster items linked")
