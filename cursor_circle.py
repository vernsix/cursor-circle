#!/usr/bin/env python3
"""
Cursor Circle Highlight for Ubuntu/Linux

A customizable cursor highlight overlay with circle, crosshair, and animation effects

Author: Vern Six (https://github.com/vernsix)
Version: 1.0.0
Created: 2025-01-17
License: MIT
"""

import gi
import signal
import sys
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkX11
import cairo

# ============== CONFIGURATION SECTION ==============
# Modify these values to customize your cursor circle

# SIZE SETTINGS
CIRCLE_SIZE = 100  # Circle diameter in pixels (60=tiny, 100=normal, 200=huge, 300=massive)

# COLOR SETTINGS (RGBA: Red, Green, Blue, Alpha/Opacity)
# Values range from 0.0 to 1.0
# Color presets (uncomment one to use):

GLOW_COLOR = (1, 1, 0, 0.2); CIRCLE_COLOR = (1, 1, 0, 0.5); CENTER_DOT_COLOR = (1, 1, 1, 0.8) # Yellow
# GLOW_COLOR = (1, 0, 0, 0.2); CIRCLE_COLOR = (1, 0, 0, 0.5); CENTER_DOT_COLOR = (1, 0.5, 0.5, 0.8)  # Red
# GLOW_COLOR = (0, 1, 0, 0.2); CIRCLE_COLOR = (0, 1, 0, 0.5); CENTER_DOT_COLOR = (0.8, 1, 0.8, 0.8)  # Green
# GLOW_COLOR = (0, 0, 1, 0.2); CIRCLE_COLOR = (0, 0, 1, 0.5); CENTER_DOT_COLOR = (0.7, 0.9, 1, 0.8)  # Blue
# GLOW_COLOR = (1, 0, 1, 0.2); CIRCLE_COLOR = (1, 0, 1, 0.5); CENTER_DOT_COLOR = (0.9, 0.7, 1, 0.8)  # Purple
# GLOW_COLOR = (0, 1, 1, 0.2); CIRCLE_COLOR = (0, 1, 1, 0.5); CENTER_DOT_COLOR = (0.8, 1, 1, 0.8)  # Cyan
# GLOW_COLOR = (1, 1, 1, 0.1); CIRCLE_COLOR = (1, 1, 1, 0.3); CENTER_DOT_COLOR = (1, 1, 1, 0.6)  # White
# GLOW_COLOR = (1, 0.5, 0, 0.2); CIRCLE_COLOR = (1, 0.5, 0, 0.5); CENTER_DOT_COLOR = (1, 0.8, 0.5, 0.8) # Orange
# GLOW_COLOR = (1, 0, 0.5, 0.2); CIRCLE_COLOR = (1, 0, 0.5, 0.5); CENTER_DOT_COLOR = (1, 0.8, 0.9, 0.8) # Pink

# STYLE SETTINGS
LINE_WIDTH = 3          # Thickness of the circle line (1=thin, 3=normal, 5=thick)
SHOW_GLOW = True        # Enable/disable the outer glow effect
SHOW_CENTER_DOT = True  # Enable/disable the center dot
CENTER_DOT_SIZE = 3     # Size of center dot in pixels

SHOW_CROSSHAIR = False  # Enable/disable crosshair inside circle
CROSSHAIR_COLOR = (1, 1, 1, 0.3)  # Crosshair color: White with 30% opacity
CROSSHAIR_WIDTH = 1     # Crosshair line thickness

# EFFECTS SETTINGS
SHOW_MULTIPLE_RINGS = False  # Enable/disable multiple concentric circles (radar effect)
RING_COUNT = 3               # Number of rings if enabled
RING_SPACING = 15            # Pixels between rings

SHOW_PULSE_EFFECT = False  # Enable/disable pulsing animation
PULSE_SPEED = 0.5          # Speed of pulse (0.1=slow, 0.5=normal, 1.0=fast)
PULSE_RANGE = 5            # Maximum pixels to expand/contract

# Crosshair style presets (uncomment to use):
# SHOW_CROSSHAIR = True; CROSSHAIR_COLOR = (1, 0, 0, 0.7)  # Red crosshair
# SHOW_CROSSHAIR = True; CROSSHAIR_COLOR = (0, 1, 0, 0.7)  # Green crosshair
# SHOW_CROSSHAIR = True; CROSSHAIR_COLOR = (1, 1, 0, 0.5)  # Yellow crosshair
# SHOW_CROSSHAIR = True; CROSSHAIR_COLOR = (0, 1, 1, 0.6)  # Cyan crosshair

# Effects presets (uncomment to use):
# SHOW_MULTIPLE_RINGS = True; RING_COUNT = 3; RING_SPACING = 20  # Simple radar
# SHOW_MULTIPLE_RINGS = True; RING_COUNT = 5; RING_SPACING = 10  # Dense radar
# SHOW_PULSE_EFFECT = True; PULSE_SPEED = 0.2; PULSE_RANGE = 10  # Slow breathing
# SHOW_PULSE_EFFECT = True; PULSE_SPEED = 1.0; PULSE_RANGE = 3   # Fast subtle pulse

# PERFORMANCE SETTINGS
UPDATE_INTERVAL = 10    # Milliseconds between position updates (10=smooth, 20=balanced, 30=power-saving)

# ============== END CONFIGURATION ==================

class CursorCircle(Gtk.Window):
    def __init__(self):
        super().__init__()

        # Calculate dimensions based on configuration
        self.window_size = CIRCLE_SIZE + 20  # Add padding
        self.center = self.window_size // 2
        self.outer_radius = self.center - 5
        self.main_radius = self.center - 10

        # Scale line width for larger circles
        self.line_width = LINE_WIDTH if CIRCLE_SIZE < 150 else max(LINE_WIDTH, CIRCLE_SIZE // 50)

        # Initialize pulse effect variables
        if SHOW_PULSE_EFFECT:
            self.pulse_size = self.main_radius
            self.pulse_direction = 1

        # Window settings
        self.set_title("Cursor Circle")
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.set_app_paintable(True)
        self.set_size_request(self.window_size, self.window_size)

        # Make transparent
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        # Make click-through
        self.set_accept_focus(False)
        self.set_can_focus(False)
        self.input_shape_combine_region(cairo.Region())

        # Drawing
        self.connect('draw', self.on_draw)

        # Mouse tracking
        self.device = None
        self.setup_mouse_tracking()

        # Update position
        GLib.timeout_add(UPDATE_INTERVAL, self.update_position)

    def on_draw(self, widget, cr):
        # Clear background
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()

        # Calculate current radius (for pulse effect)
        current_radius = self.main_radius
        if SHOW_PULSE_EFFECT:
            self.pulse_size += self.pulse_direction * PULSE_SPEED
            if self.pulse_size > self.main_radius + PULSE_RANGE or self.pulse_size < self.main_radius - PULSE_RANGE:
                self.pulse_direction *= -1
            current_radius = self.pulse_size
            # Trigger redraw for animation
            self.queue_draw()

        # Draw outer glow if enabled
        if SHOW_GLOW:
            cr.set_source_rgba(*GLOW_COLOR)
            glow_radius = self.outer_radius + (current_radius - self.main_radius) if SHOW_PULSE_EFFECT else self.outer_radius
            cr.arc(self.center, self.center, glow_radius, 0, 2 * 3.14159)
            cr.fill()

        # Draw multiple rings or single circle
        if SHOW_MULTIPLE_RINGS:
            # Draw multiple concentric rings (radar effect)
            for i in range(RING_COUNT):
                radius = current_radius - (i * RING_SPACING)
                if radius > 10:
                    # Fade opacity for inner rings
                    opacity = max(0.1, CIRCLE_COLOR[3] - (i * 0.15))
                    cr.set_source_rgba(CIRCLE_COLOR[0], CIRCLE_COLOR[1], CIRCLE_COLOR[2], opacity)
                    cr.set_line_width(max(1, self.line_width - i))
                    cr.arc(self.center, self.center, radius, 0, 2 * 3.14159)
                    cr.stroke()
        else:
            # Draw single main circle
            cr.set_source_rgba(*CIRCLE_COLOR)
            cr.set_line_width(self.line_width)
            cr.arc(self.center, self.center, current_radius, 0, 2 * 3.14159)
            cr.stroke()

        # Draw crosshair if enabled (from circle edge to edge)
        if SHOW_CROSSHAIR:
            cr.set_source_rgba(*CROSSHAIR_COLOR)
            cr.set_line_width(CROSSHAIR_WIDTH)
            # Use current_radius for pulsing crosshair
            crosshair_radius = current_radius if SHOW_PULSE_EFFECT else self.main_radius
            # Horizontal line (edge to edge of main circle)
            cr.move_to(self.center - crosshair_radius, self.center)
            cr.line_to(self.center + crosshair_radius, self.center)
            cr.stroke()
            # Vertical line (edge to edge of main circle)
            cr.move_to(self.center, self.center - crosshair_radius)
            cr.line_to(self.center, self.center + crosshair_radius)
            cr.stroke()

        # Draw center dot if enabled
        if SHOW_CENTER_DOT:
            cr.set_source_rgba(*CENTER_DOT_COLOR)
            cr.arc(self.center, self.center, CENTER_DOT_SIZE, 0, 2 * 3.14159)
            cr.fill()

        return False

    def setup_mouse_tracking(self):
        display = Gdk.Display.get_default()
        seat = display.get_default_seat()
        self.device = seat.get_pointer()

    def update_position(self):
        if self.device:
            screen, x, y = self.device.get_position()
            self.move(x - self.center, y - self.center)
        return True

def signal_handler(sig, frame):
    """Clean exit on Ctrl+C"""
    print("\nCursor circle stopped.")
    Gtk.main_quit()
    sys.exit(0)

def main():
    # Set up signal handler for clean exit
    signal.signal(signal.SIGINT, signal_handler)

    win = CursorCircle()
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
