"""Importerサービスパッケージ.

外部データソースからの問い合わせ自動取り込みを担当するサービス群。
"""
from services.importer.ai_provider_base import (AIAnalysisRequest,
                                                AIAnalysisResponse, AIProvider,
                                                AIProviderConfig,
                                                AIProviderType)
from services.importer.ai_provider_registry import (AIProviderError,
                                                    AIProviderRegistryService,
                                                    AIProviderStatus)
from services.importer.plugin_base import (DataSourcePlugin, RawImportData,
                                           ValidationError, ValidationResult)
from services.importer.plugin_registry import (PluginError,
                                               PluginRegistryService,
                                               PluginStatus)
from services.importer.result import BaseError, Result

__all__ = [
    # Common result type
    "BaseError",
    "Result",
    # Plugin base
    "DataSourcePlugin",
    "RawImportData",
    "ValidationError",
    "ValidationResult",
    # Plugin registry
    "PluginError",
    "PluginRegistryService",
    "PluginStatus",
    # AI provider base
    "AIProviderType",
    "AIProviderConfig",
    "AIAnalysisRequest",
    "AIAnalysisResponse",
    "AIProvider",
    # AI provider registry
    "AIProviderError",
    "AIProviderRegistryService",
    "AIProviderStatus",
]
