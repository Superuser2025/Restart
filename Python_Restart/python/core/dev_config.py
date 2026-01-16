"""
Development Configuration
Controls whether license checks are enforced

IMPORTANT: Set DEVELOPMENT_MODE = False before building for customers!
"""

# =============================================================================
# DEVELOPMENT MODE SWITCH
# =============================================================================

# Set to True during development (no license required)
# Set to False when building for production (license required)
DEVELOPMENT_MODE = True

# Optional: Use environment variable for extra safety
# export TRADING_APP_DEV_MODE=1    # Development
# unset TRADING_APP_DEV_MODE       # Production
import os
if os.getenv('TRADING_APP_DEV_MODE'):
    DEVELOPMENT_MODE = True


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def is_dev_mode() -> bool:
    """Check if running in development mode"""
    return DEVELOPMENT_MODE


def get_mode_label() -> str:
    """Get current mode label for UI"""
    return "🔧 DEVELOPMENT MODE" if DEVELOPMENT_MODE else "🔐 PRODUCTION MODE"


def should_enforce_license() -> bool:
    """Check if license should be enforced"""
    return not DEVELOPMENT_MODE


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
In your code, check dev mode before enforcing license:

from core.dev_config import is_dev_mode

if not is_dev_mode():
    # Only enforce license in production
    if not check_license_on_startup():
        sys.exit(0)
else:
    print("🔧 Development mode - skipping license check")
"""
