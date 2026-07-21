#include<stdio.h>
#include<stdlib.h>

// To run: 
// gcc cam_scanner.c
// ./a.out

int main(void) {
    FILE *output;
    char buffer[256];
    char usb_num[4];
    char usb_nums_arr[4][4];
    // Whichever is at video 0 will be h.264 front, video2 left, video4 right, video6 back
    // v4l2-ctl --list-devices - when scanning and plugged in how we want, h264 webcam is always usb-1.4 despite port changing
    // when find 1.4 next line will have /dev/video0 or /dev/video6, want this line
    // 1.4 is front, 1.3 is left, 1.2 is right, 2.4 is back (but this may change after arduino added)
    // v4l2-ctl --list-formats-ext --device /dev/video0
    // Execute linux terminal command
    // popen returns FILE *
    output = popen("v4l2-ctl --list-devices", "r");

    if (output == NULL) {
        fputs("POPEN: Failed to execute command.\n", stderr);
    }
    else {
        // Reads one line at a time
        while (fgets(buffer, sizeof(buffer), output) != NULL) {
            // This prints the whole output
            printf("%s", buffer);
            
            // Want to look for usb-1 or usb-2 and store everything till the )


            // Iterate through each char in the output
            for (int i = 0; buffer[i] != '\0'; i++) {
                // %d for int and %c for char
                //printf("Character %d: %c\n", i, buffer[i]);
                // when ( encounterd after 17 chars there is the specific usb number needed)
                if (buffer[i] == '(') {
                    usb_num[0] = buffer[i+17];
                    usb_num[1] = buffer[i+18];
                    usb_num[2] = buffer[i+19];
                    // null terminator need for some reason
                    usb_num[3] = '\0';
                }
            }
        }
    }
    pclose(output);

    printf("%s\n", usb_num);
}