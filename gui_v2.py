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
from cam_grid_v2 import BaseCamGrid, SmallCamGrid

# gi.require_version("Gst", "1.0")
# from gi.repository import Gst

# Starting off using stack/stack switcher for multi-page layout
# Gonna build how the ui should look, then work around the bugs with the camera feeds
class MainWindow(Gtk.Window):
    def __init__(self):
        # Super classes constructor
        Gtk.Window.__init__(self, title="Ares' Amazing Cameras")
        # May need to adjust this a tiny bit to fit main groundstation laptop if its smaller
        self.set_default_size(1900,1080)
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
        root_grid.set_row_spacing(2)
        root_grid.set_column_spacing(2)

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
        
        # Tomorrow testing decoding to fit smaller streams
        front_line = "rtspsrc location=rtsp://192.168.0.2:8554/front latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! gtksink name=sink"
        left_line = "rtspsrc location=rtsp://192.168.0.2:8554/left latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink3"
        right_line = "rtspsrc location=rtsp://192.168.0.2:8554/right latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink4"
        back_line = "rtspsrc location=rtsp://192.168.0.2:8554/back latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink2"

        # Test line for resizing - may not work - resizing main stream to fit small window - test after gtksink properties test
        #front_test = "rtspsrc location=rtsp://localhost:8554/front latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! videoscale ! video/x-raw, width=480, height=270 ! gtksink name=sink"

        # width by height
        # Need to maintain 4:3 ratio to not stretch, if enlarging enlarge both my same factor and check if 4:3
        # so currently for 640 by 480, double is 1280 by 960 - try to make bit bigger
        # 1920 by 1440 - way to large 
        # to scale multiply each by the same factor
        # 1280 * 1.1 = 1408
        # 960 * 1.1 = 1056

        # Small cams is 16:9 res
        # For small cams, og is 640 by 360 
        # divide by 2: 320 by 180 (will shrinking stream to fit even work???)
        # 320 * 1.3 = 416, 320 * 1.5 = 480
        # 180 * 1.3 = 234, 180 * 1.5 = 270
        
        # current problem, fixing size of cameras to be smaller so large cam can be big as possible
        # need to account for set size (so large can become small) in switch function

        # After see this working switch to creating children with different dimensions to avoid this passing in
        front_cam_grid = BaseCamGrid("Front", front_line, "sink", [1408,1056])
        # Switching these to be child extending base cam soon? Then don't need to pass in dim and add
        # functionality for switch button
        left_cam_grid = SmallCamGrid("Left", left_line, "sink3", [480,270])
        right_cam_grid = SmallCamGrid("Right", right_line, "sink4", [480,270])
        back_cam_grid = SmallCamGrid("Back", back_line, "sink2", [480,270])
        
        # Col, Row, Width, Height
        root_grid.attach(front_cam_grid,0,0,1,3)
        root_grid.attach(left_cam_grid,1,0,1,1)
        root_grid.attach(right_cam_grid,1,1,1,1)
        root_grid.attach(back_cam_grid,1,2,1,1)

    # Need swap logic to happen here as this where the cams are stored
    #def swap(self, smallcam, maincam):

        

window = MainWindow()
window.connect("delete-event", Gtk.main_quit)
window.show_all()
Gtk.main()