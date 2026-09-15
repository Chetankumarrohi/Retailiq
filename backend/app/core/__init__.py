"""
Core settings and security modules for RetailIQ backend.
"""
from backend.app.core.config import settings
from backend.app.core.security import SQLSecurityValidator

__all__ = ["settings", "SQLSecurityValidator"]
