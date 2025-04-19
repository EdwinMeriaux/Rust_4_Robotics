import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.util.*;
import javax.imageio.ImageIO;
import org.json.JSONObject;
import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {

    static int[][] binarizeImage(BufferedImage img) {
        int width = img.getWidth();
        int height = img.getHeight();
        int[][] matrix = new int[height][width];

        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int rgb = img.getRGB(x, y);
                int gray = (rgb >> 16) & 0xFF; // Convert to grayscale
                matrix[y][x] = (gray < 128) ? 1 : 0; // Binary threshold
            }
        }
        return matrix;
    }

    static List<int[]> getAllPoints(int[][] matrix) {
        List<int[]> points = new ArrayList<>();
        for (int y = 0; y < matrix.length; y++) {
            for (int x = 0; x < matrix[y].length; x++) {
                points.add(new int[]{x, y});
            }
        }
        return points;
    }

    public static void main(String[] args) throws IOException {
        File dir = new File("src/dungeons_medium");
        File[] files = dir.listFiles((d, name) -> name.endsWith(".png"));

        if (files == null || files.length == 0) {
            System.err.println("No images found!");
            return;
        }

        Map<String, List<int[]>> finalVisibilityMap = Collections.synchronizedMap(new HashMap<>());
        List<Thread> threads = new ArrayList<>();

        for (File file : files) {
            BufferedImage img = ImageIO.read(file);
            int[][] matrix = binarizeImage(img);
            List<int[]> allPoints = getAllPoints(matrix);

            int chunkSize = allPoints.size() / 4; // Divide work among 4 threads
            for (int i = 0; i < 4; i++) {
                int start = i * chunkSize;
                int end = Math.min(start + chunkSize, allPoints.size());
                Thread thread = new VisibilityTask(matrix, allPoints.subList(start, end), finalVisibilityMap);
                threads.add(thread);
                thread.start();
            }
        }

        // Wait for all threads to finish
        for (Thread thread : threads) {
            try {
                thread.join();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }

        // Save results to JSON
        // Ensure 'json' directory exists before writing the output file
        JSONObject json = new JSONObject(finalVisibilityMap);

        File jsonDir = new File("json");
        if (!jsonDir.exists()) {
            jsonDir.mkdir(); // Create the directory if it doesn't exist
            System.out.println("'json' directory created.");
        }

        try {
            // Write JSON file inside the 'json/' folder
            Files.write(Paths.get("json/visibility_output.json"), json.toString(4).getBytes());
            System.out.println("JSON file successfully saved in 'json' directory!");
        } catch (IOException e) {
            System.err.println("Error saving JSON: " + e.getMessage());
        }

    }
}
