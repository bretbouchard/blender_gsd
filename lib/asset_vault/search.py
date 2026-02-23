"""
Asset Vault Search Engine

Full-text, tag-based, and hybrid search for assets.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .enums import AssetCategory, AssetFormat, SearchMode
from .types import AssetIndex, AssetInfo, SearchResult


@dataclass
class SearchQuery:
    """Search query parameters."""
    text: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[AssetCategory] = None
    formats: Optional[List[AssetFormat]] = None
    min_score: float = 0.0
    max_results: int = 100
    mode: SearchMode = SearchMode.HYBRID

    @classmethod
    def from_string(cls, query_str: str) -> "SearchQuery":
        """
        Parse a search query string.

        Supports:
        - Simple text: "cyberpunk car"
        - Tags: "tag:sci-fi tag:vehicle"
        - Category: "category:furniture"
        - Format: "format:blend"

        Args:
            query_str: Query string

        Returns:
            SearchQuery instance
        """
        text_parts = []
        tags = []
        category = None
        formats = []

        for part in query_str.split():
            if part.startswith("tag:"):
                tags.append(part[4:])
            elif part.startswith("category:"):
                category = AssetCategory.from_string(part[9:])
            elif part.startswith("format:"):
                formats.append(AssetFormat.from_extension(part[7:]))
            else:
                text_parts.append(part)

        return cls(
            text=" ".join(text_parts) if text_parts else None,
            tags=tags if tags else None,
            category=category,
            formats=formats if formats else None,
        )


class SearchEngine:
    """
    Fast search engine for asset indices.

    Supports multiple search modes:
    - TEXT: Keyword search in names and paths
    - TAG: Filter by tags
    - VISUAL: Placeholder for image similarity
    - HYBRID: Combined approaches
    """

    def __init__(self, index: AssetIndex):
        """
        Initialize search engine with an index.

        Args:
            index: Asset index to search
        """
        self.index = index
        self._text_index: Dict[str, List[Tuple[str, float]]] = {}
        self._build_text_index()

    def _build_text_index(self) -> None:
        """Build inverted index for text search."""
        for rel_path, asset in self.index.assets.items():
            # Tokenize name and path
            tokens = self._tokenize(asset.name)
            tokens.extend(self._tokenize(str(asset.path)))

            # Add tokens to index
            for token in tokens:
                if token not in self._text_index:
                    self._text_index[token] = []

                # Score based on position (name > path)
                score = 1.0 if token in asset.name.lower() else 0.7
                self._text_index[token].append((rel_path, score))

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for indexing.

        Args:
            text: Text to tokenize

        Returns:
            List of lowercase tokens
        """
        # Simple tokenization: lowercase, split on non-alphanumeric
        import re
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        return tokens

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Search for assets matching the query.

        Args:
            query: Search query

        Returns:
            List of SearchResult, sorted by score descending
        """
        if query.mode == SearchMode.TEXT:
            results = self.text_search(query.text or "")
        elif query.mode == SearchMode.TAG:
            results = self.tag_search(query.tags or [])
        elif query.mode == SearchMode.HYBRID:
            results = self._hybrid_search(query)
        else:
            results = []

        # Apply filters
        if query.category:
            results = [r for r in results if r.asset.category == query.category]

        if query.formats:
            format_set = set(query.formats)
            results = [r for r in results if r.asset.format in format_set]

        # Filter by minimum score
        results = [r for r in results if r.score >= query.min_score]

        # Sort by score and limit
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:query.max_results]

    def text_search(self, text: str, fuzzy: bool = True) -> List[SearchResult]:
        """
        Full-text search.

        Args:
            text: Search text
            fuzzy: Enable fuzzy (substring) matching

        Returns:
            List of SearchResult
        """
        if not text:
            return []

        tokens = self._tokenize(text)
        if not tokens:
            return []

        # Aggregate scores per asset
        scores: Dict[str, float] = {}
        highlights: Dict[str, List[str]] = {}

        for token in tokens:
            # Exact match
            if token in self._text_index:
                for rel_path, score in self._text_index[token]:
                    if rel_path not in scores:
                        scores[rel_path] = 0.0
                        highlights[rel_path] = []
                    scores[rel_path] += score
                    highlights[rel_path].append(token)

            # Fuzzy match (prefix)
            elif fuzzy:
                for indexed_token in self._text_index:
                    if indexed_token.startswith(token):
                        for rel_path, score in self._text_index[indexed_token]:
                            if rel_path not in scores:
                                scores[rel_path] = 0.0
                                highlights[rel_path] = []
                            scores[rel_path] += score * 0.7  # Lower score for fuzzy
                            highlights[rel_path].append(indexed_token)

        # Build results
        results = []
        for rel_path, score in scores.items():
            if rel_path in self.index.assets:
                results.append(SearchResult(
                    asset=self.index.assets[rel_path],
                    score=min(1.0, score / len(tokens)),  # Normalize to 0-1
                    match_type="text",
                    highlights=highlights.get(rel_path, []),
                ))

        return results

    def tag_search(
        self,
        tags: List[str],
        match_all: bool = False,
    ) -> List[SearchResult]:
        """
        Search by tags.

        Args:
            tags: Tags to search for
            match_all: If True, all tags must match

        Returns:
            List of SearchResult
        """
        if not tags:
            return []

        tags_lower = [t.lower() for t in tags]

        # Find assets matching tags
        matching_assets: Dict[str, int] = {}  # rel_path -> match count

        for tag in tags_lower:
            if tag in self.index.tags:
                for rel_path in self.index.tags[tag]:
                    matching_assets[rel_path] = matching_assets.get(rel_path, 0) + 1

        # Filter by match_all requirement
        if match_all:
            matching_assets = {
                p: c for p, c in matching_assets.items()
                if c == len(tags)
            }

        # Build results
        results = []
        for rel_path, match_count in matching_assets.items():
            if rel_path in self.index.assets:
                score = match_count / len(tags)  # Score based on tag coverage
                results.append(SearchResult(
                    asset=self.index.assets[rel_path],
                    score=score,
                    match_type="tag",
                    highlights=tags_lower[:match_count],
                ))

        return results

    def category_search(self, category: AssetCategory) -> List[SearchResult]:
        """
        Search by category.

        Args:
            category: Category to search

        Returns:
            List of SearchResult
        """
        cat_name = category.value
        if cat_name not in self.index.categories:
            return []

        results = []
        for rel_path in self.index.categories[cat_name]:
            if rel_path in self.index.assets:
                results.append(SearchResult(
                    asset=self.index.assets[rel_path],
                    score=1.0,
                    match_type="category",
                ))

        return results

    def filter_by_format(
        self,
        results: List[SearchResult],
        formats: List[AssetFormat],
    ) -> List[SearchResult]:
        """
        Filter results by asset format.

        Args:
            results: Results to filter
            formats: Allowed formats

        Returns:
            Filtered results
        """
        format_set = set(formats)
        return [r for r in results if r.asset.format in format_set]

    def _hybrid_search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Combine text and tag search.

        Args:
            query: Search query

        Returns:
            Combined and scored results
        """
        all_results: Dict[str, SearchResult] = {}

        # Text search
        if query.text:
            text_results = self.text_search(query.text)
            for r in text_results:
                all_results[str(r.asset.path)] = SearchResult(
                    asset=r.asset,
                    score=r.score * 0.6,  # Weight for text
                    match_type="hybrid",
                    highlights=r.highlights,
                )

        # Tag search
        if query.tags:
            tag_results = self.tag_search(query.tags)
            for r in tag_results:
                path = str(r.asset.path)
                if path in all_results:
                    # Combine scores
                    all_results[path].score += r.score * 0.4
                    all_results[path].highlights.extend(r.highlights)
                else:
                    all_results[path] = SearchResult(
                        asset=r.asset,
                        score=r.score * 0.4,  # Weight for tags
                        match_type="hybrid",
                        highlights=r.highlights,
                    )

        # Category filter
        if query.category:
            cat_results = self.category_search(query.category)
            for r in cat_results:
                path = str(r.asset.path)
                if path in all_results:
                    all_results[path].score = min(1.0, all_results[path].score + 0.3)
                else:
                    all_results[path] = r

        return list(all_results.values())


def quick_search(
    index: AssetIndex,
    query: str,
    max_results: int = 20,
) -> List[SearchResult]:
    """
    Convenience function for simple searches.

    Args:
        index: Asset index to search
        query: Search query string
        max_results: Maximum results to return

    Returns:
        List of SearchResult
    """
    engine = SearchEngine(index)
    search_query = SearchQuery(
        text=query,
        max_results=max_results,
        mode=SearchMode.HYBRID,
    )
    return engine.search(search_query)
