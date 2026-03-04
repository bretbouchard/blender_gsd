"""
Knowledge Base Package

Provides tools for querying and using the accumulated Blender knowledge.

Usage:
    from lib.knowledge import KnowledgeQuery, search_knowledge, get_pattern

    # Search the knowledge base
    results = search_knowledge("curl noise particles")

    # Get a specific pattern
    pattern = get_pattern("sdf_workflow")
"""

from .query import (
    KnowledgeQuery,
    KnowledgeResult,
    Pattern,
    search_knowledge,
    get_pattern,
    list_all_patterns,
    print_quick_reference,
)

__all__ = [
    "KnowledgeQuery",
    "KnowledgeResult",
    "Pattern",
    "search_knowledge",
    "get_pattern",
    "list_all_patterns",
    "print_quick_reference",
]
