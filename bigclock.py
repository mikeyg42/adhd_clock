import sys
import logging
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QDesktopWidget,
    QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QStackedLayout,
    QSlider, QComboBox, QLineEdit, QDialog, QDialogButtonBox, QFileDialog, QColorDialog,
    QCheckBox, QDoubleSpinBox
)
from PyQt5.QtCore import (
    QTimer, Qt, QBasicTimer, QPropertyAnimation, QEasingCurve, 
    pyqtProperty, QUrl
)
from PyQt5.QtGui import (
    QFont, QFontDatabase, QPainter, QColor, QPalette
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

# Configuration Constants - uncustomizable
BUTTON_COLOR = "purple"
BUTTON_TEXT_COLOR = "white"
WIGGLE_BACKGROUND_COLOR = "white"

# Global Defaults for Colors
DEFAULT_BACKGROUND_COLOR = QColor(0, 0, 0)  # Black
DEFAULT_FLASH_COLOR = QColor(255, 0, 0)      # Red
DEFAULT_CLOCK_TEXT_COLOR = QColor(255, 255, 255)  # White
DEFAULT_BUTTON_COLOR = QColor(128, 0, 128)    # Purple

DEFAULT_FLASH_DURATION = 2.5  # in seconds
DEFAULT_FLASH_REGULARITY = 15  # in minutes
DEFAULT_VOLUME_LEVEL = 0.3

# Locate the font file and audio clip
FONT = ""  # leave empty to use the font at FONT_PATH
def resource_path(relative_path):
    """ Get the absolute path to a resource, considering both development and PyInstaller paths. """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

# Update your resource paths
RESOURCE_PATH = resource_path('resources')
FONT_PATH = os.path.join(RESOURCE_PATH, 'bayer_universal_type.ttf')
DEFAULT_AUDIO_PATH = os.path.join(RESOURCE_PATH, 'wiggle_wiggle_LMFAO_clip.mp3')

# --------------------------------------------------

# Configure logging
logging.basicConfig(level=logging.INFO)

class AppConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init_settings()
        return cls._instance

    def init_settings(self):
        """Initialize default settings."""
        self.use_24h_format = True
        self.flash_duration = 2.5
        self.flash_regularity = 15
        self.audio_path = DEFAULT_AUDIO_PATH
        self.volume_level = 0.3
        self.background_color = QColor(0, 0, 0)
        self.flash_color = QColor(255, 0, 0)
        self.clock_text_color = QColor(255, 255, 255)
        self.button_color = QColor(128, 0, 128)

    def update_setting(self, key, value):
        setattr(self, key, value)
        
# --------------------------------------------------

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Clock Settings")

        # Access the singleton instance
        self.config = AppConfig()
        
        # Set the initial values from the config instance
        self.use_24h_format = self.config.use_24h_format
        self.flash_duration = self.config.flash_duration
        self.flash_regularity = self.config.flash_regularity
        self.audio_path = self.config.audio_path
        self.volume_level = self.config.volume_level
        self.background_color = self.config.background_color
        self.flash_color = self.config.flash_color
        self.clock_text_color = self.config.clock_text_color
        self.button_color = self.config.button_color
        
        # Set the dialog on the primary screen (Screen 0)
        self.move_to_primary_screen()
        
        # UI Elements
        self.init_ui()

    def init_ui(self):
        """Set up the settings dialog UI."""
        layout = QVBoxLayout(self)

        # Flash Duration Slider
        layout.addWidget(QLabel("Flash Duration (1.0 to 10.0 seconds)"))
        self.flash_duration_input = QDoubleSpinBox(self)
        self.flash_duration_input.setRange(1.0, 10.0)  # Allow values from 1.0 to 10.0 seconds
        self.flash_duration_input.setSingleStep(0.1)    # Step size for fractional values
        self.flash_duration_input.setValue(self.flash_duration)
        layout.addWidget(self.flash_duration_input)
        
        # Flash Regularity Dropdown
        layout.addWidget(QLabel("Flash Regularity (minutes)"))
        self.flash_regularity_combo = QComboBox()
        self.flash_regularity_combo.addItems(["5", "6", "10", "12", "15", "20", "30"])
        self.flash_regularity_combo.setCurrentText(str(self.flash_regularity))
        layout.addWidget(self.flash_regularity_combo)
        
        # 24-hour format checkbox
        self.use_24h_checkbox = QCheckBox("Use 24-hour format")
        self.use_24h_checkbox.setChecked(self.use_24h_format)
        layout.addWidget(self.use_24h_checkbox)

        # Audio File Selection
        layout.addWidget(QLabel("Audio File Path"))
        self.audio_input = QLineEdit(self.audio_path)
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_audio)
        audio_layout = QHBoxLayout()
        audio_layout.addWidget(self.audio_input)
        audio_layout.addWidget(self.browse_button)
        layout.addLayout(audio_layout)

        # Volume Slider
        layout.addWidget(QLabel("Volume Level"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.volume_level)) # saved as an integer between 0 and 100
        layout.addWidget(self.volume_slider)

        # Color Pickers
        layout.addWidget(QLabel("Background Color"))
        self.background_color_button = QPushButton()
        self.set_color_button(self.background_color_button, self.background_color)
        self.background_color_button.clicked.connect(self.choose_background_color)
        layout.addWidget(self.background_color_button)

        layout.addWidget(QLabel("Flash Color"))
        self.flash_color_button = QPushButton()
        self.set_color_button(self.flash_color_button, self.flash_color)
        self.flash_color_button.clicked.connect(self.choose_flash_color)
        layout.addWidget(self.flash_color_button)

        layout.addWidget(QLabel("Clock Text Color"))
        self.clock_text_color_button = QPushButton()
        self.set_color_button(self.clock_text_color_button, self.clock_text_color)
        self.clock_text_color_button.clicked.connect(self.choose_clock_text_color)
        layout.addWidget(self.clock_text_color_button)

        layout.addWidget(QLabel("Button Color"))
        self.button_color_button = QPushButton()
        self.set_color_button(self.button_color_button, self.button_color)
        self.button_color_button.clicked.connect(self.choose_button_color)
        layout.addWidget(self.button_color_button)
        
        # Save and Start Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def set_color_button(self, button, color):
        """Set the background color of a QPushButton."""
        palette = button.palette()
        palette.setColor(QPalette.Button, color)
        button.setAutoFillBackground(True)
        button.setPalette(palette)
        button.update()
        
    def choose_background_color(self):
        """Launch color picker for background color."""
        color = QColorDialog.getColor(self.background_color, self, "Select Background Color")
        if color.isValid():
            self.background_color = color
            self.set_color_button(self.background_color_button, color)

    def choose_flash_color(self):
        """Launch color picker for flash color."""
        color = QColorDialog.getColor(self.flash_color, self, "Select Flash Color")
        if color.isValid():
            self.flash_color = color
            self.set_color_button(self.flash_color_button, color)

    def choose_clock_text_color(self):
        """Launch color picker for clock text color."""
        color = QColorDialog.getColor(self.clock_text_color, self, "Select Clock Text Color")
        if color.isValid():
            self.clock_text_color = color
            self.set_color_button(self.clock_text_color_button, color)

    def choose_button_color(self):
        """Launch color picker for button color."""
        color = QColorDialog.getColor(self.button_color, self, "Select Button Color")
        if color.isValid():
            self.button_color = color
            self.set_color_button(self.button_color_button, color)\
                
    def browse_audio(self):
        """Open a file dialog to select the audio file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.mp3 *.wav)")
        if file_path:
            self.audio_path = file_path
            self.audio_input.setText(file_path)


    def accept(self):
        """Save the settings when 'Ok' is pressed."""
        self.config.flash_duration = self.flash_duration_input.value()  # Update to use QDoubleSpinBox value
        self.config.use_24h_format = self.use_24h_checkbox.isChecked()
        self.config.flash_regularity = int(self.flash_regularity_combo.currentText())
        self.config.audio_path = self.audio_input.text()
        self.config.volume_level = self.volume_slider.value() / 100
        self.config.background_color = self.background_color
        self.config.flash_color = self.flash_color
        self.config.clock_text_color = self.clock_text_color
        self.config.button_color = self.button_color
        super().accept()
        
    def move_to_primary_screen(self):
        """Move the dialog to the primary (main) screen."""
        desktop = QDesktopWidget()
        primary_screen_geometry = desktop.screenGeometry(0)  # Get the primary screen (screen 0)
        dialog_width = self.width()
        dialog_height = self.height()
        # Center the dialog on the primary screen
        self.move(
            primary_screen_geometry.center().x() - dialog_width // 2,
            primary_screen_geometry.center().y() - dialog_height // 2
        )
        
# --------------------------------------------------

class MainWindow(QWidget):
    """
    Main application window that manages the clock display and hourly animations.
    
    Both the "wiggling" animation widget and the clock display widget are constituitively 
    active, but only one is visible at a time by way of the QStackedLayout. 
    """

    def __init__(self):
        super().__init__()
        self.config = AppConfig()
        self.stacked_layout = QStackedLayout()

        # Initialize clock and wiggle flash widgets
        self.clock_app = BigClockApp(self)
        self.wiggle_flash = WiggleFlash(self)

        # Set up the stacked layout
        self.stacked_layout.addWidget(self.clock_app)
        self.stacked_layout.addWidget(self.wiggle_flash)

        # Set up the main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(self.stacked_layout)
        self.stacked_layout.setCurrentWidget(self.clock_app)
        self.setLayout(main_layout)

        # Move the application to the extended monitor
        self.move_to_extended_monitor()
    

    def switch_to_wiggle_flash(self, hour):
        """Switch to the WiggleFlash screen for an hour change."""
        self.wiggle_flash.set_hour(hour)
        self.stacked_layout.setCurrentIndex(1)
        self.wiggle_flash.update()
        QTimer.singleShot(8000, self.switch_back_to_clock) # this is set as is mostly because the audio clip is 7.5 seconds long

    def switch_back_to_clock(self):
        """Switch back to the clock display."""
        self.stacked_layout.setCurrentWidget(self.clock_app)
        
    def move_to_extended_monitor(self):
        """Move the window to the extended monitor if available."""
        desktop = QDesktopWidget()
        screen_count = desktop.screenCount()

        if screen_count > 1:
            extended_screen = desktop.screenGeometry(1)
            self.setGeometry(extended_screen)
            self.clock_app.setFixedSize(extended_screen.width(), extended_screen.height())
            self.wiggle_flash.setFixedSize(extended_screen.width(), extended_screen.height())
        else:
            self.showMaximized()

class BigClockApp(QWidget):
    """A fullscreen clock application with a customizable display."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.config = AppConfig()
        
        # Set up timer for updating time
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(400)  # Update every 500ms

        # Set up timer for flashing
        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self.stop_flash)

        # Initialize flash color
        self._flash_color = QColor(self.config.background_color)
        
        # Set up flash animation
        self.flash_animation = QPropertyAnimation(self, b"flash_color")
        self.flash_animation.setDuration(500)
        self.flash_animation.setLoopCount(6)  # Ensure an even number of flashes
        self.flash_animation.setStartValue(self.config.background_color)
        self.flash_animation.setEndValue(self.config.flash_color)
        self.flash_animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.init_ui()

    def init_ui(self):    
        """Initialize the user interface."""
        self.setWindowTitle("Big Clock")
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        self.set_background_color(self.config.background_color)        
        self.load_font()
        
        # Initialize UI elements
        self.date_label = self.create_date_label()
        self.time_label = self.create_time_label()
        self.close_button = self.create_close_button()
        self.settings_button = self.create_settings_button()

        self.setup_layouts()
        self.update_time()
        
    def create_settings_button(self):
        """Create and return the settings button."""
        button = QPushButton(" : ) ", self)
        button.setFont(self.font)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.config.button_color.name()};
                color: black;
                border: none;
                padding: 5px;
                font-size: 20px;
            }}
            QPushButton:hover {{
                background-color: orange;
            }}
        """)
        button.clicked.connect(self.open_settings_dialog)  # Connect to show_settings_dialog method
        button.setFixedSize(80, 40)
        return button

    def create_date_label(self):
        """Create and return the date label."""
        label = QLabel(self)
        
        label.setStyleSheet(f"color: {self.config.clock_text_color.name()}; font-family: {self.font.family()}; font-size: 42px;")
        label.setAlignment(Qt.AlignCenter)
        return label

    def create_time_label(self):
        """Create and return the time label."""
        label = QLabel(self)
        label.setFont(self.font)
        if self.config.use_24h_format: # the "am" and "pm", if used, cause the text to be too large and get clipped on edges. 
            label.setStyleSheet(f"color: {self.config.clock_text_color.name()}; font-family: {self.font.family()}; font-size: 480px;")
        else:
            label.setStyleSheet(f"color: {self.config.clock_text_color.name()}; font-family: {self.font.family()}; font-size: 390px;")
        label.setAlignment(Qt.AlignCenter)
        return label

    def create_close_button(self):
        """Create and return the close button."""
        button = QPushButton("X", self)
        button.setFont(QFont('Arial', 16))
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.config.button_color.name()};
                color: red;
                border: none;
                padding: 5px;
                font-size: 20px;
            }}
            QPushButton:hover {{
                background-color: red;
            }}
        """)
        button.clicked.connect(QApplication.quit)
        #button.clicked.connect(lambda: sys.exit(0)) 
  
        button.setFixedSize(40, 40)
        return button

    def set_background_color(self, color):
        """Set the background color of the widget."""
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def load_font(self):
        """Load the custom font or use default."""
        font_db = QFontDatabase()
        try:
            if FONT:
                self.font = QFont(FONT)
            elif FONT_PATH:
                font_id = font_db.addApplicationFont(FONT_PATH)
                if font_id == -1:
                    raise RuntimeError("Failed to load font")
                font_family = font_db.applicationFontFamilies(font_id)[0]
                self.font = QFont(font_family)
            else:
                raise RuntimeError("No font specified")
        except Exception as e:
            logging.warning(f"Failed to load specified font. Defaulting to Helvetica: {e}")
            self.font = QFont('Helvetica')
        # Set a fixed font size that won't change
        self.font.setPointSize(480)
        
    def setup_layouts(self):
        """Set up the layout for the widget with a fixed size to fill the second monitor."""
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.close_button, alignment=Qt.AlignLeft | Qt.AlignTop)
        
        # Add the settings button next to the close button
        top_layout.addWidget(self.settings_button, alignment=Qt.AlignLeft | Qt.AlignTop)

        # Add a spacer between the buttons and the date label
        top_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        top_layout.addWidget(self.date_label, alignment=Qt.AlignCenter)
        top_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Main clock layout
        clock_layout = QVBoxLayout()
        clock_layout.addLayout(top_layout)
        clock_layout.addWidget(self.time_label, alignment=Qt.AlignCenter)

        # Add spacers to center the clock
        clock_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(clock_layout)

        # Set main layout margins to prevent items being too close to edges
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Apply the layout
        self.setLayout(main_layout)
        
    def update_time(self):
        """Update the displayed time and date."""
        now = datetime.now()
        if self.config.use_24h_format:
            time_format = "%H:%M:%S"
        else:
            time_format = "%I:%M:%S %p"
        self.time_label.setText(now.strftime(time_format))
        self.date_label.setText(now.strftime("%A, %B %d, %Y"))
        
        # Check if it's on the hour (0 minutes and 0 seconds)
        if now.minute == 0 and now.second == 0:
            if isinstance(self.parent(), MainWindow):
                self.parent().switch_to_wiggle_flash(now.hour)
        elif now.minute % self.config.flash_regularity == 0 and now.second == 0:
            self.start_flash()  # Regular flashing
                          
    def start_flash(self):
        self.flash_animation.setStartValue(self.config.background_color)
        self.flash_animation.setEndValue(self.config.flash_color)
        self.flash_animation.setLoopCount(6)  # Ensure an even number of flashes
        self.flash_animation.start()
        try:
            flash_duration_ms = int(self.config.flash_duration * 1000)  # Convert to integer milliseconds
            self.flash_timer.start(flash_duration_ms)
        except ValueError:
            logging.error(f"Invalid FLASH_DURATION: {self.config.flash_duration}. Using default of 2500ms.")
            self.flash_timer.start(2500)  # Default to 2.5 seconds if conversion fails
    
    def stop_flash(self):
        """Stop the flashing animation and reset the background."""
        self.flash_animation.stop()
        self.flash_timer.stop()
        self._flash_color = QColor(self.config.background_color)
        self.update()  # Trigger a repaint

    @pyqtProperty(QColor)
    def flash_color(self):
        return self._flash_color

    @flash_color.setter
    def flash_color(self, color):
        if self._flash_color != color:
            self._flash_color = color
            self.update()  # Trigger a repaint

    def paintEvent(self, event):
        """Custom paint event to handle background color changes."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._flash_color)
  
    # triggered when the settings button is clicked
    def show_settings_dialog(self):
        """Display the settings dialog and update the config if settings are modified."""
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec_() == QDialog.Accepted:
            # Update the config with new settings
            self.config.flash_duration = settings_dialog.flash_duration_input.value()
            self.config.use_24h_format = settings_dialog.use_24h_checkbox.isChecked()
            self.config.flash_regularity = int(settings_dialog.flash_regularity_combo.currentText())
            self.config.audio_path = settings_dialog.audio_input.text()
            self.config.volume_level = settings_dialog.volume_slider.value()
            self.config.background_color = settings_dialog.background_color
            self.config.flash_color = settings_dialog.flash_color
            self.config.clock_text_color = settings_dialog.clock_text_color
            self.config.button_color = settings_dialog.button_color

            # Apply updated settings dynamically
            self.set_background_color(self.config.background_color)
            self.date_label.setStyleSheet(f"color: {self.config.clock_text_color.name()}; font-family: {self.font.family()}; font-size: 42px;")
            self.time_label.setStyleSheet(f"color: {self.config.clock_text_color.name()}; font-family: {self.font.family()}; font-size: 480px;")
            self.close_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.config.button_color.name()};
                    color: white;
                    border: none;
                    padding: 5px;
                }}
                QPushButton:hover {{
                    background-color: red;
                }}
            """)
            self.settings_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.config.button_color.name()};
                    color: white;
                    border: none;
                    padding: 5px;
                }}
                QPushButton:hover {{
                    background-color: green;
                }}
            """)
    def open_settings_dialog(self):
        """Close the main window and open the settings dialog."""
        # Close the main window
        self.main_window.close()

        # Display the settings dialog
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec_() == QDialog.Accepted:
            # Update the config with new settings
            self.config.flash_duration = settings_dialog.flash_duration_input.value()
            self.config.use_24h_format = settings_dialog.use_24h_checkbox.isChecked()
            self.config.flash_regularity = int(settings_dialog.flash_regularity_combo.currentText())
            self.config.audio_path = settings_dialog.audio_input.text()
            self.config.volume_level = settings_dialog.volume_slider.value()
            self.config.background_color = settings_dialog.background_color
            self.config.flash_color = settings_dialog.flash_color
            self.config.clock_text_color = settings_dialog.clock_text_color
            self.config.button_color = settings_dialog.button_color

            # Reopen the main window with updated settings
            new_window = MainWindow()
            new_window.show()

# --------------------------------------------------

class WiggleFlash(QWidget):
    """Widget for displaying wiggling text animation on hour change."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = AppConfig()
        self.text = ""
        self.step = 0
        self.timer = QBasicTimer() 

        # Set up background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("white"))
        self.setPalette(palette)

        # Set up font
        self.font = QFont('Comic Sans MS', 144)  # Adjust size as needed
        self.setFont(self.font)

        # Start the timer for animation
        self.timer.start(60, self)  # This registers a timer event with the Qt event loop

        # Set up audio player
        self.player = QMediaPlayer()
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.config.audio_path)))
        if self.config.volume_level >1:
            self.player.setVolume(int(self.config.volume_level))
        else:
            self.player.setVolume(int(self.config.volume_level * 100))  

    def set_hour(self, hour):
        """Set the text to display the current hour and play audio."""
        if self.config.use_24h_format:
            self.text = f"IT'S NOW {hour:02d}:00, BITCH!"
        else:
            am_pm = "AM" if hour < 12 else "PM"
            hour = hour if hour <= 12 else hour - 12
            hour = 12 if hour == 0 else hour
            self.text = f"IT'S NOW {hour:d}:00 {am_pm}, BITCH!"
        self.player.play()
        self.update()

    def paintEvent(self, event):
        """Paint the wiggling text."""
        painter = QPainter(self)
        painter.setFont(self.font)
        metrics = painter.fontMetrics()

        # Center the text horizontally and vertically
        x = (self.width() - metrics.horizontalAdvance(self.text)) // 2
        y = (self.height() + metrics.ascent() - metrics.descent()) // 2

        # A sine table to give dy, the change in y coordinate, giving the text a wiggling effect
        sine_table = [0, 38, 71, 92, 100, 92, 71, 38, 0, -38, -71, -92, -100, -92, -71, -38]

        # Paint each letter of the text with a wiggling effect
        for i, char in enumerate(self.text):
            index = (self.step + i) % 16
            dy = (sine_table[index] * metrics.height()) // 400

            # Set color based on the step
            color = QColor()
            color.setHsv((15 - index) * 16, 255, 191)
            painter.setPen(color)

            # Draw each character with its y position modified by the sine table
            painter.drawText(x, y - dy, char)
            x += metrics.horizontalAdvance(char)

    def timerEvent(self, event):
        """Update the step for the wiggling animation."""
        if event.timerId() == self.timer.timerId():
            self.step += 1
            self.update()  # Trigger a repaint
        else:
            super().timerEvent(event)

# --------------------------------------------------

if __name__ == '__main__':
    app = QApplication(sys.argv)
    settings_dialog = SettingsDialog()
    if settings_dialog.exec_() == QDialog.Accepted:
        config = AppConfig()
        # Update the config with new settings
        config.flash_duration = settings_dialog.flash_duration_input.value()
        config.flash_regularity = int(settings_dialog.flash_regularity_combo.currentText())
        config.audio_path = settings_dialog.audio_input.text()
        config.volume_level = settings_dialog.volume_slider.value()
        config.background_color = settings_dialog.background_color
        config.flash_color = settings_dialog.flash_color
        config.clock_text_color = settings_dialog.clock_text_color
        config.button_color = settings_dialog.button_color
        config.use_24h_format = settings_dialog.use_24h_checkbox.isChecked()
        
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())