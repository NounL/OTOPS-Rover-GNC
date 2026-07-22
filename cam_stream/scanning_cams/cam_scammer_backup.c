#include<stdio.h>
#include<stdlib.h>

// To run: 
// gcc cam_scanner.c
// ./a.out

// Limit of how long a line is 
#define MAX_LINES 100
#define LINE_LEN 256

int main(void) {
    FILE *output;
    //char buffer[LINE_LEN];
    char usb_num[4];

    char usb_nums_arr[4][4];
    // 12 fits /dev/video0 and /0
    // important lines stored at row index 4, 9, 14, 19
    char dev_nums_arr[4][12];

    // Counting rows
    int line = 0;

    // counting indices on usb_nums_arr and dev_nums_arr
    int k = 0;

    int dev_col = 0;

    char data[MAX_LINES][LINE_LEN];

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
        while (fgets(data[line], LINE_LEN, output) != NULL) {
            // gets how many lines there are
            line++;
            // // This prints the whole output
            // //printf("%s", buffer);
            
            // // Want to look for usb-1 or usb-2 and store everything till the )

            // // Iterate through each char in the output
            // for (int i = 0; buffer[i] != '\0'; i++) {

            //     // %d for int and %c for char
            //     //printf("Character %d: %c\n", i, buffer[i]);

            //     // when ( encounterd after 17 chars there is the specific usb number needed)
            //     // Gonna add here like if j = 3, 8, 13, 18
            //     if (buffer[i] == '(') {

            //         usb_nums_arr[k][0] = buffer[i+17];
            //         usb_nums_arr[k][1] = buffer[i+18];
            //         usb_nums_arr[k][2] = buffer[i+19];
            //         usb_nums_arr[k][3] = '\0';
            //     }
                
            //     // row 4, 9, 14 and 19 store the device lines i want
            //     if (line == 1 || line == 9 || line == 14 || line == 19) {
            //         dev_nums_arr[k][i] = buffer[i];
            //         //dev_nums_arr[k][1] = buffer[i+1];
            //     }
            //}
        }
    }
    pclose(output);

    // Iterating over every line in the output
    // then every column (every individual char)
    for (int i = 0; i < line; i++){
        
        for (int j = 0; data[i][j] != '\0'; j++)
        {

            if (data[i][j] == '('){
                usb_nums_arr[k][0] = data[i][j+17];
                usb_nums_arr[k][1] = data[i][j+18];
                usb_nums_arr[k][2] = data[i][j+19];
                usb_nums_arr[k][3] = '\0';
            }

            
            //printf("%c", data[i][j]);

            if (i == 1 || i == 9 || i == 14 || i == 19) {
                // dev_nums_arr[k][dev_col] = data[i][j];
                // dev_col++;
                if (data[i][j] != ' '){
                    printf("%s", data[i]);
                    dev_nums_arr[k][dev_col] = data[i][j];
                    dev_col++;
                    
                    //dev_nums_arr[k][1] = buffer[i+1];
                }
                
            }
        }
        k++;
        dev_nums_arr[k][dev_col] = '\0';
        dev_col = 0;
        //printf("%s", data[i]);
    }

    printf("%s", dev_nums_arr[0]);
}