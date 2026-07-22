// Olly Love
// Scans cameras and stores there number to get around issue where new device number given each reboot
// This code will be at the top of the rtsp stream

#include<stdio.h>
#include<stdlib.h>

// To run: 
// gcc cam_scanner.c
// ./a.out

// usb port numbers unique to the specific port and don't change
// 1.4 = usb hub 1, port number 4 (the port furthest from the usb c port), plugged front in here
// 1.3 = left
// 1.2 = right
// 2.4 = back - but might be different if plugged into different port on jetson
// Ideal to set up like video0 will be h.264 front, video2 left, video4 right, video6 back

// Limit of how long a line is 
#define MAX_LINES 100
#define LINE_LEN 256

int main(void) {
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

    // Matches example [2,4,6,0] - will be different order (dynamic) upon each jetson reboot
    printf("%c\n", dev_nums[0]);
    printf("%c\n", dev_nums[1]);
    printf("%c\n", dev_nums[2]);
    printf("%c\n", dev_nums[3]);
}