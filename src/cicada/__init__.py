# src/cicada/__init__.py
from .core import *
from .retrieval import *

# Conditional import for codecad features
try:
    # agents (will be refactored/reorganized)
    from .feedback import *
    from .describe import *
    from .coding import *
    from .geometry_pipeline import *
    from .workflow import *
except ImportError:
    pass

__version__ = "0.7.4"
