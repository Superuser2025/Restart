"""
Verbose Mode Manager
Controls console output verbosity globally
"""

from PyQt6.QtCore import QObject, pyqtSignal


class VerboseModeManager(QObject):
    """
    Singleton manager for controlling console output verbosity
    """

    # Signal emitted when verbose mode changes
    mode_changed = pyqtSignal(bool)  # True = verbose, False = quiet

    def __init__(self):
        super().__init__()
        self._verbose = True  # Start with verbose mode ON by default

    @property
    def verbose(self):
        """Get current verbose state"""
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool):
        """Set verbose state and emit signal"""
        if self._verbose != value:
            self._verbose = value
            self.mode_changed.emit(value)
            status = "ENABLED" if value else "DISABLED"
            print(f"[Verbose Mode] Console output {status}")


# Global singleton instance
verbose_mode_manager = VerboseModeManager()


def is_verbose():
    """Check if verbose mode is enabled"""
    return verbose_mode_manager.verbose


def vprint(*args, **kwargs):
    """
    Verbose print - only prints if verbose mode is enabled

    Usage:
        from core.verbose_mode_manager import vprint
        vprint("[DEBUG] This will only show if verbose mode is ON")
    """
    if verbose_mode_manager.verbose:
        print(*args, **kwargs)


def set_verbose(enabled: bool):
    """Enable or disable verbose mode"""
    verbose_mode_manager.verbose = enabled
