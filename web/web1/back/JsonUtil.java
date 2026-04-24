import java.util.*;

public class JsonUtil {
    public static String toJson(Object v) {
        if (v == null) return "null";
        if (v instanceof Number || v instanceof Boolean) return v.toString();

        if (v instanceof Map<?,?> m) {
            StringBuilder sb = new StringBuilder("{");
            boolean first = true;
            for (var e : m.entrySet()) {
                if (!first) sb.append(',');
                first = false;
                sb.append('"').append(escape(e.getKey().toString())).append("\":")
                  .append(toJson(e.getValue()));
            }
            sb.append('}');
            return sb.toString();
        }
        if (v instanceof Collection<?> col) {
            StringBuilder sb = new StringBuilder("[");
            boolean first = true;
            for (var it : col) {
                if (!first) sb.append(',');
                first = false;
                sb.append(toJson(it));
            }
            sb.append(']');
            return sb.toString();
        }
        return "\"" + escape(v.toString()) + "\"";
    }

    private static String escape(String s){
        return s.replace("\\","\\\\").replace("\"","\\\"");
    }
}