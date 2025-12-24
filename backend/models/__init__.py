"""
Models package initialization
Exports core models and types for easy importing
"""

# Enums
from .enums import (
    InquiryStatus,
    StoryStatus,
    StoryCategory,
    Priority,
    StoryPattern,
)

# Database Models
from .database import (
    Base,
    InquiryModel,
    StoryModel,
    StoryTemplateModel,
)

# Pydantic Schemas
from .schemas import (
    Inquiry,
    InquiryResult,
    Story,
    StoryMetadata,
    StoryTemplate,
    TemplateField,
)

# API Models
from .api import (
    InquiryCreateRequest,
    StoryUpdateRequest,
    RejectRequest,
    InquiryResponse,
    StoryResponse,
    StoryGenerationResponse,
    GenerationStatusResponse,
)

# Export Models
from .export import (
    AuthConfig,
    FieldMapping,
    KanbanSystem,
    ExportResult,
    SyncStatus,
    NotificationSettings,
)

# Service Protocols
from .protocols import (
    InquiryServiceProtocol,
    StoryConverterProtocol,
    PatternRecognizerProtocol,
    StoryServiceProtocol,
    ExportServiceProtocol,
    NotificationServiceProtocol,
)

__all__ = [
    # Enums
    "InquiryStatus",
    "StoryStatus", 
    "StoryCategory",
    "Priority",
    "StoryPattern",
    
    # Database Models
    "Base",
    "InquiryModel",
    "StoryModel",
    "StoryTemplateModel",
    
    # Pydantic Schemas
    "Inquiry",
    "InquiryResult",
    "Story",
    "StoryMetadata",
    "StoryTemplate",
    "TemplateField",
    
    # API Models
    "InquiryCreateRequest",
    "StoryUpdateRequest",
    "RejectRequest",
    "InquiryResponse",
    "StoryResponse",
    "StoryGenerationResponse",
    "GenerationStatusResponse",
    
    # Export Models
    "AuthConfig",
    "FieldMapping",
    "KanbanSystem",
    "ExportResult",
    "SyncStatus",
    "NotificationSettings",
    
    # Service Protocols
    "InquiryServiceProtocol",
    "StoryConverterProtocol",
    "PatternRecognizerProtocol",
    "StoryServiceProtocol",
    "ExportServiceProtocol",
    "NotificationServiceProtocol",
]