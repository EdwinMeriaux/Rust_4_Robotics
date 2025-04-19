import org.json.JSONArray;
import org.json.JSONObject;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.FileWriter;
import java.nio.file.*;
import java.util.concurrent.*;

public class bresenham_java {
    static int width, height;
    static final JSONObject globalVisibilityMap = new JSONObject();
    static final Object lock = new Object();

    public static int[][] binarizeImage(File file) throws Exception {
        BufferedImage img = ImageIO.read(file);
        width = img.getWidth();
        height = img.getHeight();

        int[][] matrix = new int[height][width];
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int rgb = img.getRGB(x, y);
                int r = (rgb >> 16) & 0xFF;
                int g = (rgb >> 8) & 0xFF;
                int b = rgb & 0xFF;
                matrix[y][x] = (r == 255 && g == 255 && b == 255) ? 0 : 1;
            }
        }
        return matrix;
    }

    public static boolean bresenhamCanSee(int[][] binary, int x1, int y1, int x2, int y2) {
        int dx = Math.abs(x2 - x1), dy = Math.abs(y2 - y1);
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

    public static void worker(int[][] binary, int start, int end) {
        for (int i = start; i < end; i++) {
            int x = i % width;
            int y = i / width;
            JSONArray visibleList = new JSONArray();

            for (int x1 = 0; x1 < width; x1++) {
                for (int y1 = 0; y1 < height; y1++) {
                    if (binary[y1][x1] == 0 && bresenhamCanSee(binary, x, y, x1, y1)) {
                        JSONArray coord = new JSONArray();
                        coord.put(x1);
                        coord.put(y1);
                        visibleList.put(coord);
                    }
                }
            }

            synchronized (lock) {
                globalVisibilityMap.put("(" + x + ", " + y + ")", visibleList);
            }
        }
    }

    public static void main(String[] args) throws Exception {
        int numThreads = args.length >= 1 ? Integer.parseInt(args[0]) : 4;
        String inputDir = "../../dungeons_small";
        String outputDir = "json_output";
        Files.createDirectories(Paths.get(outputDir));

        try (DirectoryStream<Path> stream = Files.newDirectoryStream(Paths.get(inputDir), "*.png")) {
            for (Path path : stream) {
                int[][] binary = binarizeImage(path.toFile());
                globalVisibilityMap.clear();

                int total = width * height;
                int chunk = total / numThreads;

                ExecutorService pool = Executors.newFixedThreadPool(numThreads);
                for (int i = 0; i < numThreads; i++) {
                    int start = i * chunk;
                    int end = (i == numThreads - 1) ? total : (i + 1) * chunk;
                    pool.execute(() -> worker(binary, start, end));
                }

                pool.shutdown();
                pool.awaitTermination(10, TimeUnit.MINUTES);

                String jsonName = path.getFileName().toString().replace(".png", ".json");
                try (FileWriter writer = new FileWriter(outputDir + "/" + jsonName)) {
                    writer.write(globalVisibilityMap.toString(2)); // Pretty print with 2 spaces
                }
            }
        }

        System.out.println("Done");
    }
}