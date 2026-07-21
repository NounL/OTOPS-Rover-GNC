# Ares' Amazing Cameras (OTOPS 2026)
# Olly Love
# 2025/2026 Interface for controlling the OTOPS rover cameras at CIRC
# Layouts/Design for each camera stream and its controls

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

gi.require_version("Gst", "1.0")
from gi.repository import Gst

# Grid Layout of a camera stream interface, with the stream, and control buttons
# Consists of a main outer grid (Placeholder/stream, inner grid)
# inner grid is a small menu for button placement
class BaseCamGrid(Gtk.Grid):
    def __init__(self, placement, pipeline_str, sink):
        # Maybe inheritance somewhere as this same as old CamGrid so far
        Gst.init(None)
        Gtk.Grid.__init__(self)
        self.placement = placement
        # Stores string used to create gstreamer pipeline
        self.pipeline_str = pipeline_str
        self.pipeline = None
        self.sink = sink
        #self.swap_callback = swap_callback
        # self.width = 1280
        # self.height = 960
        self.width = 525
        self.height = 295
        # Main grid everythings added to
        self.main_cam_grid = Gtk.Grid()
        self.add(self.main_cam_grid)
        self.main_cam_grid.set_row_spacing(2)
        self.main_cam_grid.set_column_spacing(2)
        # Inner grid for on/off buttons and camera label 
        self.inner_cam_grid = Gtk.Grid()
        self.inner_cam_grid.set_row_spacing(2)
        self.inner_cam_grid.set_column_spacing(5)
        self.placeholder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_screen_size()
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
        self._build_swaps()
        self.main_cam_grid.attach(self.placeholder,0,0,1,1)
        self.main_cam_grid.attach(self.inner_cam_grid,0,1,1,1)

    def set_screen_size(self):
        self.placeholder.set_size_request(self.width, self.height)

    def stream_on(self):
        # Only turn stream on when its off
        if not self.pipeline:
            print(self.pipeline_str)
            print(self.sink)
        #self.is_streaming = True
        #if self.is_streaming:
            # print("Error: Stream already on")
            # return

            self.pipeline = Gst.parse_launch(self.pipeline_str)
            gtksink = self.pipeline.get_by_name(self.sink)
            # if not gtksink:
            #     print(f"ERROR: Could not find sink '{self.sink}' in pipeline.")
            #     return

            self.widgetSink = gtksink.props.widget
            # same size as placeholder
            self.widgetSink.set_size_request(self.width,self.height)
            self.widgetSink.set_hexpand(False)
            self.widgetSink.set_vexpand(False)

            # Replacing empty placeholder with camera stream
            self.main_cam_grid.remove(self.placeholder)
            self.main_cam_grid.attach(self.widgetSink,0,0,1,1)
            self.widgetSink.show()
            self.pipeline.set_state(Gst.State.PLAYING)

            #bus = self.pipeline.get_bus()
            #bus.add_signal_watch()

            # Will this start the pipeline?
            #self.pipeline.set_state(Gst.State.PLAYING)
            # ret = self.pipeline.set_state(Gst.State.PLAYING)
            # if ret == Gst.StateChangeReturn.FAILURE:
            #     print("Failed to start pipeline.")
            #     self.stream_off()
            # else:
            #     print("ERROR: Stream already connected.")
        else:
            print("Error: Stream already on.")

    def stream_off(self):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None

            # Wait until it has completely stopped
            # self.pipeline.get_state(Gst.CLOCK_TIME_NONE)

            # bus = self.pipeline.get_bus()
            # bus.remove_signal_watch()

            # Replace cam stream with empty placeholder
            self.main_cam_grid.remove(self.widgetSink)
            #self.widgetSink.destroy()
            # self.widgetSink = None         
            # self.pipeline = None

            self.main_cam_grid.attach(self.placeholder,0,0,1,1)
            self.placeholder.show()
        else:
            print("ERROR: Stream already disconnected.")

    def on_btn_click(self, widget):
        self.stream_on()

    def off_btn_click(self, widget):
        self.stream_off()
        
    # Overwritten by small cam child - basecam does nothing with this
    def _build_swaps(self):
        pass

class LargeCamGrid(BaseCamGrid):
    def __init__(self, placement, pipeline_str, sink, swap_callback):
        super().__init__(placement, pipeline_str, sink)

        self.swap_callback = swap_callback
        self.width = 1280
        self.height = 960
        self.set_screen_size()
        self.left_shown = False
        self.front_shown = False
        self.right_shown = False
        self.back_shown = False

    def set_screen_size(self):
        self.placeholder.set_size_request(self.width, self.height)

    # adding extra focus feature to put small cam stream as main
    def _build_swaps(self):
        self.show_left_btn = Gtk.Button(label="Show Left")
        self.show_left_btn.connect("clicked", self.show_left_btn_click)
        self.inner_cam_grid.attach(self.show_left_btn,3,0,1,1)

        self.show_right_btn = Gtk.Button(label="Show Right")
        self.show_right_btn.connect("clicked", self.show_right_btn_click)
        self.inner_cam_grid.attach(self.show_right_btn,4,0,1,1)

        self.show_back_btn = Gtk.Button(label="Show Back")
        self.show_back_btn.connect("clicked", self.show_back_btn_click)
        self.inner_cam_grid.attach(self.show_back_btn,5,0,1,1)

        self.reset_front_btn = Gtk.Button(label="Reset Front")
        self.reset_front_btn.connect("clicked", self.reset_front_btn_click)
        self.inner_cam_grid.attach(self.reset_front_btn,6,0,1,1)

    def show_left_btn_click(self, widget):
        self.front_shown = False
        self.right_shown = False
        self.back_shown = False
        # Sending left keyword to main
        self.swap_callback("Left")

        self.left_shown = True

    def show_right_btn_click(self, widget):
        self.front_shown = False
        self.left_shown = False
        self.back_shown = False
        self.swap_callback("Right")

        self.right_shown = True

    def show_back_btn_click(self, widget):
        self.front_shown = False
        self.left_shown = False
        self.right_shown = False
        self.swap_callback("Back")

        self.back_shown = True

    def reset_front_btn_click(self, widget):
        self.left_shown = False
        self.right_shown = False
        self.back_shown = False
        self.swap_callback("Front")

        self.front_shown = True
        
        
