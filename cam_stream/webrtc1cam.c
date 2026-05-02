// How to run
// gcc webrtc1cam.c $(pkg-config --cflags --libs gstreamer-1.0)
// ./a.out

// Error, something wrong with how its displaying, web directory pointing to wrong place?

#include <stdio.h>
#include <gst/gst.h>

void gst_run_stream(int port)
{
    GMainLoop *loop;
    GstElement *pipeline;
    GstStateChangeReturn ret;

    gst_init(NULL, NULL);

    loop = g_main_loop_new(NULL, FALSE);

    // Need to run from this directory: /home/ollylove/OTOPS/gstream_work/gst-plugins-rs/net/webrtc/gstwebrtc-api/dist
    // Need to be in gstwebrtc-api/dist, this will be different on jetson

    // Null for no error details
    // Should show a test feed under remote streams part of site
    // pipeline = gst_parse_launch(
    //     "videotestsrc ! webrtcsink run-signalling-server=true run-web-server=true "
    //     "web-server-directory=/home/ollylove/OTOPS/gstream_work/gst-plugins-rs/net/webrtc/gstwebrtc-api/dist",
    //     NULL
    // );

    pipeline = gst_parse_launch(
        "videotestsrc ! webrtcsink run-signalling-server=true run-web-server=true "
        "web-server-directory=/home/ollylove/OTOPS/gstream_work/gst-plugins-rs/net/webrtc",
        NULL
    );

    if (!pipeline) {
        g_printerr("Pipeline failed to launch\n");
        return;
    }

    /* Start playing */
    ret = gst_element_set_state (pipeline, GST_STATE_PLAYING);
    if (ret == GST_STATE_CHANGE_FAILURE) {
        g_printerr ("Unable to set the pipeline to the playing state.\n");
        gst_object_unref (pipeline);
        return;
    }

    //g_print("Stream running at http://localhost:%d\n", port);
    //g_print("Stream running at http://0.0.0.0:%d\n", port);

    g_main_loop_run(loop);

    /* Free resources */
    gst_element_set_state (pipeline, GST_STATE_NULL);
    gst_object_unref (pipeline);
}

int main(int argc, char const *argv[])
{
    // Default port
    int port = 8554;
    gst_run_stream(port);
    return 0;
}