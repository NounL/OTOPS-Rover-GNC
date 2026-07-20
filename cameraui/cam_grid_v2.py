# Custom Gtk grid widget 
# Displays ...

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

gi.require_version("Gst", "1.0")
from gi.repository import Gst

# Grid Layout of a camera stream interface, with the stream, and control buttons
# Consists of a main outer grid (Placeholder/stream, inner grid)
# inner grid is a small menu for button placement
class BaseCamGrid(Gtk.Grid):
    def __init__(self, placement, pipeline_str, sink, screen_dim):
        # Maybe inheritance somewhere as this same as old CamGrid so far
        Gst.init(None)
        Gtk.Grid.__init__(self)
        self.placement = placement
        # Stores string used to create gstreamer pipeline
        self.pipeline_str = pipeline_str
        self.pipeline = None
        self.sink = sink
        self.width = screen_dim[0]
        self.height = screen_dim[1]
        # Main grid everythings added to
        self.main_cam_grid = Gtk.Grid()
        self.add(self.main_cam_grid)
        self.main_cam_grid.set_row_spacing(2)
        self.main_cam_grid.set_column_spacing(2)
        # Inner grid for on/off buttons and camera label 
        self.inner_cam_grid = Gtk.Grid()
        self.inner_cam_grid.set_row_spacing(2)
        self.inner_cam_grid.set_column_spacing(2)

        self.placeholder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.placeholder.set_size_request(self.width, self.height)
        self.placeholder.set_halign(Gtk.Align.START)
        self.placeholder.set_valign(Gtk.Align.START)
        # Background color is black
        self.placeholder.override_background_color(
            Gtk.StateFlags.NORMAL,
            Gdk.RGBA(0, 0, 0, 1)
        )

        self.cam_lbl = Gtk.Label()
        # Change text color
        color = Gdk.RGBA()
        color.parse("black")
        self.cam_lbl.override_color(Gtk.StateFlags.NORMAL, color)
        # Large text - can't seem to control font with numbers
        self.cam_lbl.set_markup(f"<big>{self.placement}</big>")

        self.on_btn = Gtk.Button(label="On")
        self.off_btn = Gtk.Button(label="Off")

        self.on_btn.connect("clicked", self.on_btn_click)
        self.off_btn.connect("clicked", self.off_btn_click)

        self.inner_cam_grid.attach(self.cam_lbl,0,0,1,1)
        self.inner_cam_grid.attach(self.on_btn,1,0,1,1)
        self.inner_cam_grid.attach(self.off_btn,2,0,1,1)
        self._build_swap()
        self.main_cam_grid.attach(self.placeholder,0,0,1,1)
        self.main_cam_grid.attach(self.inner_cam_grid,0,1,1,1)

    def stream_on(self):
        if not self.pipeline:
            self.pipeline = Gst.parse_launch(self.pipeline_str)
            gtksink = self.pipeline.get_by_name(self.sink)
            self.widgetSink = gtksink.props.widget
            # same size as placeholder
            self.widgetSink.set_size_request(self.width,self.height)

            # Trying to stop widget from expanding larger then the placeholder
            # issue, i want the front main stream to expand, i want the small ones to shrink
            # look into scaling inside the pipeline, but then theres the issue with switching
            # and wanting to be large for the box
            # want to figure out switch and inheritance then look at forcing certain size
            # only want to force size on the 640 by 360 to make them even smaller to fit the boxes, 
            # when switching want to force the main large sink to be smaller, (maybe just cuz i start and stop, i pass
            # in different gst line that requests size, and do everything in the gst line requesting size
            self.widgetSink.set_hexpand(False)
            self.widgetSink.set_vexpand(False)

            # Replacing empty placeholder with camera stream
            self.main_cam_grid.remove(self.placeholder)
            self.main_cam_grid.attach(self.widgetSink,0,0,1,1)
            self.widgetSink.show()
            self.pipeline.set_state(Gst.State.PLAYING)
        else:
            print("ERROR: Stream already connected.")

    def stream_off(self):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
            # Replace cam stream with empty placeholder
            self.main_cam_grid.remove(self.widgetSink)
            self.main_cam_grid.attach(self.placeholder,0,0,1,1)
            self.placeholder.show()
        else:
            print("ERROR: Stream already disconnected.")

    def on_btn_click(self, widget):
        self.stream_on()

    def off_btn_click(self, widget):
        self.stream_off()
        
    # Overwritten by small cam child - basecam does nothing with this
    def _build_swap(self):
        pass

class SmallCamGrid(BaseCamGrid):
    # def __init__(self, placement, pipeline_str, sink, screen_dim, swap_func):
    #     super().__init__(placement, pipeline_str, sink, screen_dim)
        
    #     # Passing in swap function - accessing seperate cams in main
    #     self.swap_func = swap_func


    # adding extra focus feature to put small cam stream as main
    def _build_swap(self):
        self.swap_btn = Gtk.Button(label="Swap")
        self.swap_btn.connect("clicked", self.swap_btn_click)
        self.inner_cam_grid.attach(self.swap_btn,3,0,1,1)


    # later worry about multiple swaps and feeds getting mixed up - reset button?
    # pass in the pipelines I want to swap
    def swap_btn_click(self, widget):
        # Want to turn off this camera stream, turn off the front camera stream
        # turn this camera on in the front stream
        # turn front cam on in this stream

        # modify off button to call an off function - to call that off function here
        # Turns off small swapping camera
        #self.swap_func(self)
        pass
        
        
