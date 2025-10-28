"""
Modern Dark Theme with Animations for Focus Guardian.

Provides a sleek, modern dark mode color scheme with smooth animations
and transitions for better user experience.
"""

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Qt, QPoint, QRect
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from typing import Dict


class ModernDarkTheme:
    """Modern dark theme with animations and transitions."""
    
    @staticmethod
    def get_colors(dark_mode: bool = True) -> Dict[str, str]:
        """
        Get color palette for the theme.
        
        Args:
            dark_mode: If True, return dark mode colors; otherwise light mode
        
        Returns:
            Dictionary of color values
        """
        if dark_mode:
            return {
                # Backgrounds (Dark Mode)
                'bg_primary': '#0D1117',        # GitHub dark background
                'bg_secondary': '#161B22',     # Elevated surfaces
                'bg_tertiary': '#21262D',       # Grouped lists
                'card_bg': '#161B22',           # Cards
                'grouped_bg': '#0D1117',        # Grouped backgrounds
                
                # Accent Colors (Modern Vibrant)
                'accent_blue': '#58A6FF',       # Primary actions (GitHub blue)
                'accent_green': '#3FB950',     # Success
                'accent_orange': '#F85149',     # Warnings/destructive
                'accent_red': '#F85149',        # Errors
                'accent_purple': '#A371F7',     # Premium features
                'accent_indigo': '#6F42C1',     # Alternative
                'accent_teal': '#39C5CF',       # Info
                'accent_pink': '#DB61A2',       # Special highlights
                'accent_yellow': '#D29922',     # Attention
                
                # Text (Dark Mode)
                'text_primary': '#E6EDF3',      # Primary text (GitHub white)
                'text_secondary': '#8B949E',   # Secondary text
                'text_tertiary': '#6E7681',     # Tertiary/disabled
                
                # Borders & Separators
                'border': '#30363D',           # Standard borders
                'separator': '#21262D',         # Separator lines
                
                # Interaction States
                'hover_bg': 'rgba(56, 139, 253, 0.12)',   # Hover with GitHub blue
                'selection_bg': 'rgba(56, 139, 253, 0.15)', # Selection
                'shadow': '0 8px 24px rgba(0, 0, 0, 0.4)', # Card shadow (darker)
                
                # Semantic Backgrounds
                'warning_bg': '#3D2E00',
                'warning_text': '#F1C40F',
                'success_bg': '#0B4419',
                'success_text': '#3FB950',
                'error_bg': '#490202',
                'error_text': '#F85149',
            }
        else:
            return {
                # Backgrounds (Light Mode)
                'bg_primary': '#F5F5F7',
                'bg_secondary': '#FFFFFF',
                'bg_tertiary': '#FAFAFA',
                'card_bg': '#FFFFFF',
                'grouped_bg': '#F2F2F7',
                
                # Accent Colors (Apple System Colors)
                'accent_blue': '#007AFF',
                'accent_green': '#34C759',
                'accent_orange': '#FF9500',
                'accent_red': '#FF3B30',
                'accent_purple': '#AF52DE',
                'accent_indigo': '#5856D6',
                'accent_teal': '#5AC8FA',
                'accent_pink': '#FF2D55',
                'accent_yellow': '#FFCC00',
                
                # Text (Light Mode)
                'text_primary': '#1C1C1E',
                'text_secondary': '#8E8E93',
                'text_tertiary': '#AEAEB2',
                
                # Borders & Separators
                'border': '#D1D1D6',
                'separator': '#C6C6C8',
                
                # Interaction States
                'hover_bg': 'rgba(0, 122, 255, 0.08)',
                'selection_bg': 'rgba(0, 122, 255, 0.15)',
                'shadow': '0 2px 8px rgba(0, 0, 0, 0.08)',
                
                # Semantic Backgrounds
                'warning_bg': '#FFF9E6',
                'warning_text': '#8B6914',
                'success_bg': '#E8F5E9',
                'success_text': '#1E7B34',
                'error_bg': '#FFEAEA',
                'error_text': '#C41E3A',
            }


class FadeAnimation:
    """Fade in/out animation effect."""
    
    @staticmethod
    def apply_fade_in(widget, duration_ms=300):
        """
        Apply fade-in animation to a widget.
        
        Args:
            widget: QWidget to animate
            duration_ms: Animation duration in milliseconds
        """
        opacity_effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(opacity_effect)
        
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(duration_ms)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        
        return animation


class SlideAnimation:
    """Slide animation effect for smooth transitions."""
    
    @staticmethod
    def apply_slide(widget, from_pos, to_pos, duration_ms=400):
        """
        Apply slide animation to a widget.
        
        Args:
            widget: QWidget to animate
            from_pos: Starting position
            to_pos: Ending position
            duration_ms: Animation duration in milliseconds
        """
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration_ms)
        animation.setStartValue(QRect(from_pos.x(), from_pos.y(), widget.width(), widget.height()))
        animation.setEndValue(QRect(to_pos.x(), to_pos.y(), widget.width(), widget.height()))
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        animation.start()
        
        return animation


class PulseAnimation:
    """Pulsing animation effect for attention."""
    
    @staticmethod
    def apply_pulse(widget, duration_ms=1000):
        """
        Apply pulsing animation to a widget.
        
        Args:
            widget: QWidget to animate
            duration_ms: Animation duration in milliseconds
        """
        opacity_effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(opacity_effect)
        
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(duration_ms)
        animation.setStartValue(0.3)
        animation.setEndValue(1.0)
        animation.setLoopCount(3)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
        
        return animation

