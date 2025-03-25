# src/cicada/__init__.py
from .core import *
from .retrieval import *

# Conditional import for codecad features
try:
    from .geometry_pipeline import *
    from .workflow import *
    from .describe import *
    from .coding import *
    from .feedback import *
except ImportError:
    pass

__version__ = "0.7.0"
