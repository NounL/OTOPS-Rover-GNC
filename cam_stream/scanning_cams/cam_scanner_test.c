#include<stdio.h>
#include<stdlib.h>

// Testing with file io as can't access devices

// To run: 
// gcc cam_scanner_test.c
// ./a.out

// usb port numbers unique to the specific port and don't change
// 1.4 = usb hub 1, port number 4 (the port furthest from the usb c port), plugged front in here
// 1.3 = left
// 1.2 = right
// 2.4 = back - but might be different if plugged into different port on jetson
// Ideal to set up like video0 will be h.264 front, video2 left, video4 right, video6 back

// Limit of how many lines in a file
#define MAX_LINES 100
// Limit of how long a line is 
#define LINE_LEN 256

int main(void) {
    // Only need the number in device/0, so want like [0,2,4,6] or whatever order
    char dev_nums[5];

    // Counting rows
    int line = 0;

    // counting indices on dev_nums
    int k = 0;


    // Stores data from command line
    char data[MAX_LINES][LINE_LEN];
    
    FILE *file;

    file = fopen("cam_data.txt", "r");
    if (file == NULL) {
        printf("Error opening file.\n");
        return 1;
    }

    while (!feof(file) && !ferror(file)){
        if (fgets(data[line], LINE_LEN, file) != NULL) {
            line++;
        }
    }
    fclose(file);

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
    // In teststream want to access like dev_nums
    printf("%c\n", dev_nums[0]);
    printf("%c\n", dev_nums[1]);
    printf("%c\n", dev_nums[2]);
    printf("%c\n", dev_nums[3]);
}