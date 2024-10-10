import sys
import logging
import os
import random
import pathlib
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QDesktopWidget,
    QVBoxLayout, QHBoxLayout, QSizePolicy, QStackedLayout, QLayout,
    QSlider, QGroupBox, QLineEdit, QDialog, QDialogButtonBox, QFileDialog, 
    QColorDialog,QDoubleSpinBox, QStyle, QToolButton,QComboBox, QMessageBox
)
from PyQt5.QtCore import (
    QTimer, Qt, QBasicTimer, QPropertyAnimation, QEasingCurve, QEvent,
    pyqtProperty, QUrl, QCoreApplication, QSize, QPoint, pyqtSignal
)
from PyQt5.QtGui import (
    QFont, QFontDatabase, QPainter, QColor, QPalette, QFontMetrics
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QSoundEffect
from animated_toggle import AnimatedToggle


# ----------------------------------------------
QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

# Configuration Constants - uncustomizable
BUTTON_TEXT_COLOR = "white"
WIGGLE_BACKGROUND_COLOR = QColor(244, 246, 243)  # White

# buttons in the settings dialog
BUTTON_COLORS = [QColor(100, 255, 55), QColor(255, 50, 50)] # first is ACCEPT = GREEN , second is CANCEL = RED
BUTTON_HOVER_COLORS = [QColor(160, 20, 160), QColor(0, 175, 150)]

# Global Defaults for Colors
DEFAULT_BACKGROUND_COLOR = QColor(45, 55, 55)  # Black
DEFAULT_FLASH_COLOR = QColor(255, 40, 40)      # Red
DEFAULT_CLOCK_TEXT_COLOR = QColor(245, 245, 243)  # White
DEFAULT_TOOLBAR_COLOR = QColor(100, 180, 230) #light blue

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

WINDOW_AMT_OCCUPIED=0.15 # the window will occupy this amount of the screen height(value between 0 and 1) and span the screen width

DEFAULT_RELATIVE_SIZE_TIME_VS_DATE = 12 # this means the time will be 9x the size of the date

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
        self.flash_duration = 10
        self.flash_regularity = 15
        self.audio_path = str(DEFAULT_AUDIO_PATH)
        self.volume_level = 0.3
        self.background_color =DEFAULT_BACKGROUND_COLOR
        self.flash_color = DEFAULT_FLASH_COLOR
        self.clock_text_color = DEFAULT_CLOCK_TEXT_COLOR
        self.toolbar_color = DEFAULT_TOOLBAR_COLOR
        self.relativeFontSize = DEFAULT_RELATIVE_SIZE_TIME_VS_DATE

    def update_setting(self, key, value):
        """Update a setting."""
        setattr(self, key, value)
# --------------------------------------------------

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ADHD Clock Settings")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Access the singleton instance    
        self.config = AppConfig()

        # Set the dialog on the primary screen (Screen 0)
        self.move_to_primary_screen()

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

        # Toolbar Color
        self.create_color_picker(color_layout, "Toolbar Color", self.config.toolbar_color, "toolbar_color")

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
        self.flash_regularity_combo.clear()  # Clear existing items
        self.flash_regularity_combo.addItems([str(d) for d in divisors]) 

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
        self.set_color_button(self.color_buttons['toolbar_color'], DEFAULT_TOOLBAR_COLOR)


    def update_volume_label(self, value):
        """Update the volume label to reflect the slider's current value."""
        self.volume_label.setText(f"{value}%")    
    
    def init_sound_effect(self):
        """Dynamically load all .wav files from the resources directory for volume slider feedback."""
        
        # Path to the resources directory
        resources_dir = pathlib.Path(resource_path('resources'))
        
        # List of beep sound files (only .wav files)
        self.beep_paths = list(resources_dir.glob('*.wav'))

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

            else:
                logging.error(f"Beep sound file not found: {path}")

        # Initialize a timer to debounce slider movements
        self.beep_timer = QTimer()
        self.beep_timer.setSingleShot(True)
        self.beep_timer.timeout.connect(self.play_beep)
        
        # Timer to reset the sound effect after 15 seconds
        self.reset_sound_timer = QTimer()
        self.reset_sound_timer.setSingleShot(True)
        self.reset_sound_timer.timeout.connect(self.reset_beep_sound)
        
        # Track the last played sound
        self.current_beep_sound = None

    def play_beep(self):
        """Play the currently active beep sound."""
        if self.current_beep_sound:
            self.current_beep_sound.setVolume(self.current_volume)
            self.current_beep_sound.stop()  # Stop any currently playing beep to prevent overlap
            self.current_beep_sound.play()

    def play_random_beep(self):
        """Select and play a new random beep sound, locking it for 15 seconds."""
        
        # If no current beep sound or the reset timer is not running, choose a new sound
        if not self.current_beep_sound or not self.reset_sound_timer.isActive():
            available_sounds = [sound for sound in self.sound_effects if sound != self.current_beep_sound]
            if available_sounds:
                self.current_beep_sound = random.choice(available_sounds)
                # logging.info(f"Selected new beep sound.")
            else:
                logging.warning("No alternative beep sounds available.")
            
            # Start the 15-second timer to allow new random selection after this period
            self.reset_sound_timer.start(15000)  # 15 seconds
        
        # Play the current beep sound
        self.play_beep()

    def reset_beep_sound(self):
        """Reset the beep sound after 15 seconds, allowing a new random one to be selected."""
        self.current_beep_sound = None

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
        # self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # set size policies and adjust accordingly
        # self.clock_app.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.wiggle_flash.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.adjustSize()
        
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
        # logging.info(f"Detected {screen_count} screens.")
        if screen_count > 1:
            extended_screen = desktop.screenGeometry(1)
            self.setGeometry(extended_screen)

        elif screen_count == 1:
            # Only the main monitor is available
            main_screen = desktop.screenGeometry(0)
            window_height = int(main_screen.height() * WINDOW_AMT_OCCUPIED)
            self.setGeometry(
                0,
                main_screen.height() - window_height,
                main_screen.width(),
                window_height
            )
        else:
            logging.error("No screens detected. Exiting application.")
        
        self.setFixedSize(self.size())
            
    def update_audio_volume(self):
        self.wiggle_flash.player.setVolume(int(self.config.volume_level * 100))
            

    def allow_resize_briefly(self):
        """Allow the user to resize the window for a short period."""
        # logging.info("Temporarily allowing resizing of the window.")
        screen = QApplication.primaryScreen()
        desk_rect = screen.availableGeometry()
        # Remove fixed size constraints
        self.setMinimumSize(QSize(400, 200))  # Set a reasonable minimum size
        self.setMaximumSize(desk_rect.size()) 
        QTimer.singleShot(10000, self.reset_fixed_size)  # Re-lock after 10 seconds

    def reset_fixed_size(self):
        """Re-lock the window size to fixed dimensions."""
        # logging.info("Re-locking the window size to fixed.")
        current_size = self.size()
        self.setMinimumSize(current_size)
        self.setMaximumSize(current_size)

class BigClockApp(QWidget):
    """A big clock application with a customizable display."""
    
    flashColorChanged = pyqtSignal()
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.config = AppConfig()
        
        self.title_bar = CustomTitleBar(self)
        self.title_bar.set_toolbar_color(self.config.toolbar_color)
        self.installEventFilter(self)
        
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
        self.determine_flash_length() # saves values as self.numFlashes and self.flashDur
        
        # Configure flash animation
        self.flash_animation = QPropertyAnimation(self, b"flash_color")
        self.flash_animation.setDuration(self.flashDur)  # 500ms ish
        self.flash_animation.setLoopCount(self.numFlashes)  # Even number of flashes
        self.flash_animation.setStartValue(self.config.background_color)
        self.flash_animation.setEndValue(self.config.flash_color)
        self.flash_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # flag to prevent recursive font size adjustment
        self.is_adjusting_font = False 
        self.font_adjust_start_time = None
        
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.adjust_font_sizes)
        
        self.init_ui()
        

    def init_ui(self):    
        """Initialize the user interface."""
        self.setWindowTitle("ADHD Clock")
        
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
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"color: {self.config.clock_text_color.name()};")
        label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        # label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        # label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        return label

    def create_time_label(self):
        """Create and return the time label."""
        label = QLabel(self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"color: {self.config.clock_text_color.name()};")
        # label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        # label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        return label

    def eventFilter(self, obj, event):
        """Filter resize and mouse events."""
        """Filter resize and mouse events."""
        if event.type() == QEvent.Resize:
            if not self.is_adjusting_font:
                self.resize_timer.start(100)  # Delay adjustment for smooth resizing
            # Do not return True; allow the event to propagate
            return False  # Indicate that the event has not been fully handled
        return super().eventFilter(obj, event)
        
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
            logging.warning(f"Failed to load specified font. Defaulting to Courier: {e}")
            self.font = QFont()
            self.font.setStyleHint(QFont.TypeWriter)
        
        self.font_family = self.font.family()
            
    def setup_layouts(self):
        """Set up the layout for the widget with resizable dimensions."""
        # Main clock layout
        clock_layout = QVBoxLayout()
        clock_layout.setContentsMargins(0, 0, 0, 0)
        clock_layout.setSpacing(0)

        # Add the CustomTitleBar at the top
        clock_layout.addWidget(self.title_bar)

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
        main_layout.setSizeConstraint(QLayout.SetNoConstraint)
        # main_layout.setSizeConstraint(QLayout.SetFixedSize)
        
        # Apply the layout to the widget
        self.setLayout(main_layout)

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
        
        logging.debug(f"Starting flash with {self.numFlashes} flashes of {self.flashDur} ms each.")
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
            self.config.toolbar_color = settings_dialog.toolbar_color

            # Apply updated settings dynamically
            self.set_background_color(self.config.background_color)
            self.date_label.setStyleSheet(f"color: {self.config.clock_text_color.name()};")
            self.time_label.setStyleSheet(f"color: {self.config.clock_text_color.name()};")
            # Adjust font sizes
            self.adjust_font_sizes()
            
    def open_settings_dialog(self):
        """Display the settings dialog and update the config if settings are modified."""
        # logging.info("open_settings_dialog called")  # Added print statement
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
            self.config.toolbar_color = settings_dialog.config.toolbar_color

            # Apply updated settings dynamically
            self.set_background_color(self.config.background_color)
            self.date_label.setStyleSheet(f"color: {self.config.clock_text_color.name()};")
            self.time_label.setStyleSheet(f"color: {self.config.clock_text_color.name()};")
            
            # Adjust font sizes
            self.adjust_font_sizes()
            
            # Update volume in wiggle flash
            self.main_window.update_audio_volume()
    
    # def resizeEvent(self, event):
    #     super().resizeEvent(event)
    #     if not self.is_adjusting_font and QApplication.mouseButtons() == Qt.LeftButton:
    #             # User is resizing the window
    #         self.resize_timer.start(100)
    #     else:
    #         return
            
    def get_optimal_font_size(self, max_width, max_height):
        """Find the optimal font size for the given text to fit within max_width and max_height."""
        if max_height<1 or max_width<1:
            logging.error(f"Invalid dimensions for font size calculation... {max_width} by {max_height}")
            return 12
        # Set initial font size boundaries
        font_size = 12
        max_font_size = 8000 # arbitrary upper limit
        sample_text = "00:00:00" if self.config.toggle_24h else "00:00:00 AM" 

        while font_size <= max_font_size:
            font = QFont(self.font_family, font_size)
            fm = QFontMetrics(font)
            text_width = fm.horizontalAdvance(sample_text)
                
            text_height = fm.height()
            if text_width <= max_width and text_height <= max_height:
                # Font size fits, try larger size
                font_size += 1
            else:
                # Font size too big, go with one smaller size (which ostensibly worked!) 
                font_size -= 1
                break
        # Return the font with the optimal size
        return font_size
        
    def showEvent(self, event):
        super().showEvent(event)
        if self.width() > 0 and self.height() > 0:
            self.adjust_font_sizes()
        else:
            QTimer.singleShot(0, self.adjust_font_sizes)
            
    def adjust_font_sizes(self):
        """Adjust the font sizes of the time and date labels to fit within the window."""
        available_width = self.width()
        available_height = self.height() - self.title_bar.height()
        if available_width <= 0 or available_height <= 0:
            logging.warning("Available width or height is zero or negative. Skipping font adjustment.")
            return

        self.is_adjusting_font = True

        # Decide the portion of height allocated to time and date labels
        ratio = self.config.relativeFontSize
        if ratio<1:
            ratio= 1/ratio
            
        k = 1/(1+ratio)
        if k<0.5:
            k = 1-k
            
        time_label_height = available_height * k
        date_label_height = available_height * (1-k)

        # Adjust font size for the time and date labels
        self.date_label_font_size = self.get_optimal_font_size(available_width, date_label_height)
        date_font = QFont(self.font_family, self.date_label_font_size)
        self.date_label.setFont(date_font)

        self.time_label_font_size = self.get_optimal_font_size(available_width, time_label_height)
        time_font = QFont(self.font.family(), self.time_label_font_size)
        self.time_label.setFont(time_font)

        self.update()
        self.is_adjusting_font = False 

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
        
        # Create the layout for the title bar
        title_bar_layout = QHBoxLayout(self)
        title_bar_layout.setContentsMargins(1, 1, 1, 1)
        title_bar_layout.setSpacing(2)
        
        # Title label in the center
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
        
        main_window = parent.main_window
        
        # Resize button for temporary resizing
        self.resize_button = QToolButton(self)
        resize_icon = self.style().standardIcon(QStyle.SP_TitleBarMaxButton)
        self.resize_button.setIcon(resize_icon)
        self.resize_button.setToolTip("Resize Window")
        self.resize_button.clicked.connect(main_window.allow_resize_briefly)  # Allow resizing temporarily

        # Settings button
        self.settings_button = QToolButton(self)
        settings_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        self.settings_button.setIcon(settings_icon)
        self.resize_button.setToolTip("Resize Window")
        self.settings_button.clicked.connect(parent.open_settings_dialog)

        # Close button
        self.close_button = QToolButton(self)
        close_icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarCloseButton
        )
        self.close_button.setIcon(close_icon)
        self.close_button.setToolTip("Close")
        self.close_button.clicked.connect(QApplication.quit)
        
        buttons = [self.resize_button, self.settings_button, self.close_button]
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

    def set_toolbar_color(self, color: QColor):
        """
        Update the background color of the custom title bar.
        The color is passed as a QColor object.
        """
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, color)
        self.setPalette(palette)
        
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
        app.quit()