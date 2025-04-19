import java.util.*;
public class VisibilityTask extends Thread {
    private int[][] matrix;
    private List<int[]> assignedPoints;
    private Map<String, List<int[]>> visibilityMap;

    public VisibilityTask(int[][] matrix, List<int[]> assignedPoints, Map<String, List<int[]>> visibilityMap) {
        this.matrix = matrix;
        this.assignedPoints = assignedPoints;
        this.visibilityMap = visibilityMap;
    }

    @Override
    public void run() {
        for (int[] point : assignedPoints) {
            int x1 = point[0], y1 = point[1];
            List<int[]> visiblePoints = new ArrayList<>();

            for (int[] target : assignedPoints) {
                int x2 = target[0], y2 = target[1];
                List<int[]> line = BresenhamAlgorithm.bresenhamLine(x1, y1, x2, y2);

                boolean obstructed = false;
                for (int[] p : line) {
                    if (matrix[p[1]][p[0]] == 1) { // Obstacle found
                        obstructed = true;
                        break;
                    }
                }
                if (!obstructed) {
                    visiblePoints.add(target);
                }
            }
            synchronized (visibilityMap) { // Synchronize updates to shared data
                visibilityMap.put(Arrays.toString(point), visiblePoints);
            }
        }
    }
}
