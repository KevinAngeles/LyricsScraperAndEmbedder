from typing import Optional, List, Type, Dict, TypeVar
from .base_provider import LyricsProvider, TrackInfo
from .genius_provider import GeniusProvider
import importlib
import pkgutil
import inspect

T = TypeVar('T', bound=LyricsProvider)

class ProviderFactory:
    """Factory class for creating and managing lyrics providers."""
    
    _providers: Dict[str, Type[LyricsProvider]] = {}
    _initialized = False
    
    @classmethod
    def _initialize(cls):
        """Initialize the factory with all available providers."""
        if cls._initialized:
            return
            
        # Register built-in providers
        cls.register_provider(GeniusProvider)
        
        # TODO: Dynamically discover and register other providers from the providers package
        
        cls._initialized = True
    
    @classmethod
    def register_provider(cls, provider_class: Type[T]) -> None:
        """Register a new lyrics provider."""
        if not inspect.isclass(provider_class) or not issubclass(provider_class, LyricsProvider):
            raise ValueError("Provider must be a subclass of LyricsProvider")
            
        # Use the provider's name as the key (lowercase)
        provider_name = provider_class.__name__.lower().replace('provider', '')
        cls._providers[provider_name] = provider_class
    
    @classmethod
    def get_provider_for_url(cls, url: str) -> Optional[LyricsProvider]:
        """Get the appropriate provider for the given URL."""
        cls._initialize()
        
        for provider_class in cls._providers.values():
            if hasattr(provider_class, 'can_handle') and provider_class.can_handle(url):
                return provider_class()
        
        return None
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get a list of available provider names."""
        cls._initialize()
        return list(cls._providers.keys())
    
    @classmethod
    def get_provider(cls, name: str) -> Optional[Type[LyricsProvider]]:
        """Get a provider class by name."""
        cls._initialize()
        return cls._providers.get(name.lower())
