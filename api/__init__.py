"""
Backend API for video segmentation and editing
"""

from .main import app
from .models import *
from .routes import *

__all__ = ['app']

