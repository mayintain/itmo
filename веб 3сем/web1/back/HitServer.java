import com.fastcgi.FCGIInterface;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.*;

public class HitServer {

    private static double msSince(long t0) { return (System.nanoTime() - t0) / 1_000_000.0; }

    public static void main(String[] args) {
        FCGIInterface fcgi = new FCGIInterface();

        while (fcgi.FCGIaccept() >= 0) {
            long t0 = System.nanoTime();

            Map<String,Object> payload = new LinkedHashMap<>();
            int statusCode = 200;
            String statusText = "OK";

            try {
                RequestParser parser = new RequestParser();
                Map<String,String> form = parser.parseInput();

                String action = form.getOrDefault("action", "check");

                if ("history".equals(action)) {
                    payload = Map.of("history", HistoryStorage.snapshot());
                } else if ("clear".equals(action)) {
                    HistoryStorage.clear();
                    payload = Map.of("cleared", true);
                } else { 
                    int    x = parser.parseX(form);  
                    double y = parser.parseY(form);  
                    double r = parser.parseR(form); 

                    boolean hit = HitChecker.isHit(x, y, r);

                    Map<String,Object> row = new LinkedHashMap<>();
                    row.put("x", x);
                    row.put("y", y);
                    row.put("r", r);
                    row.put("hit", hit);
                    row.put("serverTime", new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()));
                    row.put("scriptTimeMs", msSince(t0));

                    HistoryStorage.add(row);
                    payload = row;
                }

            } catch (Exception e) {
                statusCode = 400;
                statusText = "Bad Request";
                payload = Map.of("error", e.getMessage(), "scriptTimeMs", msSince(t0));
            }

            byte[] bodyBytes = JsonUtil.toJson(payload).getBytes(StandardCharsets.UTF_8);
            System.out.print("Status: " + statusCode + " " + statusText + "\r\n");
            System.out.print("Content-Type: application/json; charset=utf-8\r\n");
            System.out.print("Content-Length: " + bodyBytes.length + "\r\n");
            System.out.print("\r\n");
            System.out.write(bodyBytes, 0, bodyBytes.length);
            System.out.flush();
        }
    }
}