// Olly Love
// rtsp multi-camera stream
// One rtsp server and port, multiple mounts, each to view a different stream

// How to run:
// gcc nodelayrtsp.c $(pkg-config --cflags --libs gstreamer-rtsp-server-1.0)
// ./a.out

// sync=false here may cause to much cpu usage
// Might need to modify latency=0 to a few ms 
// Note - better to use sink that has a window that can be moved around the screen when testing
// gst-launch-1.0 rtspsrc location=rtsp://localhost:8554/front latency=0 drop-on-latency=true ! rtph265depay ! queue ! h265parse ! avdec_h265 ! videoconvert ! ximagesink
// gst-launch-1.0 rtspsrc location=rtsp://localhost:8554/back latency=0 drop-on-latency=true ! rtph265depay ! queue ! h265parse ! avdec_h265 ! videoconvert ! ximagesink
// gst-launch-1.0 rtspsrc location=rtsp://localhost:8554/left latency=0 drop-on-latency=true ! rtph265depay ! queue ! h265parse ! avdec_h265 ! videoconvert ! ximagesink
// gst-launch-1.0 rtspsrc location=rtsp://localhost:8554/right latency=0 drop-on-latency=true ! rtph265depay ! queue ! h265parse ! avdec_h265 ! videoconvert ! ximagesink

#include <stdio.h>
#include <gst/gst.h>
#include <gst/rtsp-server/rtsp-server.h>

#define NUM_CAMERAS 1

void gst_rtsp_server_run(int port)
{
    GMainLoop *loop;
    GstRTSPServer *server;
    GstRTSPMountPoints *mounts;

    // Array of factory pointers - need a factory for each port
    GstRTSPMediaFactory *factories[NUM_CAMERAS];

    char *pipeline_descs[NUM_CAMERAS] = {
        // speed-preset may reduce quality
        // This works great, modify for actual camera, then modify for gpu
        "( videotestsrc is-live=true ! x265enc tune=zerolatency speed-preset=ultrafast ! h265parse ! rtph265pay name=pay0 pt=96 )",

        // Pipeline for h264 test webcam - this webcam doesn't need encoding as outputs h264 automatically
        // "( v4l2src device=/dev/video2 ! video/x-h264, width=640, height=480, framerate=30/1 ! h264parse ! rtph264pay name=pay0 pt=96 )"
        // Modified test webcam pipeline for low latency
        // tune=zerolatency speed-preset=ultrafast - these properties only for cpu encoder
        // "( v4l2src device=/dev/video2 is-live=true ! video/x-h264, width=640, height=480, framerate=30/1 ! h264parse ! rtph264pay name=pay0 pt=96 )"
        
        // If these dont work try taking out iframeinterval, insert-sps-pps, and change back to h264
        // even take out the part specifying memory:NVMM to just have nvvidconv
        // Line for actual camera - actual cameras send raw data, need encoding
        // mjpeg - more cpu, more latency, less bandwidth
        // Also try reducing bitrate since 480p, 8 mil for 1080p
        // "( v4l2src device=/dev/video2 is-live=true ! image/jpeg, width=640, height=480, framerate=30/1 ! \
        //    jpegdec ! nvvidconv ! 'video/x-raw(memory:NVMM),format=NV12,width=640,height=480,framerate=30/1' ! \
        //    nvv4l2h265enc bitrate=8000000 iframeinterval=15 insert-sps-pps=true ! h265parse ! \
        //    rtph265pay name=pay0 pt=96 config-interval=1 )"
        
        // yuy - less cpu, less latency, higher bandwidth
        // "( v4l2src device=/dev/video2 is-live=true ! video/x-raw, format=YUY2 width=640, height=480, framerate=30/1 ! \
        //    nvvidconv ! 'video/x-raw(memory:NVMM),format=NV12,width=640,height=480,framerate=30/1' ! nvv4l2h265enc bitrate=8000000 \
        //    iframeinterval=15 insert-sps-pps=true ! h265parse ! rtph265pay name=pay0 pt=96 config-interval=1 )"

        // Last resort if gpu not working
        // Line for actual camera no gpu - yuy - make sure to specify this the format
        // "( v4l2src device=/dev/video2 is-live=true ! video/x-raw, format=YUY2 width=640, height=480, framerate=30/1 ! \
        //    videoconvert ! x265enc bitrate=500 tune=zerolatency speed-preset=ultrafast iframeinterval=15 insert-sps-pps=true ! \
        //    h265parse ! rtph265pay name=pay0 pt=96 config-interval=1 )"
    };

    gst_init(NULL, NULL);

    loop = g_main_loop_new(NULL, FALSE);

    server = gst_rtsp_server_new();
    g_object_set(server, "service", g_strdup_printf("%d", port), NULL);

    // Stores mount points
    mounts = gst_rtsp_server_get_mount_points(server);

    // Testing w 4 cameras, can easily add more
    const char *mount_points[] = {"/front", "/back", "/left", "/right"};

    // Building pipelines
    for (int i = 0; i < NUM_CAMERAS; i++){
        factories[i] = gst_rtsp_media_factory_new();
        gst_rtsp_media_factory_set_launch(factories[i], pipeline_descs[i]);
        gst_rtsp_media_factory_set_shared(factories[i], TRUE);
    }

    // Mounting pipelines
    for (int i = 0; i < NUM_CAMERAS; i++){
        gst_rtsp_mount_points_add_factory(mounts, mount_points[i], factories[i]);
    }
    
    g_object_unref(mounts);
    gst_rtsp_server_attach(server, NULL);

    for (int i = 0; i < NUM_CAMERAS; i++){
        g_print("RTSP server is running at rtsp://localhost:%d%s\n", port, mount_points[i]);
    }

    g_main_loop_run(loop);
}

int main(int argc, char const *argv[])
{
    // Default RTSP port
    int port = 8554;

    gst_rtsp_server_run(port);

    return 0;
}