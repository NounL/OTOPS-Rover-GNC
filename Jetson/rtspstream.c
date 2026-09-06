// Olly Love
// rtsp multi-camera stream
// One rtsp server and port, multiple mounts, each to view a different stream

// v4l2-ctl --list-devices
// Scan for hardware specs: 
// v4l2-ctl --list-formats-ext --device /dev/video0

// How to run:
// gcc latest-rtspstream.c $(pkg-config --cflags --libs gstreamer-rtsp-server-1.0)
// ./a.out

// Rename
// gcc latest-rtspstream.c -o teststream ...

// Monitor usb with lsusb -tv

// sync=false here may cause to much cpu usage
// Might need to modify latency=0 to a few ms 
// Note - better to use sink that has a window that can be moved around the screen when testing
// gst-launch-1.0 rtspsrc location=rtsp://localhost:8554/front latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! ximagesink
// gst-launch-1.0 rtspsrc location=rtsp://localhost:8554/back latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! ximagesink
// gst-launch-1.0 rtspsrc location=rtsp://localhost:8554/left latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! ximagesink
// gst-launch-1.0 rtspsrc location=rtsp://localhost:8554/right latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! ximagesink

// Line to connect for mjpeg:
// Could move queue earlier like before rtpjpegdepay if there are issues
// gst-launch-1.0 rtspsrc location=rtsp://localhost:8554/front latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! ximagesink
// gst-launch-1.0 rtspsrc location=rtsp://localhost:8554/back latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! ximagesink
// gst-launch-1.0 rtspsrc location=rtsp://localhost:8554/left latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! ximagesink
// gst-launch-1.0 rtspsrc location=rtsp://localhost:8554/right latency=0 drop-on-latency=true ! rtpjpegdepay ! queue ! jpegdec ! videoconvert ! ximagesink

// Line for webcam
// gst-launch-1.0 rtspsrc location=rtsp://localhost:8554/front latency=0 drop-on-latency=true ! rtph264depay ! queue ! h264parse ! avdec_h264 ! videoconvert ! ximagesink


#include <stdio.h>
#include <gst/gst.h>
#include <gst/rtsp-server/rtsp-server.h>

#define NUM_CAMERAS 4

// prev passed in char char * host, int port
void gst_rtsp_server_run(int port)
{
    GMainLoop *loop;
    GstRTSPServer *server;
    GstRTSPMountPoints *mounts;

    // Array of factory pointers - need a factory for each port
    GstRTSPMediaFactory *factories[NUM_CAMERAS];

    // Try a mjpeg pipeline for better cpu
    char *pipeline_descs[NUM_CAMERAS] = {
        // Test line
        // speed-preset may reduce quality
        //"( videotestsrc is-live=true ! x264enc tune=zerolatency speed-preset=ultrafast ! h264parse ! rtph264pay name=pay0 pt=96 )",

        // Mjpeg test
        // with real stream don't need jpegenc
        //"( videotestsrc is-live=true ! jpegenc ! jpegparse ! rtpjpegpay name=pay0 pt=26 )"
		
		// ip address: 10.160.22.170
		// Works - usb overload issue, only 2 work at a time
		
		// Testing Mjpeg
        // "( v4l2src device=/dev/video0 is-live=true ! video/x-raw, width=640, height=480, framerate=30/1 ! \
        //    videoconvert ! x264enc bitrate=100 tune=zerolatency speed-preset=ultrafast iframeinterval=15 insert-sps-pps=true ! \
        //    h264parse ! rtph264pay name=pay0 pt=96 config-interval=1 )",
           
        // "( v4l2src device=/dev/video2 is-live=true ! video/x-raw, width=640, height=480, framerate=30/1 ! \
        //    videoconvert ! x264enc bitrate=100 tune=zerolatency speed-preset=ultrafast iframeinterval=15 insert-sps-pps=true ! \
        //    h264parse ! rtph264pay name=pay0 pt=96 config-interval=1 )",
           
        //  "( v4l2src device=/dev/video4 is-live=true ! video/x-raw, width=640, height=480, framerate=30/1 ! \
        //    videoconvert ! x264enc bitrate=100 tune=zerolatency speed-preset=ultrafast iframeinterval=15 insert-sps-pps=true ! \
        //    h264parse ! rtph264pay name=pay0 pt=96 config-interval=1 )",
        
        // 640 by 480 highest quality for no delay so far - also 600 by 800 might be ok w rover setup
        // on real setup 1280 by 720 works
        "( v4l2src device=/dev/video0 is-live=true ! video/x-h264, width=800, height=600, framerate=30/1 ! \
		  h264parse ! rtph264pay name=pay0 pt=96 config-interval=1 )",
		   
		 //"( v4l2src device=/dev/video0 is-live=true ! image/jpeg, width=640, height=360, framerate=30/1 ! \
		   //jpegparse ! rtpjpegpay name=pay0 pt=96 config-interval=1 )",
		
		"( v4l2src device=/dev/video2 is-live=true ! image/jpeg, width=640, height=360, framerate=30/1 ! \
		   jpegparse ! rtpjpegpay name=pay0 pt=96 config-interval=1 )",

		"( v4l2src device=/dev/video4 is-live=true ! image/jpeg, width=640, height=360, framerate=30/1 ! \
		   jpegparse ! rtpjpegpay name=pay0 pt=26 config-interval=1 )",
		
		"( v4l2src device=/dev/video6 is-live=true ! image/jpeg, width=640, height=360, framerate=30/1 ! \
		   jpegparse ! rtpjpegpay name=pay0 pt=26 config-interval=1 )",
		   
		//"( v4l2src device=/dev/video6 is-live=true ! image/jpeg, width=640, height=360, framerate=30/1 ! \
		//     jpegparse ! rtpjpegpay name=pay0 pt=26 config-interval=1 )",
    };

    gst_init(NULL, NULL);

    loop = g_main_loop_new(NULL, FALSE);

    server = gst_rtsp_server_new();
    g_object_set(server, "service", g_strdup_printf("%d", port), NULL);

    // Stores mount points
    mounts = gst_rtsp_server_get_mount_points(server);

    // Testing w 4 cameras, can easily add more
    const char *mount_points[] = {"/front", "/left", "/right", "/back"};

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
        //g_print("RTSP server is running at rtsp://%s:%d%s\n",host, port, mount_points[i]);
        g_print("RTSP server is running at rtsp://192.168.1.31:%d%s\n", port, mount_points[i]);
    }

    g_main_loop_run(loop);
}

int main(int argc, char const *argv[])
{
    // Default RTSP port
    int port = 8554;
    

    //gst_rtsp_server_run("192.168.0.2", port);
    gst_rtsp_server_run(port);

    return 0;
}
