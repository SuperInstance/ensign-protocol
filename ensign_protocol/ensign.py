"""Ensign wire format: header + fields + checksum."""

import json
import hashlib
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


class ValidationError(Exception):
    """Raised when ensign validation fails."""
    pass


@dataclass
class EnsignHeader:
    """Ensign metadata header."""
    name: str
    version: str = "0.1.0"
    source_room: str = ""
    created_at: float = field(default_factory=time.time)
    tile_count: int = 0
    compression: str = "none"  # none, gzip, zstd

    def validate(self) -> List[str]:
        errors = []
        if not self.name or len(self.name) < 2:
            errors.append("name must be >= 2 chars")
        if not self.version:
            errors.append("version required")
        if self.tile_count < 0:
            errors.append("tile_count must be >= 0")
        if self.compression not in ("none", "gzip", "zstd"):
            errors.append(f"unknown compression: {self.compression}")
        return errors


@dataclass
class EnsignField:
    """A single instinct/pattern field in an ensign."""
    key: str
    value: Any
    weight: float = 1.0
    category: str = "general"

    def validate(self) -> List[str]:
        errors = []
        if not self.key:
            errors.append("field key required")
        if not 0.0 <= self.weight <= 2.0:
            errors.append(f"weight {self.weight} out of range [0.0, 2.0]")
        return errors


@dataclass
class Ensign:
    """A complete ensign: header + fields + checksum.
    
    Usage:
        ensign = Ensign(header=EnsignHeader(name="navigator"), fields=[
            EnsignField(key="avoid_shallow", value=True, weight=0.9),
        ])
        data = ensign.save()
        loaded = Ensign.load(data)
        loaded.validate()  # raises ValidationError if corrupt
    """
    header: EnsignHeader
    fields: List[EnsignField] = field(default_factory=list)
    _checksum: str = ""

    def checksum(self) -> str:
        """Compute SHA-256 checksum of header + fields."""
        content = json.dumps({
            "header": asdict(self.header),
            "fields": [asdict(f) for f in self.fields],
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def save(self) -> str:
        """Serialize to JSON string with checksum."""
        self._checksum = self.checksum()
        return json.dumps({
            "header": asdict(self.header),
            "fields": [asdict(f) for f in self.fields],
            "_checksum": self._checksum,
        }, indent=2)

    @classmethod
    def load(cls, data: str) -> "Ensign":
        """Deserialize from JSON string."""
        raw = json.loads(data)
        header = EnsignHeader(**raw["header"])
        fields = [EnsignField(**f) for f in raw.get("fields", [])]
        ensign = cls(header=header, fields=fields)
        ensign._checksum = raw.get("_checksum", "")
        return ensign

    def validate(self) -> None:
        """Full validation. Raises ValidationError with all issues."""
        errors = []
        errors.extend(self.header.validate())
        for i, f in enumerate(self.fields):
            for e in f.validate():
                errors.append(f"field[{i}] {f.key}: {e}")
        
        # Checksum integrity
        expected = self.checksum()
        if self._checksum and self._checksum != expected:
            errors.append(f"checksum mismatch: expected {expected}, got {self._checksum}")
        
        if errors:
            raise ValidationError("; ".join(errors))

    def add_field(self, key: str, value: Any, weight: float = 1.0, category: str = "general") -> "Ensign":
        """Builder pattern: add a field and return self."""
        self.fields.append(EnsignField(key=key, value=value, weight=weight, category=category))
        return self

    def fields_by_category(self, category: str) -> List[EnsignField]:
        """Filter fields by category."""
        return [f for f in self.fields if f.category == category]

    def total_weight(self) -> float:
        """Sum of all field weights."""
        return sum(f.weight for f in self.fields)
