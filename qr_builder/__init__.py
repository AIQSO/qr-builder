from .auth import (
    TIER_LIMITS,
    TierLimits,
    UserSession,
    UserTier,
    get_all_tiers_info,
    get_tier_info,
)
from .config import (
    AppConfig,
    SecurityConfig,
    ServerConfig,
    get_config,
)
from .core import (
    ARTISTIC_PRESETS,
    # Constants
    MAX_DATA_LENGTH,
    MAX_QR_SIZE,
    MIN_QR_SIZE,
    VALID_POSITIONS,
    QRConfig,
    QRStyle,
    calculate_position,
    embed_qr_in_image,
    generate_artistic_qr,
    generate_qart,
    # Basic functions
    generate_qr,
    generate_qr_only,
    # Unified interface
    generate_qr_unified,
    # Advanced styles
    generate_qr_with_logo,
    generate_qr_with_text,
    parse_color,
    validate_data,
    validate_size,
)

__version__ = "0.3.0"

__all__ = [
    # Basic functions
    "generate_qr",
    "generate_qr_only",
    "embed_qr_in_image",
    "calculate_position",
    "validate_data",
    "validate_size",
    "parse_color",
    # Advanced styles
    "generate_qr_with_logo",
    "generate_qr_with_text",
    "generate_artistic_qr",
    "generate_qart",
    # Unified interface
    "generate_qr_unified",
    "QRConfig",
    "QRStyle",
    "ARTISTIC_PRESETS",
    # Auth & Tiers
    "UserTier",
    "TierLimits",
    "UserSession",
    "TIER_LIMITS",
    "get_all_tiers_info",
    "get_tier_info",
    # Configuration
    "get_config",
    "AppConfig",
    "ServerConfig",
    "SecurityConfig",
    # Constants
    "MAX_DATA_LENGTH",
    "MAX_QR_SIZE",
    "MIN_QR_SIZE",
    "VALID_POSITIONS",
    "__version__",
]
