"""
Internationalization (i18n) support for MAL Bombing Detector.

This module provides localization functionality supporting:
- JSON-based translation files
- String interpolation with named parameters
- Fallback to English for missing translations
- Nested key access (e.g., "cli.welcome")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .config import get_config, ROOT_DIR


LOCALES_DIR = ROOT_DIR / "locales"


class I18n:
    """
    Internationalization manager.
    
    Provides translation functionality with support for:
    - Multiple languages
    - Nested keys
    - Parameter interpolation
    - Fallback to English
    
    Example:
        >>> i18n = I18n("en")
        >>> i18n.t("cli.welcome", version="1.0.0")
        'MAL Bombing Detector v1.0.0'
    """
    
    def __init__(self, language: str = "en"):
        """
        Initialize i18n manager.
        
        Args:
            language: Language code (e.g., "en", "ru").
        """
        self.language = language
        self._translations: Dict[str, Any] = {}
        self._fallback: Dict[str, Any] = {}
        self._load_translations()
    
    def _load_translations(self) -> None:
        """Load translation files."""
        # Load requested language
        lang_file = LOCALES_DIR / f"{self.language}.json"
        if lang_file.exists():
            self._translations = self._load_json(lang_file)
        
        # Load English as fallback
        if self.language != "en":
            en_file = LOCALES_DIR / "en.json"
            if en_file.exists():
                self._fallback = self._load_json(en_file)
    
    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        """Load JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _get_nested(self, data: Dict[str, Any], key: str) -> Optional[str]:
        """
        Get nested value from dictionary using dot notation.
        
        Args:
            data: Dictionary to search.
            key: Dot-separated key (e.g., "cli.welcome").
        
        Returns:
            Value if found, None otherwise.
        """
        parts = key.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current if isinstance(current, str) else None
    
    def t(self, key: str, **kwargs: Any) -> str:
        """
        Translate a key with optional parameter interpolation.
        
        Args:
            key: Translation key (dot notation supported).
            **kwargs: Parameters for string interpolation.
        
        Returns:
            Translated string, or key if not found.
        
        Example:
            >>> i18n.t("cli.analyzing", count=50)
            'Analyzing 50 anime...'
        """
        # Try requested language
        value = self._get_nested(self._translations, key)
        
        # Fall back to English
        if value is None:
            value = self._get_nested(self._fallback, key)
        
        # Return key if not found
        if value is None:
            return key
        
        # Interpolate parameters
        try:
            return value.format(**kwargs)
        except KeyError:
            return value
    
    def get_dict(self, key: str) -> Dict[str, Any]:
        """
        Get a nested dictionary from translations.
        
        Args:
            key: Dot-separated key to dictionary.
        
        Returns:
            Dictionary if found, empty dict otherwise.
        """
        parts = key.split(".")
        current = self._translations
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                # Try fallback
                current = self._fallback
                for p in parts:
                    if isinstance(current, dict) and p in current:
                        current = current[p]
                    else:
                        return {}
                break
        
        return current if isinstance(current, dict) else {}
    
    def set_language(self, language: str) -> None:
        """
        Change the current language.
        
        Args:
            language: New language code.
        """
        self.language = language
        self._load_translations()
    
    @property
    def available_languages(self) -> list[str]:
        """Get list of available languages."""
        languages = []
        for file in LOCALES_DIR.glob("*.json"):
            languages.append(file.stem)
        return sorted(languages)


# Global i18n instance
_i18n: Optional[I18n] = None


def get_i18n() -> I18n:
    """
    Get the global i18n instance.
    
    Returns:
        I18n: The global i18n manager.
    """
    global _i18n
    if _i18n is None:
        config = get_config()
        _i18n = I18n(config.language)
    return _i18n


def t(key: str, **kwargs: Any) -> str:
    """
    Shorthand for translation.
    
    Args:
        key: Translation key.
        **kwargs: Interpolation parameters.
    
    Returns:
        Translated string.
    
    Example:
        >>> from src.utils.i18n import t
        >>> t("cli.complete")
        'Analysis complete!'
    """
    return get_i18n().t(key, **kwargs)


def set_language(language: str) -> None:
    """
    Set the global language.
    
    Args:
        language: Language code.
    """
    get_i18n().set_language(language)


# Alias for backward compatibility
I18nManager = I18n
