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
    def __init__(self, placement, pipeline_str, sink, screen_dim, on_colrow, off_colrow, inner_colrow):
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
        self.main_cam_grid.set_row_spacing(5)
        self.main_cam_grid.set_column_spacing(5)
        # Inner grid for on/off buttons and camera label 
        self.inner_cam_grid = Gtk.Grid()
        self.inner_cam_grid.set_row_spacing(5)
        self.inner_cam_grid.set_column_spacing(5)

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

        # Heres where it varies - for large grid want large screen spanning 
        # 3 columns in 0th row, then inner grid in row 1, each label, button 1 width 1 height
        
        # Big grid code - putting here to figure out pass in
        # self.inner_cam_grid.attach(self.cam_lbl,0,0,1,1)
        # # col 1, row 1, 1 by 1
        # self.inner_cam_grid.attach(self.on_btn,1,0,1,1)
        # self.inner_cam_grid.attach(self.off_btn,2,0,1,1)
        # # Can tweak column span to see fit
        # self.outer_cam_grid.attach(self.placeholder,0,0,1,1)
        # self.outer_cam_grid.attach(self.inner_cam_grid,0,1,1,1)

        # For small grid want small screen spanning
        # spans 0th column (only 1 col i think), 3 rows, 
        # inner grid in col 2 with label, on, off, (and extra switch button) 1 by 1

        # Small grid code - putting here to figure out pass in - child class extends adding extra button
        # self.inner_cam_grid.attach(self.cam_lbl,0,0,1,1)
        # # col 1, row 1, 1 by 1
        # self.inner_cam_grid.attach(self.on_btn,0,1,1,1)
        # self.inner_cam_grid.attach(self.off_btn,0,2,1,1)
        # # Can tweak column span to see fit
        # self.outer_cam_grid.attach(self.placeholder,0,0,1,1)
        # self.outer_cam_grid.attach(self.inner_cam_grid,1,0,1,1)

        # Can pass in 3 arrays
        # on_colrow (ie [1,0] vs [0,1]), off_colrow, inner_colrow
        # final that should work for both 
        self.inner_cam_grid.attach(self.cam_lbl,0,0,1,1)
        # col 1, row 1, 1 by 1
        self.inner_cam_grid.attach(self.on_btn,on_colrow[0],on_colrow[1],1,1)
        self.inner_cam_grid.attach(self.off_btn,off_colrow[0],off_colrow[1],1,1)
        # Can tweak column span to see fit
        self.main_cam_grid.attach(self.placeholder,0,0,1,1)
        self.main_cam_grid.attach(self.inner_cam_grid,inner_colrow[0],inner_colrow[1],1,1)

    def on_btn_click(self, widget):
        if not self.pipeline:
            self.pipeline = Gst.parse_launch(self.pipeline_str)
            gtksink = self.pipeline.get_by_name(self.sink)
            self.widgetSink = gtksink.props.widget
            # same size as placeholder
            self.widgetSink.set_size_request(self.width,self.height)

            # Replacing empty placeholder with camera stream
            self.main_cam_grid.remove(self.placeholder)
            self.main_cam_grid.attach(self.widgetSink,0,0,1,1)
            self.widgetSink.show()
            self.pipeline.set_state(Gst.State.PLAYING)
        else:
            print("ERROR: Stream already connected.")

    def off_btn_click(self, widget):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
            # Replace cam stream with empty placeholder
            self.main_cam_grid.remove(self.widgetSink)
            self.main_cam_grid.attach(self.placeholder,0,0,1,1)
            self.placeholder.show()
        else:
            print("ERROR: Stream already disconnected.")
        
        
