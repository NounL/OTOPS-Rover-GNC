# Ares' Amazing Cameras (OTOPS 2026)
# Olly Love
# 2025/2026 Interface for controlling the OTOPS rover cameras at CIRC
# Helpful Source: https://www.youtube.com/watch?v=FszqUfibD3w
# Note: Server must be running for cameras to be able to connect to it
# Make sure the IP addresses match that of the server

# Installs: 
# Make sure you have gstreamer installed through there webpage instructions
# sudo apt install libgtk-3-dev gir1.2-gtk-3.0 python3-gi python3-gi-cairo
# sudo apt install gstreamer1.0-gtk3

# If face issues on groundstation, run like this:
# GDK_BACKEND=x11 python3 gui_v2.py

# How to run stream - will later be just ./rtspstream
# gcc latest-rtspstream.c $(pkg-config --cflags --libs gstreamer-rtsp-server-1.0)
# ./a.out

# Scan for camera specs: 
# v4l2-ctl --list-devices
# v4l2-ctl --list-formats-ext --device /dev/video0

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from cam_grid_v2 import BaseCamGrid, LargeCamGrid

# gi.require_version("Gst", "1.0")
# from gi.repository import Gst

class MainWindow(Gtk.Window):
    def __init__(self):
        # Super classes constructor
        Gtk.Window.__init__(self, title="Ares' Amazing Cameras (OTOPS 2026)")
        # Size to perfectly fit groundstation
        self.set_default_size(1850,1000)
        # Dark gray background
        self.override_background_color(
            Gtk.StateFlags.NORMAL,
            Gdk.RGBA(0.5, 0.5, 0.5, 1)
        )

        # Main root container which holds everything
        root_grid = Gtk.Grid()
        self.add(root_grid)

        # Allign in the center and padding between items
        root_grid.set_halign(Gtk.Align.CENTER)
        root_grid.set_valign(Gtk.Align.CENTER)
        root_grid.set_row_spacing(2)
        root_grid.set_column_spacing(2)

        # still tcp/udp issue?
        # 3 innomakers - mjpeg
        # front_line = "rtspsrc location=rtsp://localhost:8554/front protocols=tcp latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink"
        #front_line = "rtspsrc location=rtsp://192.168.0.2:8554/front latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink"
        
        # This ip for on rover nanobeam/prism network
        #self.front_line = "rtspsrc location=rtsp://192.168.1.31:8554/front latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! gtksink name=sink"
        self.front_line = "rtspsrc location=rtsp://localhost:8554/front latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! gtksink name=sink"
        self.front_line_small = "rtspsrc location=rtsp://localhost:8554/front latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! videoscale ! video/x-raw, width=525, height=295 ! gtksink name=sink"
        self.left_line_small = "rtspsrc location=rtsp://localhost:8554/left latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! videoscale ! video/x-raw, width=525, height=295 ! gtksink name=sink2"
        # Larger streams that haven't been scaled down for showing in large main window
        self.left_line_large = "rtspsrc location=rtsp://localhost:8554/left latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink2"
        self.right_line_small = "rtspsrc location=rtsp://localhost:8554/right latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! videoscale ! video/x-raw, width=525, height=295 ! gtksink name=sink3"
        self.right_line_large = "rtspsrc location=rtsp://localhost:8554/right latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink3"
        self.back_line_small = "rtspsrc location=rtsp://localhost:8554/back latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! videoscale ! video/x-raw, width=525, height=295 ! gtksink name=sink4"
        self.back_line_large = "rtspsrc location=rtsp://localhost:8554/back latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink4"

        self.front_cam_sink = "sink"
        self.left_cam_sink = "sink2"
        self.right_cam_sink = "sink3"
        self.back_cam_sink = "sink4"

        self.front_cam_grid = LargeCamGrid("Front", self.front_line, self.front_cam_sink, self.swap)
        self.left_cam_grid = BaseCamGrid("Left", self.left_line_small, self.left_cam_sink)
        self.right_cam_grid = BaseCamGrid("Right", self.right_line_small, self.right_cam_sink)
        self.back_cam_grid = BaseCamGrid("Back", self.back_line_small, self.back_cam_sink)
        
        # Col, Row, Width, Height
        root_grid.attach(self.front_cam_grid,0,0,1,3)
        root_grid.attach(self.left_cam_grid,1,0,1,1)
        root_grid.attach(self.right_cam_grid,1,1,1,1)
        root_grid.attach(self.back_cam_grid,1,2,1,1)

    # cleaner swap - get functionality below perfect first
    def swap(self, value):
        pass

    # Show left, right, back in main and swap + front cam reset handled
    # need to optimize the code
    # Then consider quality of stream issue - do we need a way to request low quality?
    # That issue when all 4 cameras on need to close app and restart, is there better way?
    def swap(self, value):
        # need to also handle when they are both off, they should only swap when they're on - fix later
        if value == "Left" and self.front_cam_grid.left_shown == False:
            self.front_cam_grid.stream_off()
            self.left_cam_grid.stream_off()

            # If these 2 are on reset them to not lose track of what cam is where
            # they will move to different streams on the gui otherwise confusing everyone
            # want to call a reset function of some sort? 
            if self.right_cam_grid.pipeline:
                self.right_cam_grid.stream_off()
                self.right_cam_grid.pipeline_str = self.right_line_small
                self.right_cam_grid.sink = self.right_cam_sink
                self.right_cam_grid.stream_on()
                self.right_cam_grid.cam_lbl.set_markup("<big>Right</big>")
            if self.back_cam_grid.pipeline:
                self.back_cam_grid.stream_off()
                self.back_cam_grid.pipeline_str = self.back_line_small
                self.back_cam_grid.sink = self.back_cam_sink
                self.back_cam_grid.stream_on()
                self.back_cam_grid.cam_lbl.set_markup("<big>Back</big>")

            # Show left stream in main grid - setter method?
            self.front_cam_grid.pipeline_str = self.left_line_large
            self.front_cam_grid.sink = self.left_cam_sink
            self.front_cam_grid.stream_on()
            self.front_cam_grid.cam_lbl.set_markup("<big>Left</big>")

            # Show front stream in left grid
            self.left_cam_grid.pipeline_str = self.front_line_small
            self.left_cam_grid.sink = self.front_cam_sink
            self.left_cam_grid.stream_on()
            self.left_cam_grid.cam_lbl.set_markup("<big>Front</big>")
        elif value == "Right" and self.front_cam_grid.right_shown == False:
            self.front_cam_grid.stream_off()
            self.right_cam_grid.stream_off()

            if self.left_cam_grid.pipeline:
                self.left_cam_grid.stream_off()
                self.left_cam_grid.pipeline_str = self.left_line_small
                self.left_cam_grid.sink = self.left_cam_sink
                self.left_cam_grid.stream_on()
                self.left_cam_grid.cam_lbl.set_markup("<big>Left</big>")
            if self.back_cam_grid.pipeline:
                self.back_cam_grid.stream_off()
                self.back_cam_grid.pipeline_str = self.back_line_small
                self.back_cam_grid.sink = self.back_cam_sink
                self.back_cam_grid.stream_on()
                self.back_cam_grid.cam_lbl.set_markup("<big>Back</big>")

            # Show right stream in main grid - setter method?
            self.front_cam_grid.pipeline_str = self.right_line_large
            self.front_cam_grid.sink = self.right_cam_sink
            self.front_cam_grid.stream_on()
            self.front_cam_grid.cam_lbl.set_markup("<big>Right</big>")

            # Show front stream in right grid
            self.right_cam_grid.pipeline_str = self.front_line_small
            self.right_cam_grid.sink = self.front_cam_sink
            self.right_cam_grid.stream_on()
            self.right_cam_grid.cam_lbl.set_markup("<big>Front</big>")
        elif value == "Back" and self.front_cam_grid.back_shown == False:
            self.front_cam_grid.stream_off()
            self.back_cam_grid.stream_off()

            if self.left_cam_grid.pipeline:
                self.left_cam_grid.stream_off()
                self.left_cam_grid.pipeline_str = self.left_line_small
                self.left_cam_grid.sink = self.left_cam_sink
                self.left_cam_grid.stream_on()
                self.left_cam_grid.cam_lbl.set_markup("<big>Left</big>")
            if self.right_cam_grid.pipeline:
                self.right_cam_grid.stream_off()
                self.right_cam_grid.pipeline_str = self.back_line_small
                self.right_cam_grid.sink = self.back_cam_sink
                self.right_cam_grid.stream_on()
                self.right_cam_grid.cam_lbl.set_markup("<big>Right</big>")

            # Show back stream in main grid - setter method?
            self.front_cam_grid.pipeline_str = self.back_line_large
            self.front_cam_grid.sink = self.back_cam_sink
            self.front_cam_grid.stream_on()
            self.front_cam_grid.cam_lbl.set_markup("<big>Back</big>")

            # Show front stream in back grid
            self.back_cam_grid.pipeline_str = self.front_line_small
            self.back_cam_grid.sink = self.front_cam_sink
            self.back_cam_grid.stream_on()
            self.back_cam_grid.cam_lbl.set_markup("<big>Front</big>")
        # Resetting front stream 
        elif value == "Front" and self.front_cam_grid.front_shown == False:
            # When front being reset, want everything to also be reset
            # As either window could be showing front, they need to go back to og view
            if self.left_cam_grid.pipeline:
                self.left_cam_grid.stream_off()
                self.left_cam_grid.pipeline_str = self.left_line_small
                self.left_cam_grid.sink = self.left_cam_sink
                self.left_cam_grid.stream_on()
                self.left_cam_grid.cam_lbl.set_markup("<big>Left</big>")
            if self.right_cam_grid.pipeline:
                self.right_cam_grid.stream_off()
                self.right_cam_grid.pipeline_str = self.right_line_small
                self.right_cam_grid.sink = self.right_cam_sink
                self.right_cam_grid.stream_on()
                self.right_cam_grid.cam_lbl.set_markup("<big>Right</big>")
            if self.back_cam_grid.pipeline:
                self.back_cam_grid.stream_off()
                self.back_cam_grid.pipeline_str = self.back_line_small
                self.back_cam_grid.sink = self.back_cam_sink
                self.back_cam_grid.stream_on()
                self.back_cam_grid.cam_lbl.set_markup("<big>Back</big>")

            self.front_cam_grid.stream_off()
            self.front_cam_grid.pipeline_str = self.front_line
            self.front_cam_grid.sink = self.front_cam_sink
            self.front_cam_grid.stream_on()
            self.front_cam_grid.cam_lbl.set_markup("<big>Front</big>")

        else:
            print(f"ERROR: Already showing {value} stream")

window = MainWindow()
window.connect("delete-event", Gtk.main_quit)
window.show_all()
Gtk.main()