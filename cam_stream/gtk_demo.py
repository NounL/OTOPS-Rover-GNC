# Olly Love
# Demoing how to get camera feed into our ui

# Source: https://www.youtube.com/watch?v=FszqUfibD3w

# Must run server file first else this won't work

# Installs: 
# sudo apt install libgtk-3-dev gir1.2-gtk-3.0 python3-gi python3-gi-cairo
# sudo apt install gstreamer1.0-gtk3

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

gi.require_version("Gst", "1.0")
from gi.repository import Gst

class Window(Gtk.Window):

    def __init__(self):

        Gtk.Window.__init__(self, title="camera app")
        self.set_default_size(500,400)

        self.connect("realize", self.on_realize)

        self.vBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Adding vertical layout to the window
        self.add(self.vBox)

    def on_realize(self, widget):
        Gst.init(None)
        pipeline = Gst.parse_launch("rtspsrc location=rtsp://localhost:8554/front latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! gtksink name=sink")
        gtksink = pipeline.get_by_name("sink")
        widgetSink = gtksink.props.widget
        widgetSink.show()
        self.vBox.add(widgetSink)
        pipeline.set_state(Gst.State.PLAYING)
        # These buttons dont do anything, just showing a layout + the camera feed
        btn1 = Gtk.Button(label="record")
        btn2 = Gtk.Button(label="snapshot")
        self.vBox.add(btn1)
        self.vBox.add(btn2)
        btn1.show()
        btn2.show()

myWindow = Window()
myWindow.show_all()
Gtk.main()
