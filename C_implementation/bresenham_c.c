#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <dirent.h>
#include <png.h>
#include <stdint.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <json-c/json.h>

#define MAX_PATH 1024
#define MAX_THREADS 32

int width, height;

typedef struct {
    uint8_t **binary_img;
    int start;
    int end;
} ThreadArgs;

json_object *global_visibility_map;
pthread_mutex_t json_mutex = PTHREAD_MUTEX_INITIALIZER;

uint8_t** binarize_png_to_matrix(const char *filename) {
    FILE *fp = fopen(filename, "rb");

    png_structp png = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    png_infop info = png_create_info_struct(png);
    png_init_io(png, fp);
    png_read_info(png, info);

    width = png_get_image_width(png, info);
    height = png_get_image_height(png, info);

    png_set_strip_16(png);
    png_set_palette_to_rgb(png);
    png_set_expand_gray_1_2_4_to_8(png);
    png_set_tRNS_to_alpha(png);
    png_set_gray_to_rgb(png);                   // <- Important for grayscale!
    png_set_filler(png, 0xFF, PNG_FILLER_AFTER); // <- Guarantees 4 channels (RGBA)


    png_read_update_info(png, info);

    png_bytep *rows = malloc(height * sizeof(png_bytep));
    for (int y = 0; y < height; y++)
        rows[y] = malloc(png_get_rowbytes(png, info));
    png_read_image(png, rows);
    fclose(fp);

    uint8_t **mat = malloc(height * sizeof(uint8_t *));
    for (int y = 0; y < height; y++) {
        mat[y] = malloc(width);
        png_bytep row = rows[y];

        for (int x = 0; x < width; x++) {
            png_bytep px = &row[x * 4];
            //printf("px[0]: %d, px[1]: %d, px[2]: %d\n", px[0], px[1], px[2]);
            mat[y][x] = (px[0] == 255 && px[1] == 255 && px[2] == 255) ? 0 : 1;
        }
        free(row);
    }

    free(rows);
    png_destroy_read_struct(&png, &info, NULL);
    return mat;
}

int bresenham_can_see(uint8_t **binary, int x1, int y1, int x2, int y2) {
    int dx = abs(x2 - x1), dy = abs(y2 - y1);
    int sx = x1 < x2 ? 1 : -1, sy = y1 < y2 ? 1 : -1;
    int err = dx - dy;

    while (1) {
        if (x1 < 0 || y1 < 0 || x1 >= width || y1 >= height) return 0;
        if (binary[y1][x1] != 0) return 0;
        if (x1 == x2 && y1 == y2) break;

        int e2 = 2 * err;
        if (e2 > -dy) { err -= dy; x1 += sx; }
        if (e2 < dx) { err += dx; y1 += sy; }
    }
    return 1;
}

void* thread_worker(void *arg) {
    ThreadArgs *args = (ThreadArgs *)arg;
    uint8_t **binary_img = args->binary_img;
    int start = args->start;
    int end = args->end;

    for (int i = start; i < end; i++) {
        int x = i % width;
        int y = i / width;

        // Pre-initialize every point with empty list
        char key[32];
        snprintf(key, sizeof(key), "(%d, %d)", x, y);
        json_object *visible_list = json_object_new_array();

        pthread_mutex_lock(&json_mutex);
        json_object_object_add(global_visibility_map, key, visible_list);
        pthread_mutex_unlock(&json_mutex);

        for (int x1 = 0; x1 < width; x1++) {
            for (int y1 = 0; y1 < height; y1++) {

                if (binary_img[y1][x1] == 0 && bresenham_can_see(binary_img, x, y, x1, y1)) {
                    json_object *coord = json_object_new_array();
                    json_object_array_add(coord, json_object_new_int(x1));
                    json_object_array_add(coord, json_object_new_int(y1));

                    pthread_mutex_lock(&json_mutex);
                    json_object_array_add(visible_list, coord);
                    pthread_mutex_unlock(&json_mutex);
                }
            }
        }
    }
    return NULL;
}


int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <num_threads>\n", argv[0]);
        return 1;
    }

    int numThreads = atoi(argv[1]);
    if (numThreads <= 0 || numThreads > MAX_THREADS) numThreads = 4;

    const char *inputDir = "../dungeons_medium";
    const char *jsonOutputDir = "./json_output";
    mkdir(jsonOutputDir, 0777);

    DIR *d = opendir(inputDir);
    struct dirent *entry;
    int totalFiles = 0;

    while ((entry = readdir(d))) {
        if (strstr(entry->d_name, ".png")) {
            char filePath[MAX_PATH];
            snprintf(filePath, sizeof(filePath), "%s/%s", inputDir, entry->d_name);

            uint8_t **binary_img = binarize_png_to_matrix(filePath);

            if (!binary_img) continue;

            pthread_t threads[MAX_THREADS];
            global_visibility_map = json_object_new_object();

            int num_points = width * height;
            int chunk_size = num_points / numThreads;

            for (int i = 0; i < numThreads; i++) {
                int start = i * chunk_size;
                int end = (i == numThreads - 1) ? num_points : (i + 1) * chunk_size;

                //printf("Thread %d processing points %d to %d\n", i, start, end);

                ThreadArgs *args = malloc(sizeof(ThreadArgs));
                args->binary_img = binary_img;
                args->start = start;
                args->end = end;
                pthread_create(&threads[i], NULL, thread_worker, args);
            }

            for (int i = 0; i < numThreads; i++)
                pthread_join(threads[i], NULL);

            // Output JSON file
            char jsonPath[MAX_PATH];
            snprintf(jsonPath, sizeof(jsonPath), "%s/%s", jsonOutputDir, entry->d_name);
            jsonPath[strlen(jsonPath) - 4] = '\0'; // remove .png
            strcat(jsonPath, ".json");

            FILE *fout = fopen(jsonPath, "w");
            if (fout) {
                fputs(json_object_to_json_string_ext(global_visibility_map, JSON_C_TO_STRING_PRETTY), fout);
                fclose(fout);
            } else {
                perror("Failed to write JSON file");
            }

            json_object_put(global_visibility_map);
            totalFiles++;
        }
    }

    closedir(d);
    printf("Processed %d PNG files\n", totalFiles);
    return 0;
}
