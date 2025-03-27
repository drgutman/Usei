"""
# Animate to 50
progress_bar.setValueAnimated(50)

# Add 30 to current target
progress_bar.addValue(30)

# Set immediate value
progress_bar.setValue(100)

# Customize animation properties
progress_bar.setDuration(1000)
progress_bar.setEasingCurve(QEasingCurve(QEasingCurve.Type.OutBounce))

"""
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QProgressBar

class AnimatedProgressBar(QProgressBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._target_value = self.value()
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setEasingCurve(QEasingCurve(QEasingCurve.Type.InOutCubic))
        self.animation.setDuration(500)
        self.animation.finished.connect(self._check_finished)

    def _clamp(self, value):
        return max(self.minimum(), min(value, self.maximum()))

    def addValue(self, value: int):
        new_target = self._target_value + value
        self.setValueAnimated(new_target)

    def setValueAnimated(self, value: int):
        self._target_value = self._clamp(value)
        self._start_animation()

    def _start_animation(self):
        current = self.value()
        target = self._target_value
        if current == target:
            return
        self.animation.stop()
        self.animation.setStartValue(current)
        self.animation.setEndValue(target)
        self.animation.start()

    def setValue(self, value: int):
        # Immediate value set without animation
        self._target_value = self._clamp(value)
        self.animation.stop()
        super().setValue(self._target_value)

    def setDuration(self, duration_ms: int):
        self.animation.setDuration(duration_ms)

    def setEasingCurve(self, curve: QEasingCurve):
        self.animation.setEasingCurve(curve)

    def _check_finished(self):
        # Ensure final value matches target after animation
        if self.value() != self._target_value:
            super().setValue(self._target_value)

    def setMinimum(self, min_val: int):
        super().setMinimum(min_val)
        self._target_value = self._clamp(self._target_value)

    def setMaximum(self, max_val: int):
        super().setMaximum(max_val)
        self._target_value = self._clamp(self._target_value)

    def setRange(self, minimum: int, maximum: int):
        super().setRange(minimum, maximum)
        self._target_value = self._clamp(self._target_value)

