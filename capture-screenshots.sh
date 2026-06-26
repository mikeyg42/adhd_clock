#!/usr/bin/env bash
# Capture README and portfolio screenshots for Big Clock.
#
# CHANGELOG:
# 2026-06-26: Created to make PyQt screenshot capture repeatable from one command.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-${ROOT_DIR}/venv/bin/python}"
OUT_DIR="${OUT_DIR:-${ROOT_DIR}/screenshots}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Python interpreter not found or not executable: ${PYTHON_BIN}" >&2
  echo "Set PYTHON_BIN=/path/to/python or create the project venv first." >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"
cd "${ROOT_DIR}"

export OUT_DIR
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"

"${PYTHON_BIN}" - <<'PY'
import os
import sys
from pathlib import Path

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication

from bigclock import AppConfig, MainWindow, SettingsDialog


def process_events(app, count=4):
    for _ in range(count):
        app.processEvents()


def prepare_resizable(widget, width, height):
    widget.setMinimumSize(0, 0)
    widget.setMaximumSize(16777215, 16777215)
    widget.resize(width, height)


out_dir = Path(os.environ["OUT_DIR"])
app = QApplication.instance() or QApplication(sys.argv)

config = AppConfig()
config.toggle_24h = True
config.flash_duration = 5
config.flash_regularity = 15

clock = MainWindow()
prepare_resizable(clock, 1280, 320)
clock.show()
process_events(app)
clock.clock_app.adjust_font_sizes()
process_events(app)
clock.grab().save(str(out_dir / "bigclock-main.png"))

clock.clock_app.flash_color = QColor(255, 40, 40)
process_events(app)
clock.grab().save(str(out_dir / "bigclock-flash.png"))

settings = SettingsDialog()
prepare_resizable(settings, 900, 840)
settings.show()
process_events(app)
settings.grab().save(str(out_dir / "bigclock-settings.png"))

clock.clock_app.timer.stop()
clock.clock_app.flash_timer.stop()
clock.wiggle_flash.timer.stop()
settings.done(0)
clock.close()
app.quit()
PY

echo "Screenshots written to ${OUT_DIR}"
