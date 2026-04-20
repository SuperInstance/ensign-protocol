"""ensign-protocol — Wire format for PLATO ensigns.

Ensigns are compressed behavioral instincts extracted from room tiles.
This crate defines the load/save/validate cycle for ensign transport.
"""

__version__ = "0.1.0"

from .ensign import Ensign, EnsignHeader, EnsignField, ValidationError

__all__ = ["Ensign", "EnsignHeader", "EnsignField", "ValidationError"]
