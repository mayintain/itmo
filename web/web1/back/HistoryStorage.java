import java.util.*;

public class HistoryStorage {
    private static final List<Map<String,Object>> HISTORY =
            Collections.synchronizedList(new ArrayList<>());

    public static void add(Map<String,Object> row) {
        HISTORY.add(row);
    }

    public static List<Map<String,Object>> snapshot() {
        synchronized (HISTORY) {
            return new ArrayList<>(HISTORY);
        }
    }

    public static void clear() {
        HISTORY.clear();
    }
}