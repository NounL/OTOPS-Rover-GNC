# Olly Love
# Demoing how to get camera feed into our ui

# Source: https://www.youtube.com/watch?v=FszqUfibD3w

# Must run server file first else this won't work

# Installs: 
# sudo apt install libgtk-3-dev gir1.2-gtk-3.0 python3-gi python3-gi-cairo
# sudo apt install gstreamer1.0-gtk3

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from cam_grid_v2 import BaseCamGrid

# gi.require_version("Gst", "1.0")
# from gi.repository import Gst

# Starting off using stack/stack switcher for multi-page layout
# Gonna build how the ui should look, then work around the bugs with the camera feeds
class MainWindow(Gtk.Window):
    def __init__(self):
        # Super classes constructor
        Gtk.Window.__init__(self, title="Ares' Amazing Cameras")
        # May tailor this to the size of main groundstation laptop
        # Width by height
        # Width can easily handle large stream and small stream (need 1280 at most)
        # need 1920 width to double width of large stream for very large view (640*2 then the small stream width)
        # Large placeholder will be 1280 by 720
        # height can handle 3 stacked 360p streams (thats 1080)
        self.set_default_size(1935,1100)
        # Dark gray background
        self.override_background_color(
            Gtk.StateFlags.NORMAL,
            Gdk.RGBA(0.4, 0.4, 0.4, 1)
        )

        # Main root container which holds everything
        root_grid = Gtk.Grid()
        self.add(root_grid)

        # Allign in the center and padding between items
        root_grid.set_halign(Gtk.Align.CENTER)
        root_grid.set_valign(Gtk.Align.CENTER)
        root_grid.set_row_spacing(10)
        root_grid.set_column_spacing(10)

        # Issue - when adding a 4th to 3 cams working fine, it permanently slows down everything til
        # app closed and reopened
        # Also, do want to add user interaction to control camera quality, ie have max values,
        # but user can lower to account for network?

        # 600 by 800 webcam h264 a bit of delay, tolerable?

        # Gstreamer pipelines - Need to be modified for real jetson stream - also tcp/udp issue
        # tryinng to get udp, need to allow udp port through firewall
        # Jetson ip: 10.160.22.170
        # 3 innomakers - mjpeg
        # front_line = "rtspsrc location=rtsp://localhost:8554/front protocols=tcp latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink"
        #front_line = "rtspsrc location=rtsp://192.168.0.2:8554/front latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink"
        front_line = "rtspsrc location=rtsp://localhost:8554/front latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! gtksink name=sink"
        back_line = "rtspsrc location=rtsp://localhost:8554/back latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink2"
        left_line = "rtspsrc location=rtsp://localhost:8554/left latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink3"
        right_line = "rtspsrc location=rtsp://localhost:8554/right latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink4"

        # After see this working switch to creating children with different dimensions to avoid this passing in
        # Pass in gst pipeline
        front_cam_grid = BaseCamGrid("Front", front_line, "sink", [1280,720], [1,0], [2,0], [0,1])
        # Switching these to be child extending base cam soon? Then don't need to pass in dim and add
        # functionality for switch button
        left_cam_grid = BaseCamGrid("Left", left_line, "sink3", [640,360], [0,1], [0,2], [1,0])
        right_cam_grid = BaseCamGrid("Right", right_line, "sink4", [640,360], [0,1], [0,2], [1,0])
        back_cam_grid = BaseCamGrid("Back", back_line, "sink2", [640,360], [0,1], [0,2], [1,0])
        
        # Col, Row, Width, Height
        root_grid.attach(front_cam_grid,0,0,1,3)
        root_grid.attach(left_cam_grid,1,0,1,1)
        root_grid.attach(right_cam_grid,1,1,1,1)
        root_grid.attach(back_cam_grid,1,2,1,1)

window = MainWindow()
window.connect("delete-event", Gtk.main_quit)
window.show_all()
Gtk.main()