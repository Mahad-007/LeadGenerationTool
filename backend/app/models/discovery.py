"""Discovery models for API responses."""

from typing import Literal
from pydantic import BaseModel, Field


class SearchMetadata(BaseModel):
    """Metadata about a search that discovered URLs."""
    engine: Literal["google", "bing", "duckduckgo", "built_in_database"] = Field(
        description="Search engine used"
    )
    query: str = Field(description="Search query used")
    results_count: int = Field(ge=0, description="Number of results found")


class Discovery(BaseModel):
    """A discovered niche with its URLs."""
    niche: str = Field(description="Niche category name")
    discovered_at: str = Field(description="ISO timestamp of discovery")
    total_urls: int = Field(ge=0, description="Total URLs discovered for this niche")
    urls: list[str] = Field(default_factory=list, description="List of discovered URLs")
    search_metadata: list[SearchMetadata] = Field(
        default_factory=list, description="Search metadata for each source"
    )
    source: Literal["database", "search_engines"] = Field(
        description="Where the URLs were sourced from"
    )


class DiscoveryMetadata(BaseModel):
    """Metadata about the discovery process."""
    generated_at: str = Field(description="ISO timestamp of generation")
    total_niches: int = Field(ge=0, description="Total niches discovered")
    total_urls: int = Field(ge=0, description="Total URLs discovered across all niches")


class DiscoveryResponse(BaseModel):
    """Response from the discovery endpoint."""
    metadata: DiscoveryMetadata = Field(description="Discovery process metadata")
    discoveries: list[Discovery] = Field(
        default_factory=list, description="List of discoveries by niche"
    )
