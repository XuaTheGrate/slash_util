from .bot import *
from .core import *
from .context import *
from .cog import *

from ._patch import inject
inject()
del inject