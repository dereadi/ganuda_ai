"""
ganuda-pii recognizers plugin system
Cherokee AI Federation - CORE PACKAGE

Domain-specific recognizers are organized as plugins.
Each plugin module should export a get_recognizers() function.

Example:
    from ganuda_pii.recognizers import veteran
    service.add_recognizers(veteran.get_recognizers())

Available plugins:
    - veteran: VA-specific patterns (SSN variants, VA file numbers)
    - ssdi: Social Security disability patterns (future)
    - healthcare: HIPAA-related patterns (future)
"""

# Import available plugins for convenience
from . import veteran

__all__ = ["veteran"]
