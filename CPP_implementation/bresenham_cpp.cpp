#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <thread>
#include <mutex>
#include <dirent.h>
#include <sys/stat.h>
#include <png.h>
#include <json/json.h>

#define MAX_PATH 1024
#define MAX_THREADS 32

int width, height;
std::mutex json_mutex;
Json::Value global_visibility_map;

struct ThreadArgs {
    std::vector<std::vector<uint8_t>> *binary_img;
    int start;
    int end;
};

std::vector<std::vector<uint8_t>> binarize_png_to_matrix(const std::string &filename) {
    FILE *fp = fopen(filename.c_str(), "rb");
    if (!fp) throw std::runtime_error("fopen failed");

    png_structp png = png_create_read_struct(PNG_LIBPNG_VER_STRING, nullptr, nullptr, nullptr);
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

    std::vector<png_bytep> rows(height);
    for (int y = 0; y < height; ++y)
        rows[y] = (png_bytep)malloc(png_get_rowbytes(png, info));
    png_read_image(png, rows.data());
    fclose(fp);

    std::vector<std::vector<uint8_t>> mat(height, std::vector<uint8_t>(width));
    for (int y = 0; y < height; ++y) {
        png_bytep row = rows[y];
        for (int x = 0; x < width; ++x) {
            png_bytep px = &row[x * 4];
            mat[y][x] = (px[0] == 255 && px[1] == 255 && px[2] == 255) ? 0 : 1;
        }
        free(row);
    }

    png_destroy_read_struct(&png, &info, nullptr);
    return mat;
}

bool bresenham_can_see(const std::vector<std::vector<uint8_t>> &binary, int x1, int y1, int x2, int y2) {
    int dx = abs(x2 - x1), dy = abs(y2 - y1);
    int sx = x1 < x2 ? 1 : -1, sy = y1 < y2 ? 1 : -1;
    int err = dx - dy;

    while (true) {
        if (x1 < 0 || y1 < 0 || x1 >= width || y1 >= height || binary[y1][x1] != 0) return false;
        if (x1 == x2 && y1 == y2) break;

        int e2 = 2 * err;
        if (e2 > -dy) { err -= dy; x1 += sx; }
        if (e2 < dx) { err += dx; y1 += sy; }
    }
    return true;
}

void thread_worker(ThreadArgs args) {
    auto &binary_img = *args.binary_img;

    for (int i = args.start; i < args.end; ++i) {
        int x = i % width;
        int y = i / width;

        std::string key = "(" + std::to_string(x) + ", " + std::to_string(y) + ")";
        Json::Value visible_list(Json::arrayValue);

        for (int x1 = 0; x1 < width; ++x1) {
            for (int y1 = 0; y1 < height; ++y1) {
                if (bresenham_can_see(binary_img, x, y, x1, y1)) {
                    Json::Value coord(Json::arrayValue);
                    coord.append(x1);
                    coord.append(y1);
                    visible_list.append(coord);
                }
            }
        }

        std::lock_guard<std::mutex> lock(json_mutex);
        global_visibility_map[key] = visible_list;
    }
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <num_threads>" << std::endl;
        return 1;
    }

    int numThreads = std::stoi(argv[1]);
    if (numThreads <= 0 || numThreads > MAX_THREADS) numThreads = 4;

    const std::string inputDir = "../dungeons_small";
    const std::string jsonOutputDir = "./json_output";
    mkdir(jsonOutputDir.c_str(), 0777);

    DIR *d = opendir(inputDir.c_str());
    struct dirent *entry;
    int totalFiles = 0;

    while ((entry = readdir(d))) {
        if (strstr(entry->d_name, ".png")) {
            std::string filePath = inputDir + "/" + entry->d_name;
            auto binary_img = binarize_png_to_matrix(filePath);

            global_visibility_map.clear();
            int num_points = width * height;
            int chunk_size = num_points / numThreads;

            std::vector<std::thread> threads;
            for (int i = 0; i < numThreads; ++i) {
                int start = i * chunk_size;
                int end = (i == numThreads - 1) ? num_points : (i + 1) * chunk_size;
                threads.emplace_back(thread_worker, ThreadArgs{&binary_img, start, end});
            }
            for (auto &t : threads) t.join();

            std::string jsonPath = jsonOutputDir + "/" + std::string(entry->d_name);
            jsonPath.replace(jsonPath.end() - 4, jsonPath.end(), ".json");

            std::ofstream fout(jsonPath);
            fout << global_visibility_map.toStyledString();
            fout.close();

            ++totalFiles;
        }
    }
    closedir(d);
    std::cout << "Processed " << totalFiles << " PNG files" << std::endl;
    return 0;
}