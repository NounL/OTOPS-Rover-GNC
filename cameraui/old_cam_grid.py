# Custom Gtk grid widget 
# Displays ...

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

gi.require_version("Gst", "1.0")
from gi.repository import Gst

# Pass in the Gtk widget being extended
class CamGrid(Gtk.Grid):
    # Pass in front, back, left, or right as cameras placement
    def __init__(self, placement, pipeline_str, sink):
        Gst.init(None)
        # initialize as a Gtk grid widget
        Gtk.Grid.__init__(self)
        self.placement = placement
        # Stores string used to create gstreamer pipeline
        self.pipeline_str = pipeline_str
        self.pipeline = None
        self.sink = sink
        # Outer grid - holds placeholder and inner grid
        self.outer_cam_grid = Gtk.Grid()
        self.add(self.outer_cam_grid)
        self.outer_cam_grid.set_row_spacing(5)
        self.outer_cam_grid.set_column_spacing(5)

        # Inner grid for on/off buttons and camera label 
        self.inner_cam_grid = Gtk.Grid()
        self.inner_cam_grid.set_row_spacing(5)
        self.inner_cam_grid.set_column_spacing(5)

        # Empty black box that holds place when stream is off
        self.placeholder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # Size of the box for a stream
        # Width by height
        self.placeholder.set_size_request(700,400)
        self.placeholder.set_halign(Gtk.Align.START)
        self.placeholder.set_valign(Gtk.Align.START)
        # Background color is black
        self.placeholder.override_background_color(
            Gtk.StateFlags.NORMAL,
            Gdk.RGBA(0, 0, 0, 1)
        )

        # May cause error
        self.cam_lbl = Gtk.Label()
        # Change text color
        color = Gdk.RGBA()
        color.parse("black")
        self.cam_lbl.override_color(Gtk.StateFlags.NORMAL, color)
        # Large text - can't seem to control font with numbers
        self.cam_lbl.set_markup(f"<big>{self.placement}</big>")

        self.on_btn = Gtk.Button(label="On")
        self.off_btn = Gtk.Button(label="Off")
        self.cam_btn = Gtk.Button(label="View")

        self.on_btn.connect("clicked", self.on_btn_click)
        self.off_btn.connect("clicked", self.off_btn_click)
        self.cam_btn.connect("clicked", self.cam_btn_click)

        # col, row, width, height
        self.inner_cam_grid.attach(self.cam_lbl,0,0,1,1)
        self.inner_cam_grid.attach(self.on_btn,0,1,1,1)
        self.inner_cam_grid.attach(self.off_btn,1,1,1,1)
        self.inner_cam_grid.attach(self.cam_btn,2,1,1,1)
        
        # Spans 3 to fit 3 horizontal buttons
        self.outer_cam_grid.attach(self.placeholder,0,0,3,1)
        self.outer_cam_grid.attach(self.inner_cam_grid,0,1,3,1)

    def on_btn_click(self, widget):
        if not self.pipeline:
            self.pipeline = Gst.parse_launch(self.pipeline_str)
            gtksink = self.pipeline.get_by_name(self.sink)
            self.widgetSink = gtksink.props.widget
            # same size as placeholder
            self.widgetSink.set_size_request(700, 400)

            # Replacing empty placeholder with camera stream
            self.outer_cam_grid.remove(self.placeholder)
            self.outer_cam_grid.attach(self.widgetSink,0,0,3,1)
            self.widgetSink.show()
            self.pipeline.set_state(Gst.State.PLAYING)
        else:
            print("ERROR: Stream already connected.")

    def off_btn_click(self, widget):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
            # Replace cam stream with empty placeholder
            self.outer_cam_grid.remove(self.widgetSink)
            self.outer_cam_grid.attach(self.placeholder,0,0,3,1)
            self.placeholder.show()
        else:
            print("ERROR: Stream already disconnected.")

    # Somehow causes change of page to page with a sole image of the camera
    # via stack and stackswitcher
    def cam_btn_click(self, widget):
        print("test")
        
        
