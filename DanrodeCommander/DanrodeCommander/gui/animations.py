"""
gui/animations.py
Small, purposeful animation helpers: fade in/out and a subtle scale-in.
No decorative or "fancy" effects — kept intentionally minimal.
"""

from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QObject,
    QPropertyAnimation,
    QRect,
    QSequentialAnimationGroup,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget


def fade_in(widget: QWidget, duration: int = 160, parent: QObject | None = None) -> QPropertyAnimation:
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    effect.setOpacity(0.0)

    anim = QPropertyAnimation(effect, b"opacity", parent or widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return anim


def fade_out(widget: QWidget, duration: int = 140, on_finished=None) -> QPropertyAnimation:
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        effect.setOpacity(1.0)

    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(effect.opacity())
    anim.setEndValue(0.0)
    anim.setEasingCurve(QEasingCurve.Type.InCubic)
    if on_finished:
        anim.finished.connect(on_finished)
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return anim


def scale_in(widget: QWidget, duration: int = 180) -> QPropertyAnimation:
    """Grows the widget from 96% to 100% of its target geometry."""
    target = widget.geometry()
    start = QRect(
        target.x() + int(target.width() * 0.02),
        target.y() + int(target.height() * 0.02),
        int(target.width() * 0.96),
        int(target.height() * 0.96),
    )
    widget.setGeometry(start)

    anim = QPropertyAnimation(widget, b"geometry", widget)
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(target)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return anim


def open_animation(widget: QWidget) -> QSequentialAnimationGroup:
    """Combined fade + scale used when opening dialogs."""
    fade_in(widget)
    scale_in(widget)
