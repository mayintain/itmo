import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpExchange;
import java.io.*;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.*;

public class LocalServer {

    private static final Set<Integer> X_ALLOWED = new HashSet<>(Arrays.asList(-3,-2,-1,0,1,2,3,4,5));
    private static final Set<Double>  R_ALLOWED = new HashSet<>(Arrays.asList(1.0,1.5,2.0,2.5,3.0));

    private static final List<Map<String,Object>> HISTORY =
            Collections.synchronizedList(new ArrayList<>());

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 8081), 0);
        server.createContext("/api/point", LocalServer::handlePoint);
        System.out.println("Local API running at http://127.0.0.1:8081/api/point");
        server.start();
    }

    private static void handlePoint(HttpExchange ex) throws IOException {
        long t0 = System.nanoTime();
        Map<String,Object> result = new LinkedHashMap<>();
        result.put("serverTime", new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()));

        ex.getResponseHeaders().add("Access-Control-Allow-Origin", "*");
        ex.getResponseHeaders().add("Access-Control-Allow-Headers", "Content-Type");
        ex.getResponseHeaders().add("Content-Type", "application/json; charset=UTF-8");
        if ("OPTIONS".equalsIgnoreCase(ex.getRequestMethod())) { ex.sendResponseHeaders(204, -1); return; }

        try {
            if (!"POST".equalsIgnoreCase(ex.getRequestMethod()))
                throw new IllegalArgumentException("Use POST");

            String body = new String(ex.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            Map<String,String> form = parseUrlEncoded(body);

            String action = form.getOrDefault("action", "check");

            if ("history".equals(action)) {
                // вернуть всю историю
                Map<String,Object> resp = new LinkedHashMap<>();
                synchronized (HISTORY) {
                    resp.put("history", new ArrayList<>(HISTORY));
                }
                writeJson(ex, 200, resp, t0);
                return;
            }

            if ("clear".equals(action)) {
                HISTORY.clear();
                Map<String,Object> resp = Map.of("cleared", true);
                writeJson(ex, 200, resp, t0);
                return;
            }

            int x = Integer.parseInt(req(form,"x"));
            double y = Double.parseDouble(req(form,"y").replace(',', '.'));
            double r = Double.parseDouble(req(form,"r").replace(',', '.'));

            if (!X_ALLOWED.contains(x))         throw new IllegalArgumentException("X not allowed");
            if (!(y > -3 && y < 5))             throw new IllegalArgumentException("Y out of range (-3,5)");
            if (!R_ALLOWED.contains(roundR(r))) throw new IllegalArgumentException("R not allowed");

            boolean hit = isHit(x, y, r);

            Map<String,Object> entry = new LinkedHashMap<>();
            entry.put("x", x);
            entry.put("y", y);
            entry.put("r", r);
            entry.put("hit", hit);
            entry.put("serverTime", result.get("serverTime"));
            entry.put("scriptTimeMs", msSince(t0));

            HISTORY.add(entry);

            writeJson(ex, 200, entry, t0);

        } catch (Exception e) {
            Map<String,Object> err = new LinkedHashMap<>();
            err.put("error", e.getMessage());
            err.put("scriptTimeMs", msSince(t0));
            writeJson(ex, 200, err, t0); 
        }
    }

   
   private static boolean isHit(double x, double y, double R) {
    // Q2: прямоугольник слева-сверху
    boolean rect = (x >= -R && x <= 0 && y >= 0 && y <= R/2.0);

    // Q3: четверть круга снизу-слева
    boolean circle = (x <= 0 && y <= 0 && (x*x + y*y) <= R*R);

    // Q1: треугольник справа-сверху (ограничение y <= -0.5*x + R/2)
    boolean tri = (x >= 0 && y >= 0 && y <= (-0.5 * x + R/2.0));

    return rect || circle || tri;
}


    private static String req(Map<String,String> m, String k){
        String v = m.get(k);
        if (v == null || v.isEmpty()) throw new IllegalArgumentException("Missing " + k);
        return v;
    }
    private static Map<String,String> parseUrlEncoded(String s) throws UnsupportedEncodingException {
        Map<String,String> map = new HashMap<>();
        if (s == null || s.isEmpty()) return map;
        for (String part : s.split("&")) {
            int eq = part.indexOf('=');
            if (eq >= 0) {
                String key = URLDecoder.decode(part.substring(0,eq), "UTF-8");
                String val = URLDecoder.decode(part.substring(eq+1), "UTF-8");
                map.put(key, val);
            }
        }
        return map;
    }
    private static Double roundR(double r){ return Math.round(r*2.0)/2.0; }

    private static double msSince(long t0) {
        return (System.nanoTime() - t0) / 1_000_000.0; 
    }

    private static void writeJson(HttpExchange ex, int status, Map<String,Object> obj, long t0) throws IOException {
        byte[] payload = toJson(obj).getBytes(StandardCharsets.UTF_8);
        ex.sendResponseHeaders(status, payload.length);
        try (OutputStream os = ex.getResponseBody()) { os.write(payload); }
    }


    private static String toJson(Object v) {
        if (v == null) return "null";
        if (v instanceof Number || v instanceof Boolean) return v.toString();
        if (v instanceof Map<?,?> m) {
            StringBuilder sb = new StringBuilder("{");
            boolean first = true;
            for (var e : m.entrySet()) {
                if (!first) sb.append(',');
                first = false;
                sb.append('"').append(escape(e.getKey().toString())).append("\":").append(toJson(e.getValue()));
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