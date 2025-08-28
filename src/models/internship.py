"""Data models for the internship finder application."""
from datetime import datetime
from typing import Optional, Dict, Any

from ..utils.helpers import clean_text


class Internship:
    """Data model for an internship posting."""

    def __init__(
        self,
        title: str,
        company: str,
        location: str,
        url: str,
        source: str,
        posted_date: Optional[datetime] = None,
        description: Optional[str] = None,
        **kwargs
    ):
        self.title = clean_text(title)
        self.company = clean_text(company)
        self.location = clean_text(location)
        self.url = url.strip()
        self.source = source
        self.posted_date = posted_date or datetime.utcnow()
        self.description = clean_text(description or '')
        self.metadata = kwargs  # Store any additional fields

    def to_dict(self) -> Dict[str, Any]:
        """Convert the internship to a dictionary for storage."""
        return {
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'url': self.url,
            'source': self.source,
            'posted_date': self.posted_date,
            'description': self.description,
            **self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Internship':
        """Create an Internship instance from a dictionary."""
        return cls(
            title=data.get('title', ''),
            company=data.get('company', ''),
            location=data.get('location', ''),
            url=data.get('url', ''),
            source=data.get('source', ''),
            posted_date=data.get('posted_date'),
            description=data.get('description', ''),
            **{k: v for k, v in data.items() 
               if k not in ['title', 'company', 'location', 'url', 'source', 'posted_date', 'description']}
        )

    def __str__(self) -> str:
        return f"{self.title} at {self.company} ({self.location})"

    def __repr__(self) -> str:
        return f"<Internship: {self.title} at {self.company}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Internship):
            return False
        return self.url == other.url

    def __hash__(self) -> int:
        return hash(self.url)
