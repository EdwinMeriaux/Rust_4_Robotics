import java.util.*;

public class BresenhamAlgorithm {
    public static List<int[]> bresenhamLine(int x1, int y1, int x2, int y2) {
        List<int[]> points = new ArrayList<>();
        int dx = Math.abs(x2 - x1), dy = Math.abs(y2 - y1);
        int sx = (x1 < x2) ? 1 : -1, sy = (y1 < y2) ? 1 : -1;
        int err = dx - dy;

        while (true) {
            points.add(new int[]{x1, y1});
            if (x1 == x2 && y1 == y2) break;
            int e2 = 2 * err;
            if (e2 > -dy) { err -= dy; x1 += sx; }
            if (e2 < dx) { err += dx; y1 += sy; }
        }
        return points;
    }
}
