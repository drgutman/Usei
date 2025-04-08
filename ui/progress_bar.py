import sys
from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QTimer, Qt, QRectF, QPointF, pyqtSlot 
)
from PyQt6.QtWidgets import (
    QProgressBar, QApplication, QWidget, QVBoxLayout, QPushButton, QStyleOptionProgressBar, QStyle
)
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QPalette, QGradient, QBrush, QTransform


from core.utils import SettingsManager
settings_manager = SettingsManager()

class AnimatedProgressBar(QProgressBar):
    def __init__(self, *args, **kwargs):
        # Call the QProgressBar constructor
        super().__init__(*args, **kwargs)
        self._target_value = self.value()
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setEasingCurve(QEasingCurve(QEasingCurve.Type.InOutCubic))
        self.animation.setDuration(500) # Default duration

    def _clamp(self, value):
        # Use float for target value to allow fractional increments
        min_val = float(self.minimum())
        max_val = float(self.maximum())
        return max(min_val, min(value, max_val))

    def addValue(self, value: int):
        # Keep input as int, but internal target is float
        new_target = self._target_value + float(value)
        self.setValueAnimated(new_target)



    # Accept float for internal consistency, but clamp result for QProgressBar
    @pyqtSlot(float)
    def setValueAnimated(self, value: float):
        clamped_value_float = self._clamp(value)
        # Only update target if it actually changes after clamping
        if self._target_value != clamped_value_float:
            self._target_value = clamped_value_float
            self._start_animation()
        # If the clamped value is the current value, ensure target is synced
        # Compare integer part for QProgressBar's value
        elif int(self.value()) == int(clamped_value_float):
             self._target_value = clamped_value_float


    def _start_animation(self):
        current = self.value()
        # Target for animation is the integer part of our float target
        target_int = int(self._target_value)

        # Clamp target_int just in case float rounding causes issues
        target_int_clamped = max(self.minimum(), min(target_int, self.maximum()))

        if current == target_int_clamped:
            # Ensure internal float target is still set correctly
            # self._target_value = float(target_int_clamped) # Keep the float precision
            return

        self.animation.stop()
        self.animation.setStartValue(current)
        self.animation.setEndValue(target_int_clamped)
        self.animation.start()


    # Override setValue to handle float target
    def setValue(self, value: int):
        # Immediate value set without animation
        clamped_value = max(self.minimum(), min(value, self.maximum()))
        self._target_value = float(clamped_value) # Keep target in sync as float
        self.animation.stop()
        super().setValue(clamped_value) # Use super's setValue

    def setDuration(self, duration_ms: int):
        self.animation.setDuration(duration_ms)

    def setEasingCurve(self, curve: QEasingCurve):
        self.animation.setEasingCurve(curve)


    def setMinimum(self, min_val: int):
        super().setMinimum(min_val)
        self._target_value = self._clamp(self._target_value)
        if self.animation.state() == QPropertyAnimation.State.Running:
             self._start_animation() # Restart animation with potentially new clamped target
        else:
             self.setValue(int(self.value())) # Re-clamp current value if needed

    def setMaximum(self, max_val: int):
        super().setMaximum(max_val)
        self._target_value = self._clamp(self._target_value)
        if self.animation.state() == QPropertyAnimation.State.Running:
             self._start_animation() # Restart animation with potentially new clamped target
        else:
             self.setValue(int(self.value())) # Re-clamp current value if needed

    def setRange(self, minimum: int, maximum: int):
        super().setRange(minimum, maximum)
        self._target_value = self._clamp(self._target_value)
        if self.animation.state() == QPropertyAnimation.State.Running:
             self._start_animation() # Restart animation with potentially new clamped target
        else:
             self.setValue(int(self.value())) # Re-clamp current value if needed

    # Expose target value (as float)
    def targetValue(self) -> float:
        return self._target_value


class IndeterminateAnimatedProgressBar(AnimatedProgressBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._gradient_offset = 10
        self._pattern_width = 1000
        self._gradient_step = 4
        self._bg_animation_timer = QTimer(self)
        self._bg_animation_timer.timeout.connect(self._update_gradient_animation)
        self._bg_animation_timer.setInterval(16) # ~60 FPS for background shimmer
        self._bg_animation_timer.start()

        # --- NEW: Keep-Alive Animation Setup ---
        self._keep_alive_increment = 0.15  # Progress points per tick (adjust for speed)
        self._keep_alive_interval = 250   # Milliseconds between ticks (adjust for speed)
        self._next_milestone_target = float(self.maximum()) # Default to max, allow keep-alive initially

        self._keep_alive_timer = QTimer(self)
        self._keep_alive_timer.timeout.connect(self._tick_keep_alive)
        self._keep_alive_timer.setInterval(self._keep_alive_interval)
        self._keep_alive_timer.start()

    @pyqtSlot()
    def _tick_keep_alive(self):
        # Only increment if the current target is below the next known milestone
        # And also below the overall maximum
        if (self._target_value < self._next_milestone_target and
            self._target_value < float(self.maximum())):

            # Calculate potential new target
            new_target = self._target_value + self._keep_alive_increment

            # Ensure it doesn't exceed the milestone or the max value
            capped_target = min(new_target, self._next_milestone_target, float(self.maximum()))

            # Update the internal target value directly
            # Use setValueAnimated to trigger the smooth visual update
            if capped_target > self._target_value:
                 # print(f"KeepAlive Tick: {self._target_value:.2f} -> {capped_target:.2f} (Milestone: {self._next_milestone_target})") # Debug
                 self.setValueAnimated(capped_target)

    @pyqtSlot(int)
    def set_next_milestone_target(self, percentage: int):
        # Ensure the milestone is within the valid range
        clamped_milestone = float(max(self.minimum(), min(percentage, self.maximum())))
        # print(f"KeepAlive Milestone Set: {clamped_milestone}") # Debug
        self._next_milestone_target = clamped_milestone
        # Optional: If current value already exceeds new milestone, clamp it?
        # Or just let keep-alive stop naturally. Let's try the latter first.

    def _update_gradient_animation(self):
        self._gradient_offset = (self._gradient_offset + self._gradient_step) % self._pattern_width
        self.update() # Request repaint


    def set_background_animation_enabled(self, enabled: bool):
        if enabled:
            if not self._bg_animation_timer.isActive():
                self._gradient_offset = 0
                self._bg_animation_timer.start()
                self.update()
        else:
            if self._bg_animation_timer.isActive():
                self._bg_animation_timer.stop()
                self.update()

    def paintEvent(self, event):
        theme = settings_manager.get('SETTINGS/Theme')
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        opt = QStyleOptionProgressBar()
        self.initStyleOption(opt) # Fills opt with current state (uses int value)

        if theme == "Dark":
            _base_color = QColor(45, 45, 45, 255)
            _shine_color = QColor(72, 72, 72, 255)
        else:
            _base_color = QColor(125, 125, 125, 255)
            _shine_color = QColor(170, 170, 170, 255)

        groove_rect = self.style().subElementRect(QStyle.SubElement.SE_ProgressBarGroove, opt, self)
        if self._bg_animation_timer.isActive():
             pattern_gradient = QLinearGradient(QPointF(0, 0), QPointF(self._pattern_width, 0))
             pattern_gradient.setColorAt(0.0,  _base_color)
             pattern_gradient.setColorAt(0.38,  _base_color)
             pattern_gradient.setColorAt(0.5,  _shine_color)
             pattern_gradient.setColorAt(0.62,  _base_color)
             pattern_gradient.setColorAt(1.0,  _base_color)

             pattern_gradient.setSpread(QGradient.Spread.RepeatSpread)
             brush = QBrush(pattern_gradient)
             transform = QTransform()
             transform.translate(self._gradient_offset, 0)
             brush.setTransform(transform)
             painter.fillRect(groove_rect, brush)
        else:
            fallback_bg = QColor(45, 45, 45, 255) if theme == "Dark" else QColor(125, 125, 125, 255)
            painter.fillRect(QRectF(groove_rect), fallback_bg)



        # --- 2. Draw Progress Bar Chunk (Use self.value() which is animated int) ---
        # QProgressBar's value property IS the animated value.
        # Our internal _target_value (float) drives the animation end point.
        progress = self.value() # Use the current animated integer value
        maximum = self.maximum()
        minimum = self.minimum()

        chunk_rect = QRectF()
        if maximum > minimum:
            # Use the integer progress value for ratio calculation
            progress_ratio = float(progress - minimum) / float(maximum - minimum)
            chunk_width = groove_rect.width() * progress_ratio
            chunk_rect = QRectF(
                groove_rect.x(), groove_rect.y(), chunk_width, groove_rect.height()
            )
            if progress == maximum:
                 chunk_rect.setWidth(groove_rect.width())

            painter.save()
            painter.setClipRect(groove_rect)
            if chunk_rect.isValid() and chunk_rect.width() > 0:
                 # --- Debug Print (Optional) ---
                 # print(f"Paint - Value: {progress}, Target: {self._target_value:.2f}, Milestone: {self._next_milestone_target}, ChunkW: {chunk_rect.width():.2f}")
                 painter.fillRect(chunk_rect, self.palette().highlight())
            painter.restore()

        # --- 3. Draw Text (Unchanged) ---
        if self.isTextVisible():
            # ... (existing text drawing code) ...
            text = self.text()
            text_rect = self.style().subElementRect(QStyle.SubElement.SE_ProgressBarLabel, opt, self)
            text_color_role = QPalette.ColorRole.Text
            effective_chunk_rect = chunk_rect if maximum > minimum and chunk_rect.isValid() else QRectF()
            if effective_chunk_rect.intersects(QRectF(text_rect)):
                 text_color_role = QPalette.ColorRole.HighlightedText
            painter.setPen(self.palette().color(text_color_role))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)