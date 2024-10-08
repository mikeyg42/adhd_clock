from PyQt5.QtCore import Qt, QSize, QPoint, QPointF, QRectF, QEasingCurve, QPropertyAnimation, QParallelAnimationGroup, pyqtSlot, pyqtProperty
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtGui import QColor, QBrush, QPen, QPainter

class AnimatedToggle(QCheckBox):
    """Custom QCheckBox widget that behaves like a toggle switch with animations."""

    # Define shared pen objects for transparency and default styles
    _transparent_pen = QPen(Qt.transparent)
    _light_grey_pen = QPen(Qt.lightGray)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.bar_color_unchecked=QColor(251,144,98)
        self.bar_color_checked =QColor(206,73,147)

        self.handle_color=QColor(238,93,108)
        
        self.pulse_unchecked_color=QColor(238,175,97)
        self.pulse_checked_color=QColor(106,13,131) 
    
        # Initialize animation properties
        self._handle_position = 0
        self._pulse_radius = 0

        # Configure the toggle animations
        self.animation = QPropertyAnimation(self, b"handle_position", self)
        self.animation.setEasingCurve(QEasingCurve.InQuad)
        self.animation.setDuration(200)

        self.pulse_anim = QPropertyAnimation(self, b"pulse_radius", self)
        self.pulse_anim.setDuration(350)
        self.pulse_anim.setStartValue(3)
        self.pulse_anim.setEndValue(18)

        # Group animations for smooth transitions
        self.animations_group = QParallelAnimationGroup()
        self.animations_group.addAnimation(self.animation)
        self.animations_group.addAnimation(self.pulse_anim)

        self.stateChanged.connect(self.setup_animation)
            
    # def make_less_saturated_and_lighter(self, color):
    #     h, s, v, a = color.getHsv()
    #     new_saturation = int(max(s / 1.6, 1)) # unchecked should be higher value and lower saturation
    #     newColor = QColor()
    #     new_value = int(min(v * 1.6, 255))
    #     print(f"hue = {h}, new value = {new_value} and new_saturation = {new_saturation}")
    #     newColor.setHsv(h, new_saturation, new_value, 0)
    #     return newColor
  
    def sizeHint(self):
        return QSize(40,30)

    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    @pyqtSlot(int)
    def setup_animation(self, value):
        """Start the toggle animation based on the state."""
        self.animations_group.stop()
        self.animation.setEndValue(1 if value else 0)
        self.animations_group.start()

    def paintEvent(self, e):
        """Custom paint event to draw the toggle with dynamic labels."""
        contRect = self.contentsRect()

        # Add fixed margins to control the overall size and placement
        left_margin = 8
        right_margin = 12
        top_margin = 0
        bottom_margin = 0

        # Adjust the rectangle dimensions based on these margins
        inner_width = contRect.width() - left_margin - right_margin
        inner_height = contRect.height() - top_margin - bottom_margin
        handle_radius = round(0.4 * inner_height) 
        trailLength = contRect.width() - 4 * handle_radius
        xPos = contRect.x() + 2 * handle_radius + trailLength * self._handle_position

        # Setup painter
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(self._transparent_pen)

        # Draw the bar (with fixed margins)
        bar_rect = QRectF(left_margin, top_margin, inner_width - handle_radius, 0.5 * inner_height)
        bar_rect.moveCenter(QPointF(left_margin + inner_width / 2, top_margin + inner_height / 2))  # Ensure the bar is centered
        rounding = bar_rect.height() / 2  # makes for pill-like appearance
        bar_brush = QBrush(self.bar_color_checked if self.isChecked() else self.bar_color_unchecked)
        p.setBrush(bar_brush)
        p.drawRoundedRect(bar_rect, rounding, rounding)

        # Draw pulse animation (smaller pulse)
        if self.pulse_anim.state() == QPropertyAnimation.Running:
            pulse_brush = QBrush(self.pulse_checked_color if self.isChecked() else self.pulse_unchecked_color)
            p.setBrush(pulse_brush)
            p.drawEllipse(QPointF(xPos, bar_rect.center().y()), self._pulse_radius, self._pulse_radius)

        # Draw the handle (smaller handle)
        handle_brush = QBrush(self.handle_color)
        p.setBrush(handle_brush)
        p.drawEllipse(QPointF(xPos, bar_rect.center().y()), handle_radius, handle_radius)

        # Draw labels (24hr / 12hr) at handle location
        font = p.font()
        
        # Logic to enlarge and change color for active label
        if self.isChecked():
            # 24hr label active
            p.setPen(QPen(QColor(50, 250, 250)))  # Cyan color
            font.setPointSize(12)  # Larger font size when active
            p.setFont(font)
            font.setBold(True)
            p.drawText(QPointF(xPos - 10, bar_rect.center().y() + 5), "24hr")
            
            # 12hr label inactive (transparent)
            p.setPen(QPen(QColor(0, 0, 0, 0)))  # Transparent color
            font.setPointSize(12)  # Default font size
            p.setFont(font)
            p.drawText(QPointF(contRect.x() + 5 +handle_radius, bar_rect.center().y() + 5), "12hr")
        else:
            # 12hr label active
            p.setPen(QPen(QColor(50, 250, 250)))  # Cyan color
            font.setPointSize(10)  # Larger font size when active
            p.setFont(font)
            font.setBold(True)
            p.drawText(QPointF(xPos - 10, bar_rect.center().y() + 5), "12hr")
            
            # 24hr label inactive (transparent)
            p.setPen(QPen(QColor(0, 0, 0, 0)))  # Transparent color
            font.setPointSize(10)  # Default font size
            p.setFont(font)
            p.drawText(QPointF(contRect.x() + 5 + handle_radius, bar_rect.center().y() + 5), "24hr")

        p.end()

    @pyqtProperty(float)
    def handle_position(self):
        return self._handle_position

    @handle_position.setter
    def handle_position(self, pos):
        self._handle_position = pos
        self.update()

    @pyqtProperty(float)
    def pulse_radius(self):
        return self._pulse_radius

    @pulse_radius.setter
    def pulse_radius(self, pos):
        self._pulse_radius = pos
        self.update()
