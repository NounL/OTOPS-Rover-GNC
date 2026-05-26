// Olly Love
// rtsp multi-camera test stream
// One rtsp server and port, multiple mounts, each to view a different stream

// How to run:
// gcc teststream.c $(pkg-config --cflags --libs gstreamer-rtsp-server-1.0)
// ./a.out

#include <stdio.h>
#include <gst/gst.h>
#include <gst/rtsp-server/rtsp-server.h>

#define NUM_CAMERAS 3

void gst_rtsp_server_run(int port)
{
    GMainLoop *loop;
    GstRTSPServer *server;
    GstRTSPMountPoints *mounts;

    // Array of factory pointers - need a factory for each port
    GstRTSPMediaFactory *factories[NUM_CAMERAS];

    char *pipeline_descs[NUM_CAMERAS] = {
        // To test multi-stream just copy and paste this however many times and change NUM_CAMERAS
        "( videotestsrc is-live=true ! x264enc tune=zerolatency speed-preset=ultrafast ! h264parse ! rtph264pay name=pay0 pt=96 )",
        "( videotestsrc is-live=true ! x264enc tune=zerolatency speed-preset=ultrafast ! h264parse ! rtph264pay name=pay0 pt=96 )",
        "( videotestsrc is-live=true ! x264enc tune=zerolatency speed-preset=ultrafast ! h264parse ! rtph264pay name=pay0 pt=96 )"
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