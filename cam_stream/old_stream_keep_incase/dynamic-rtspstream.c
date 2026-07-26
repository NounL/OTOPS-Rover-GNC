// Olly Love
// rtsp multi-camera stream
// One rtsp server and port, multiple mounts, each to view a different stream

// v4l2-ctl --list-devices
// Scan for hardware specs: 
// v4l2-ctl --list-formats-ext --device /dev/video0

// How to run:
// gcc rtspstream.c $(pkg-config --cflags --libs gstreamer-rtsp-server-1.0)
// ./a.out

// Rename
// gcc latest-rtspstream.c -o teststream ...
// Monitor usb with lsusb -tv

#include <stdio.h>
#include <gst/gst.h>
#include <gst/rtsp-server/rtsp-server.h>

#define NUM_CAMERAS 4

// usb port numbers unique to the specific port and don't change
// 1.4 = usb hub 1, port number 4 (the port furthest from the usb c port), plugged front in here
// 1.3 = left
// 1.2 = right
// 2.4 = back - but might be different if plugged into different port on jetson
// Ideal to set up like video0 will be h.264 front, video2 left, video4 right, video6 back

// Limit of how long a line is 
#define MAX_LINES 100
#define LINE_LEN 256

// prev passed in char char * host, int port
void gst_rtsp_server_run(int port)
{
    GMainLoop *loop;
    GstRTSPServer *server;
    GstRTSPMountPoints *mounts;

    // Array of factory pointers - need a factory for each port
    GstRTSPMediaFactory *factories[NUM_CAMERAS];
    
    // 4 pipelines with 1000 allocated for the max length of each pipeline
    char pipeline_descs[NUM_CAMERAS][1000];
    
    FILE *output;
    // 4 camera numbers + null terminator for some reason cuz c needs that
    char dev_nums[5];
    // Storing data read from popen command
    char data[MAX_LINES][LINE_LEN];
    // Counting rows
    int line = 0;
    // counting indices on dev_nums
    int k = 0;

    // Executing linux shell command to see device info and get usb cam data
    output = popen("v4l2-ctl --list-devices", "r");

    if (output == NULL) {
        fputs("POPEN: Failed to execute command.\n", stderr);
    }
    else {
        // Reads lines in one at a time
        while (fgets(data[line], LINE_LEN, output) != NULL) {
            line++;
        }
    }
    pclose(output);

    // Iterating over every line in the output
    // then every column (every individual char)
    for (int i = 0; i < line; i++){
        //printf("%s", data[i]);
        for (int j = 0; data[i][j] != '\0'; j++){

            // I know the exact lines the dev/video i need is on
            // and the exact device numbers checking for
            if (i == 4 || i == 9 || i == 14 || i == 19){
                if (data[i][j] == '0' || data[i][j] == '2' || data[i][j] == '4' || data[i][j] == '6'){
                    dev_nums[k] = data[i][j];
                    k++;
                }
            }
        }
    }
    dev_nums[k] = '\0';
    
    // front
    sprintf(
		pipeline_descs[0],
		"( v4l2src device=/dev/video%c is-live=true ! video/x-h264, width=800, height=600, framerate=30/1 ! \
		   h264parse ! rtph264pay name=pay0 pt=96 config-interval=1 )",
		 // front cam data stored at 2nd index of device output
		dev_nums[2]
	);
	
	// left
	sprintf(
		pipeline_descs[1],
		"( v4l2src device=/dev/video%c is-live=true ! image/jpeg, width=640, height=360, framerate=30/1 ! \
		   jpegparse ! rtpjpegpay name=pay0 pt=26 config-interval=1 )",
		 // left cam data stored at 1st index of device output
		dev_nums[1]
	);
	
	sprintf(
		pipeline_descs[2],
		"( v4l2src device=/dev/video%c is-live=true ! image/jpeg, width=640, height=360, framerate=30/1 ! \
		   jpegparse ! rtpjpegpay name=pay0 pt=26 config-interval=1 )",
		 // right cam data stored at 0th index of device output
		dev_nums[0]
	);
	
	sprintf(
		pipeline_descs[3],
		"( v4l2src device=/dev/video%c is-live=true ! image/jpeg, width=640, height=360, framerate=30/1 ! \
		   jpegparse ! rtpjpegpay name=pay0 pt=26 config-interval=1 )",
		 // back cam at last index
		dev_nums[3]
	);

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
    
    //printf("%c\n", dev_nums[0]);
    //printf("%c\n", dev_nums[1]);
    //printf("%c\n", dev_nums[2]);
    //printf("%c\n", dev_nums[3]);

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
