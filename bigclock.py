import sys
import logging
import os
import random
import pathlib
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QDesktopWidget,
    QVBoxLayout, QHBoxLayout, QSizePolicy, QStackedLayout,
    QSlider, QGroupBox, QLineEdit, QDialog, QDialogButtonBox, QFileDialog, 
    QColorDialog,QDoubleSpinBox, QStyle, QToolButton,QComboBox, QMessageBox
)
from PyQt5.QtCore import (
    QTimer, Qt, QBasicTimer, QPropertyAnimation, QEasingCurve, 
    pyqtProperty, QUrl, QCoreApplication, QSize, QPoint, pyqtSignal
)
from PyQt5.QtGui import (
    QFont, QFontDatabase, QPainter, QColor, QPalette
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QSoundEffect
from animated_toggle import AnimatedToggle


# ----------------------------------------------
QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

# Configuration Constants - uncustomizable
BUTTON_COLOR = "purple"
BUTTON_TEXT_COLOR = "white"
WIGGLE_BACKGROUND_COLOR = "white"

BUTTON_COLORS = [QColor(255, 160, 255), QColor(166, 255, 240)]
BUTTON_HOVER_COLORS = [QColor(160, 20, 160), QColor(0, 175, 150)]

# Global Defaults for Colors
DEFAULT_BACKGROUND_COLOR = QColor(0, 0, 0)  # Black
DEFAULT_FLASH_COLOR = QColor(255, 0, 0)      # Red
DEFAULT_CLOCK_TEXT_COLOR = QColor(255, 255, 255)  # White
DEFAULT_BUTTON_COLOR = QColor(128, 0, 128)    # Purple

DEFAULT_FLASH_DURATION = 5  # in seconds
DEFAULT_FLASH_REGULARITY = 15  # in minutes
DEFAULT_VOLUME_LEVEL = 0.3

# Locate the font file and audio clip
FONT = ""  # leave empty to use the font at FONT_PATH
def resource_path(relative_path):
    """ Get the absolute path to a resource, considering both development and PyInstaller paths. """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

# Update your resource paths
RESOURCE_PATH = pathlib.Path(resource_path('resources'))

FONT_PATH = RESOURCE_PATH / 'bayer_universal_type.ttf'
DEFAULT_AUDIO_PATH = RESOURCE_PATH / 'wiggle_wiggle_LMFAO_clip.mp3'

# --------------------------------------------------

# Configure logging
logging.basicConfig(level=logging.INFO)

class AppConfig:
    """Singleton class to manage application configuration settings."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init_settings()
        return cls._instance

    def init_settings(self):
        """Initialize default settings."""
        self.toggle_24h = True
        self.flash_duration = 9
        self.flash_regularity = 1
        self.audio_path = str(DEFAULT_AUDIO_PATH)  # Store as string
        self.volume_level = 0.3
        self.background_color = QColor(0, 0, 0)
        self.flash_color = QColor(255, 0, 0)
        self.clock_text_color = QColor(255, 255, 255)
        self.button_color = QColor(128, 0, 128)  # Refers to the two pushbuttons on the main clock screen

    def update_setting(self, key, value):
        """Update a setting."""
        setattr(self, key, value)
# --------------------------------------------------

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Clock Settings")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Access the singleton instance    
        self.config = AppConfig()

        # Set the dialog on the primary screen (Screen 0)
        # self.move_to_primary_screen()

        # create a dictionary to store the colors of the buttons
        self.color_buttons = {}
        
        # Initialize the sound effect for volume feedback
        self.init_sound_effect()
        
        # UI Elements
        self.init_ui()

    def init_ui(self):
        """Set up the settings dialog UI."""
        main_layout = QVBoxLayout(self)

        # Flash Settings Group
        flash_group = QGroupBox("Flash Settings")
        flash_layout = QVBoxLayout()

        # Flash Duration Input
        flash_layout.addWidget(QLabel("Flash Duration (1.0 to 10.0 seconds)"))
        self.flash_duration_input = QDoubleSpinBox(self)
        self.flash_duration_input.setRange(1.0, 10.0)
        self.flash_duration_input.setSingleStep(0.1)
        self.flash_duration_input.setValue(self.config.flash_duration)
        flash_layout.addWidget(self.flash_duration_input)

        # Flash Regularity Input (replaced QSpinBox with QComboBox)
        flash_layout.addWidget(QLabel("Flash Regularity (minutes)"))
        self.flash_regularity_combo = QComboBox(self)
        self.update_flash_regularity_options(60)  # Populate with divisors of 60
        self.flash_regularity_combo.setCurrentText(str(self.config.flash_regularity))  # Set initial value
        flash_layout.addWidget(self.flash_regularity_combo)

        flash_group.setLayout(flash_layout)
        main_layout.addWidget(flash_group)


        # Time Format Group
        time_format_group = QGroupBox("Time Format")
        time_format_layout = QHBoxLayout()
        time_format_layout.addWidget(QLabel("Use 24-hour Clock?"))
        self.toggle_24h_clock = AnimatedToggle()
        self.toggle_24h_clock.setChecked(self.config.toggle_24h)
        time_format_layout.addWidget(self.toggle_24h_clock)
        time_format_group.setLayout(time_format_layout)
        main_layout.addWidget(time_format_group)

        # Audio Settings Group
        audio_group = QGroupBox("Audio Settings")
        audio_layout = QVBoxLayout()

        # Audio File Selection
        audio_path_layout = QHBoxLayout()
        audio_path_layout.addWidget(QLabel("Audio File Path"))
        self.audio_input = QLineEdit(str(self.config.audio_path))
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_audio)
        audio_path_layout.addWidget(self.audio_input)
        audio_path_layout.addWidget(self.browse_button)
        audio_layout.addLayout(audio_path_layout)

        # Volume Slider with Label
        audio_layout.addWidget(QLabel("Volume Level"))
        volume_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.config.volume_level * 100))
        volume_layout.addWidget(self.volume_slider)
        self.volume_label = QLabel(f"{self.volume_slider.value()}%")
        volume_layout.addWidget(self.volume_label)
        audio_layout.addLayout(volume_layout)

        audio_group.setLayout(audio_layout)
        main_layout.addWidget(audio_group)

        self.volume_slider.valueChanged.connect(self.update_volume_label)
        self.volume_slider.valueChanged.connect(self.debounce_play_beep)


        # Color Settings Group
        color_group = QGroupBox("Color Settings")
        color_layout = QVBoxLayout()

        # Background Color
        self.create_color_picker(color_layout, "Background Color", self.config.background_color, "background_color")

        # Flash Color
        self.create_color_picker(color_layout, "Flash Color", self.config.flash_color, "flash_color")

        # Clock Text Color
        self.create_color_picker(color_layout, "Clock Text Color", self.config.clock_text_color, "clock_text_color")

        # Button Color
        self.create_color_picker(color_layout, "Button Color", self.config.button_color, "button_color")

        color_group.setLayout(color_layout)
        main_layout.addWidget(color_group)

        # Restore Defaults Button
        restore_defaults_button = QPushButton("Restore Defaults")
        restore_defaults_button.clicked.connect(self.restore_defaults)
        main_layout.addWidget(restore_defaults_button)

        # Accept and Exit Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.customize_buttons(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
        
    def update_flash_regularity_options(self, number):
        """Populate the combo box with divisors of the given number."""
        divisors = [i for i in range(1, number + 1) if number % i == 0]  # Divisors of 60
        self.flash_regularity_combo.clear()  # Clear existing items if any
        self.flash_regularity_combo.addItems([str(d) for d in divisors])  # Add divisors to combo box

    def restore_defaults(self):
        """Restore settings to default values."""
        self.flash_duration_input.setValue(DEFAULT_FLASH_DURATION)
        self.flash_regularity_combo.setCurrentText(str(DEFAULT_FLASH_REGULARITY))  # Update this line
        self.audio_input.setText(str(DEFAULT_AUDIO_PATH))
        self.volume_slider.setValue(int(DEFAULT_VOLUME_LEVEL * 100))
        self.toggle_24h_clock.setChecked(True)
        self.set_color_button(self.color_buttons['background_color'], DEFAULT_BACKGROUND_COLOR)
        self.set_color_button(self.color_buttons['flash_color'], DEFAULT_FLASH_COLOR)
        self.set_color_button(self.color_buttons['clock_text_color'], DEFAULT_CLOCK_TEXT_COLOR)
        self.set_color_button(self.color_buttons['button_color'], DEFAULT_BUTTON_COLOR)

    
    def update_volume_label(self, value):
        """Update the volume label to reflect the slider's current value."""
        self.volume_label.setText(f"{value}%")    
    
    def init_sound_effect(self):
        """Dynamically load all .wav files from the resources directory for volume slider feedback."""

        # List of beep sound files (only .wav files)
        self.beep_paths = list(RESOURCE_PATH.glob('*.wav'))

        # Clear the sound effects list before loading
        self.sound_effects = []

        # Preload all .wav files as QSoundEffect
        for path in self.beep_paths:
            sound = QSoundEffect()
            if path.exists():
                sound.setSource(QUrl.fromLocalFile(str(path)))
                sound.setLoopCount(1)  # Play the beep once per trigger
                sound.setVolume(self.config.volume_level)  # Initial volume
                self.sound_effects.append(sound)
                #logging.info(f"Beep sound loaded from: {path}")
            else:
                logging.error(f"Beep sound file not found: {path}")

        # Initialize a timer to debounce slider movements
        self.beep_timer = QTimer()
        self.beep_timer.setSingleShot(True)
        self.beep_timer.timeout.connect(self.play_random_beep)
        
    def play_random_beep(self):
        """Play a random beep sound based on the current volume."""
        if self.sound_effects:
            beep_sound = random.choice(self.sound_effects)  # Randomly select a sound effect
            beep_sound.setVolume(self.current_volume)  # Adjust volume based on slider
            beep_sound.stop()  # Stop any currently playing beep to prevent overlap
            beep_sound.play()
            logging.info(f"Playing beep sound at volume: {self.current_volume}")
        else:
            logging.warning("No beep sounds available to play.")


    def create_color_picker(self, layout, label_text, color, attribute_name):
        layout.addWidget(QLabel(label_text))
        button = QPushButton()
        self.set_color_button(button, color)
        button.clicked.connect(lambda: self.choose_color(button, attribute_name))
        layout.addWidget(button)
        self.color_buttons[attribute_name] = button

    def set_color_button(self, button, color):
        """Set the background color of a QPushButton."""
        palette = button.palette()
        palette.setColor(QPalette.Button, color)
        button.setAutoFillBackground(True)
        button.setPalette(palette)
        button.update()

    def choose_color(self, button, attribute_name):
        current_color = getattr(self.config, attribute_name)
        color = QColorDialog.getColor(current_color, self, f"Select {attribute_name.replace('_', ' ').title()} Color")
        if color.isValid():
            self.set_color_button(button, color)
            setattr(self.config, attribute_name, color)
            
    def browse_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.mp3 *.wav)")
        if file_path:
            self.audio_input.setText(file_path)
            self.config.audio_path = file_path
    
    def debounce_play_beep(self, value):
        """Start or restart the beep timer on slider value change."""
        self.current_volume = value / 100.0 if value > 1 else value
        self.beep_timer.start(200)  # Wait 200ms before playing beep
        
    def accept(self):
        """Save the settings when 'Ok' is pressed."""
        self.config.update_setting('flash_duration', self.flash_duration_input.value())
        self.config.update_setting('flash_regularity', int(self.flash_regularity_combo.currentText()))
        self.config.update_setting('audio_path', self.audio_input.text())
        self.config.update_setting('volume_level', self.volume_slider.value() / 100.0)
        self.config.update_setting('toggle_24h', self.toggle_24h_clock.isChecked())
        # Colors are already updated in choose_color
        super().accept()

    def reject(self):
        """Prompt user before closing the application when 'Cancel' is pressed."""
        reply = QMessageBox.question(
            self, 'Confirm Exit',
            "Are you sure you want to exit=?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QApplication.quit()
    def reject(self):
        """Prompt user before closing the settings dialog when 'Cancel' is pressed."""
        reply = QMessageBox.question(
            self, 'Confirm Exit',
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            super().reject()  # Close the dialog and return QDialog.Rejected
        # Else, do nothing and keep the dialog open


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

    def apply_button_style(self, button, color, hover_color):
        button.setMinimumHeight(50)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name()};
                color: black;
                border-radius: 10px;
                font-size: 16px;
                padding: 10px 12px;
            }}
            QPushButton:hover {{
                background-color: {hover_color.name()};
                color: red;
            }}
        """)
        
    def customize_buttons(self, button_box):
        """Customize the appearance of QDialogButtonBox buttons."""
        # Increase the font size of the buttons and apply styles
        button_font = QFont("Helvetica", 16)
        button_box.setFont(button_font)
        for i, button in enumerate(button_box.buttons()):
            button.setMinimumHeight(50)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BUTTON_COLORS[i].name()};
                    color: black;
                    border-radius: 10px;
                    font-size: 16px;
                    padding: 10px 12px;
                }}
                QPushButton:hover {{
                    background-color: {BUTTON_HOVER_COLORS[i].name()};
                    color: red;
                }}
            """)
            
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
            
    def update_audio_volume(self):
        self.wiggle_flash.player.setVolume(int(self.config.volume_level * 100))

class BigClockApp(QWidget):
    """A fullscreen clock application with a customizable display."""
    
    flashColorChanged = pyqtSignal()
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.config = AppConfig()
        
        # Set up timer for updating time
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(250)  # Update every so often

        # Set up timer for flashing
        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self.stop_flash)

        # Initialize flash color
        self._flash_color = QColor(self.config.background_color)
            
        # Parse configs set by user and determine the number of flashes and their duration
        self.determine_flash_length()
        
        # Set up flash animation
        self.flash_animation = QPropertyAnimation(self, b"flash_color")
        self.flash_animation.setDuration(self.flashDur)  # 500ms ish
        self.flash_animation.setLoopCount(self.numFlashes)  # Even number of flashes
        self.flash_animation.setStartValue(self.config.background_color)
        self.flash_animation.setEndValue(self.config.flash_color)
        self.flash_animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.init_ui()

    def init_ui(self):    
        """Initialize the user interface."""
        self.setWindowTitle("Big Clock")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.titleBar = CustomTitleBar(self)
        
        self.set_background_color(self.config.background_color)        
        self.load_font()
        
        # Initialize UI elements
        self.date_label = self.create_date_label()
        self.time_label = self.create_time_label()

        self.setup_layouts()
        self.update_time()

    def create_date_label(self):
        """Create and return the date label."""
        label = QLabel(self)
        
        label.setStyleSheet(f"color: {self.config.clock_text_color.name()}; font-family: {self.font.family()}; font-size: 42px;")
        label.setAlignment(Qt.AlignCenter)
        return label

    def create_time_label(self):
        """Create and return the time label."""
        label = QLabel(self)
        if self.config.toggle_24h: # the "am" and "pm", if used, cause the text to be too large and get clipped on edges. 
            label.setStyleSheet(f"color: {self.config.clock_text_color.name()}; font-family: {self.font.family()}; font-size: 480px;")
        else:
            label.setStyleSheet(f"color: {self.config.clock_text_color.name()}; font-family: {self.font.family()}; font-size: 390px;")
        label.setAlignment(Qt.AlignCenter)
        return label

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
                font_id = font_db.addApplicationFont(str(FONT_PATH))
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
        # Main clock layout
        clock_layout = QVBoxLayout()
        clock_layout.setContentsMargins(0, 0, 0, 0)
        clock_layout.setSpacing(0)

        # Add the CustomTitleBar at the top
        clock_layout.addWidget(self.titleBar)

        # Add the date label
        clock_layout.addWidget(self.date_label, alignment=Qt.AlignCenter)

        # Add the time label
        clock_layout.addWidget(self.time_label, alignment=Qt.AlignCenter)

        # Add spacers to center the clock
        clock_layout.addStretch()

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addLayout(clock_layout)


    def determine_flash_length(self):
        # round down to the nearest whole number
        int_flash_dur = int(self.config.flash_duration)
        numFlashes = int_flash_dur*2
        flashtime = (self.config.flash_duration * 1000)/numFlashes
        self.numFlashes = max(int(numFlashes), 1)
        self.flashDur = max(int(flashtime), 1)
     
    def update_time(self):
        """Update the displayed time and date."""
        now = datetime.now()
        if self.config.toggle_24h:
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
        self.determine_flash_length()  # Recalculate durations based on current settings
        
        logging.info(f"Starting flash with {self.numFlashes} flashes of {self.flashDur} ms each.")
        self.flash_animation.setDuration(self.flashDur)
        self.flash_animation.setLoopCount(self.numFlashes)
        self.flash_animation.setStartValue(self.config.background_color)
        self.flash_animation.setEndValue(self.config.flash_color)
        self.flash_animation.start()
        
        # Total duration of the flashing sequence
        total_flash_duration_ms = int(self.config.flash_duration * 1000)
        self.flash_timer.start(total_flash_duration_ms)
        
    def stop_flash(self):
        """Stop the flashing animation and reset the background."""
        self.flash_animation.stop()
        self.flash_timer.stop()
        self.flash_color = self.config.background_color  # Use the property setter

    @pyqtProperty(QColor, notify=flashColorChanged)
    def flash_color(self):
        return self._flash_color

    @flash_color.setter
    def flash_color(self, color):
        if self._flash_color != color:
            self._flash_color = color
            self.flashColorChanged.emit()  # Emit the notify signal
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
            self.config.toggle_24h = settings_dialog.toggle_24h.isChecked()
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
         
    def open_settings_dialog(self):
        """Display the settings dialog and update the config if settings are modified."""
        logging.info("open_settings_dialog called")  # Added print statement
        # Display the settings dialog
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec_() == QDialog.Accepted:
            # Update the config with new settings
            self.config.flash_duration = settings_dialog.flash_duration_input.value()
            self.config.toggle_24h = settings_dialog.toggle_24h_clock.isChecked()
            self.config.flash_regularity = int(settings_dialog.flash_regularity_combo.currentText())
            self.config.audio_path = settings_dialog.audio_input.text()
            self.config.volume_level = settings_dialog.volume_slider.value() / 100.0
            self.config.background_color = settings_dialog.config.background_color
            self.config.flash_color = settings_dialog.config.flash_color
            self.config.clock_text_color = settings_dialog.config.clock_text_color
            self.config.button_color = settings_dialog.config.button_color

            # Apply updated settings dynamically
            self.set_background_color(self.config.background_color)
            self.date_label.setStyleSheet(f"color: {self.config.clock_text_color.name()}; font-family: {self.font.family()}; font-size: 42px;")
            self.time_label.setStyleSheet(f"color: {self.config.clock_text_color.name()}; font-family: {self.font.family()}; font-size: 480px;")

            # Update volume in wiggle flash
            self.main_window.update_audio_volume()

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
        self.myfonts = { "Bondoni 72", "Charlkboard", "Futura", "Herculanum", "Luminari", "Silom" }

        # Start the timer for animation
        self.timer.start(60, self)  # This registers a timer event with the Qt event loop

        # Set up audio player
        self.player = QMediaPlayer()
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.config.audio_path)))
        self.player.setVolume(int(self.config.volume_level * 100))  # Convert to integer percentage
   
    def set_hour(self, hour):
        """Set the text to display the current hour and play audio."""
        if self.config.toggle_24h:
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
        font = QFont()
        font.setFamily(random.choice(self.myfonts))
        font.setPointSize(180)
        font.setBold(False)
        font.setItalic(False)
        
        painter = QPainter()
        painter.setFont(font)
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
            
class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QPalette.ColorRole.Highlight)
        
        self.old_pos = None
        
        title_bar_layout = QHBoxLayout(self)
        title_bar_layout.setContentsMargins(1, 1, 1, 1)
        title_bar_layout.setSpacing(2)
        
        self.title = QLabel(f"{self.__class__.__name__}", self)
        self.title.setStyleSheet(
            """font-weight: bold;
               border: 2px solid black;
               border-radius: 12px;
               margin: 2px;
            """
        )
        self.title.setAlignment(Qt.AlignCenter)
        title = parent.windowTitle()
        if title:
            self.title.setText(title)
        title_bar_layout.addWidget(self.title)

        # Spacer to push buttons to the right
        title_bar_layout.addStretch()

        # Settings button
        self.settings_button = QToolButton(self)
        settings_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        self.settings_button.setIcon(settings_icon)
        self.settings_button.clicked.connect(parent.open_settings_dialog)

        # Close button
        self.close_button = QToolButton(self)
        close_icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarCloseButton
        )
        self.close_button.setIcon(close_icon)
        self.close_button.clicked.connect(QApplication.quit)
        
        buttons = [
            self.settings_button,
            self.close_button,
        ]
        for button in buttons:
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setFixedSize(QSize(28, 28))
            button.setStyleSheet(
                """QToolButton { border: 2px solid white;
                                 border-radius: 12px;
                                }
                """
            )
            title_bar_layout.addWidget(button)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.window().move(self.window().pos() + delta)
            self.old_pos = event.globalPos()
            event.accept()
            
            
# --------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)  # Create the application instance

    # Create the settings dialog and show it
    settings_dialog = SettingsDialog()
    if settings_dialog.exec_() == QDialog.Accepted:
        # User accepted the settings, proceed to show the main window
        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec_())
    else:
        # User canceled the settings, exit the application
        sys.exit()