"""
AI Assist Base Class - Provides AI checkbox and suggestion display for all widgets

All widgets should inherit from AIAssistMixin to get AI functionality
"""

from PyQt6.QtWidgets import QCheckBox, QLabel, QFrame, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Optional, Dict, Any
import logging

from core.ml_integration import get_ml_prediction, is_ml_available, create_ai_suggestion

logger = logging.getLogger(__name__)


class AIAssistMixin:
    """
    Mixin class that adds AI assistance capabilities to any widget

    Usage:
        class MyWidget(QWidget, AIAssistMixin):
            def __init__(self):
                super().__init__()
                self.setup_ai_assist("my_widget_type")

            def my_update_method(self, data):
                # ... normal widget logic ...

                # Add AI analysis if enabled
                if self.ai_enabled:
                    ai_suggestion = self.get_ai_suggestion(data)
                    self.display_ai_suggestion(ai_suggestion)
    """

    # Signal emitted when AI assist is toggled
    ai_toggled = pyqtSignal(bool)

    def setup_ai_assist(self, widget_type: str, checkbox_label: str = "🤖 AI Assist"):
        """
        Initialize AI assist functionality for this widget

        Args:
            widget_type: Unique identifier for this widget type
            checkbox_label: Label for the AI checkbox
        """
        self.widget_type = widget_type
        self.ai_enabled = False
        self.ai_checkbox_label = checkbox_label
        self.ai_suggestion_frame = None
        self.ai_suggestion_label = None

        logger.info(f"AI Assist initialized for widget: {widget_type}")

    def create_ai_checkbox(self, parent_layout: QHBoxLayout = None) -> QCheckBox:
        """
        Create the AI Assist checkbox

        Args:
            parent_layout: Optional layout to add checkbox to

        Returns:
            The created checkbox widget
        """
        checkbox = QCheckBox(self.ai_checkbox_label)
        checkbox.setChecked(self.ai_enabled)
        checkbox.stateChanged.connect(self._on_ai_checkbox_toggled)

        # Style the checkbox
        checkbox.setStyleSheet("""
            QCheckBox {
                color: #3B82F6;
                font-weight: bold;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:checked {
                background-color: #3B82F6;
                border: 2px solid #1E40AF;
                border-radius: 3px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #1E293B;
                border: 2px solid #475569;
                border-radius: 3px;
            }
        """)

        if parent_layout:
            parent_layout.addWidget(checkbox)

        self.ai_checkbox = checkbox
        return checkbox

    def _on_ai_checkbox_toggled(self, state):
        """Handle AI checkbox state change"""
        self.ai_enabled = (state == Qt.CheckState.Checked.value)
        logger.info(f"AI Assist {'enabled' if self.ai_enabled else 'disabled'} for {self.widget_type}")

        # Emit signal
        if hasattr(self, 'ai_toggled'):
            self.ai_toggled.emit(self.ai_enabled)

        # Show/hide AI suggestion frame
        if self.ai_suggestion_frame:
            self.ai_suggestion_frame.setVisible(self.ai_enabled)

        # Trigger update if widget has update method
        if hasattr(self, 'update_ai_suggestions'):
            self.update_ai_suggestions()

    def create_ai_suggestion_frame(self, parent_layout: QVBoxLayout = None) -> QFrame:
        """
        Create the frame where AI suggestions will be displayed

        Args:
            parent_layout: Optional layout to add frame to

        Returns:
            The created frame widget
        """
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setVisible(False)  # Hidden by default

        # Frame layout
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)

        # Suggestion label
        self.ai_suggestion_label = QLabel("🤖 AI analyzing...")
        self.ai_suggestion_label.setWordWrap(True)

        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.ai_suggestion_label.setFont(font)

        frame_layout.addWidget(self.ai_suggestion_label)

        # Style the frame
        frame.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border: 2px solid #3B82F6;
                border-radius: 8px;
                padding: 5px;
            }
        """)

        if parent_layout:
            parent_layout.addWidget(frame)

        self.ai_suggestion_frame = frame
        return frame

    def get_ai_suggestion(self, widget_data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Get AI suggestion from ML system

        Args:
            widget_data: Widget-specific data to analyze

        Returns:
            AI suggestion dictionary or None
        """
        if not self.ai_enabled:
            return None

        try:
            # Get ML prediction for this widget type
            prediction = get_ml_prediction(self.widget_type)

            if prediction is None:
                return None

            # Let subclass implement widget-specific analysis
            if hasattr(self, 'analyze_with_ai'):
                return self.analyze_with_ai(prediction, widget_data)

            # Default suggestion format
            return create_ai_suggestion(
                widget_type=self.widget_type,
                text=f"ML prediction: {prediction.get('signal', 'UNKNOWN')}",
                confidence=prediction.get('confidence', 0.5),
                data=prediction
            )

        except Exception as e:
            logger.error(f"Error getting AI suggestion for {self.widget_type}: {e}")
            return None

    def display_ai_suggestion(self, suggestion: Optional[Dict[str, Any]]):
        """
        Display AI suggestion in the widget

        Args:
            suggestion: Suggestion dictionary from get_ai_suggestion()
        """
        if not self.ai_suggestion_frame or not self.ai_suggestion_label:
            return

        if not self.ai_enabled or suggestion is None:
            self.ai_suggestion_frame.setVisible(False)
            return

        # Extract suggestion components
        text = suggestion.get('text', 'No suggestion available')
        emoji = suggestion.get('emoji', '🤖')
        confidence_pct = suggestion.get('confidence_pct', '?%')
        color = suggestion.get('color', 'white')

        # Format display text
        display_text = f"{emoji} AI: {text} ({confidence_pct} confidence)"

        # Update label
        self.ai_suggestion_label.setText(display_text)

        # Update frame color based on confidence
        border_color = self._get_color_code(color)
        self.ai_suggestion_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #1E293B;
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 5px;
            }}
        """)

        # Update label color
        self.ai_suggestion_label.setStyleSheet(f"""
            QLabel {{
                color: {border_color};
            }}
        """)

        # Show the frame
        self.ai_suggestion_frame.setVisible(True)

    def _get_color_code(self, color_name: str) -> str:
        """Convert color name to hex code"""
        color_map = {
            'green': '#10B981',
            'yellow': '#F59E0B',
            'red': '#EF4444',
            'blue': '#3B82F6',
            'white': '#F8FAFC',
        }
        return color_map.get(color_name.lower(), '#3B82F6')

    def check_ml_availability(self) -> bool:
        """
        Check if ML system is available

        Returns:
            True if ML service is running, False otherwise
        """
        return is_ml_available()

    def update_ai_suggestions(self):
        """
        Trigger update of AI suggestions

        Subclasses should override this to implement widget-specific updates
        """
        if self.ai_enabled:
            suggestion = self.get_ai_suggestion()
            self.display_ai_suggestion(suggestion)


class AIAssistWidget:
    """
    Example implementation showing how to use AIAssistMixin

    class MyWidget(QWidget, AIAssistMixin):
        def __init__(self):
            super().__init__()
            self.setup_ai_assist("my_widget")

            layout = QVBoxLayout(self)

            # Add AI checkbox at top
            header = QHBoxLayout()
            header.addWidget(QLabel("My Widget"))
            header.addStretch()
            self.create_ai_checkbox(header)
            layout.addLayout(header)

            # ... widget content ...

            # Add AI suggestion frame at bottom
            self.create_ai_suggestion_frame(layout)

        def analyze_with_ai(self, prediction, widget_data):
            # Custom AI analysis for this widget
            return create_ai_suggestion(
                widget_type=self.widget_type,
                text="Custom suggestion here",
                confidence=prediction.get('confidence', 0.5)
            )

        def update_data(self, data):
            # Normal widget update
            # ...

            # Update AI if enabled
            if self.ai_enabled:
                suggestion = self.get_ai_suggestion(data)
                self.display_ai_suggestion(suggestion)
    """
    pass
