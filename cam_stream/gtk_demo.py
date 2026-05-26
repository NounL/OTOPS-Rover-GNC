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

        self.pipeline = None
        self.pipeline2 = None
        self.pipeline3 = None

        self.connect("realize", self.on_realize)

        self.vBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        self.hBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # Error - need to add to hbox first, currently adding to 
        # adding horizontal layout into the vertical
        self.vBox.add(self.hBox)

        # Adding vertical layout to the window
        self.add(self.vBox)
    
    # Want to start stream seperate, then on button press connect, disconnect, and be able 
    # to connect to a different camera
    # need 6 buttons, 2 for each pipeline
    # then on jetson work on starting the stream, on the jetson, from this script
    def on_realize(self, widget):
        Gst.init(None)
        # Should be changed later as testing jpeg instead of h264
        #self.pipeline = Gst.parse_launch("rtspsrc location=rtsp://localhost:8554/front latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! gtksink name=sink")
        # self.pipeline2 = Gst.parse_launch("rtspsrc location=rtsp://localhost:8554/back latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! gtksink name=sink2")
        # self.pipeline3 = Gst.parse_launch("rtspsrc location=rtsp://localhost:8554/left latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! gtksink name=sink3")
        
        # gonna have 3 sinks, 1 for each stream
        # add an hbox to the vbox, it contains each sink

        # gtksink = self.pipeline.get_by_name("sink")
        # widgetSink = gtksink.props.widget
        # widgetSink.show()
        # #self.vBox.add(widgetSink)
        # self.hBox.add(widgetSink)

        # gtksink2 = self.pipeline2.get_by_name("sink2")
        # widgetSink2 = gtksink2.props.widget
        # widgetSink2.show()
        # #self.vBox.add(widgetSink)
        # self.hBox.add(widgetSink2)

        # gtksink3 = self.pipeline3.get_by_name("sink3")
        # widgetSink3 = gtksink3.props.widget
        # widgetSink3.show()
        # #self.vBox.add(widgetSink)
        # self.hBox.add(widgetSink3)

        # self.pipeline.set_state(Gst.State.PLAYING)
        # self.pipeline2.set_state(Gst.State.PLAYING)
        # self.pipeline3.set_state(Gst.State.PLAYING)


        btn1 = Gtk.Button(label="connect1")
        btn2 = Gtk.Button(label="disconnect1")

        btn3 = Gtk.Button(label="connect2")
        btn4 = Gtk.Button(label="disconnect2")

        btn5 = Gtk.Button(label="connect3")
        btn6 = Gtk.Button(label="disconnect3")

        # Button presses
        btn1.connect("clicked", self.on_btn1click)
        btn2.connect("clicked", self.on_btn2click)

        btn3.connect("clicked", self.on_btn3click)
        btn4.connect("clicked", self.on_btn4click)

        btn5.connect("clicked", self.on_btn5click)
        btn6.connect("clicked", self.on_btn6click)

        self.vBox.add(btn1)
        self.vBox.add(btn2)
        self.vBox.add(btn3)
        self.vBox.add(btn4)
        self.vBox.add(btn5)
        self.vBox.add(btn6)

        btn1.show()
        btn2.show()
        btn3.show()
        btn4.show()
        btn5.show()
        btn6.show()

    # Create pipelines in __init__
    # Attach widgets in on_realize
    # Start/stop pipelines on button press
    # Recreate pipeline only if it fails to start - have some error catch if statement in each button

    def on_btn1click(self, widget):
        # print("pipeline =", self.pipeline)
        # self.pipeline.set_state(Gst.State.PLAYING)
        #self.pipeline = Gst.parse_launch("rtspsrc location=rtsp://localhost:8554/front latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! gtksink name=sink")
        self.pipeline = Gst.parse_launch("rtspsrc location=rtsp://192.168.0.3:8554/front protocols=tcp latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink")
        gtksink = self.pipeline.get_by_name("sink")
        self.widgetSink = gtksink.props.widget
        self.widgetSink.show()
        #self.vBox.add(widgetSink)
        self.hBox.add(self.widgetSink)

        self.pipeline.set_state(Gst.State.PLAYING)

    def on_btn2click(self, widget):
        self.pipeline.set_state(Gst.State.NULL)
        self.pipeline = None
        self.widgetSink.hide()

    def on_btn3click(self, widget):
        self.pipeline2 = Gst.parse_launch("rtspsrc location=rtsp://192.168.0.3:8554/back protocols=tcp latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink2")
        gtksink2 = self.pipeline2.get_by_name("sink2")
        self.widgetSink2 = gtksink2.props.widget
        self.widgetSink2.show()
        self.hBox.add(self.widgetSink2)

        self.pipeline2.set_state(Gst.State.PLAYING)

    def on_btn4click(self, widget):
        self.pipeline2.set_state(Gst.State.NULL)
        self.pipeline2 = None
        self.widgetSink2.hide()

    def on_btn5click(self, widget):
        self.pipeline3 = Gst.parse_launch("rtspsrc location=rtsp://192.168.0.3:8554/left protocols=tcp latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! gtksink name=sink3")
        
        gtksink3 = self.pipeline3.get_by_name("sink3")
        self.widgetSink3 = gtksink3.props.widget
        self.widgetSink3.show()
        #self.vBox.add(widgetSink)
        self.hBox.add(self.widgetSink3)

        self.pipeline3.set_state(Gst.State.PLAYING)

    def on_btn6click(self, widget):
        self.pipeline3.set_state(Gst.State.NULL)
        self.pipeline3 = None
        self.widgetSink.hide()

myWindow = Window()
myWindow.show_all()
Gtk.main()
