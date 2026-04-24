import java.io.UnsupportedEncodingException;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.*;

public class RequestParser {

    private static final Set<Integer> X_ALLOWED =
            new HashSet<>(Arrays.asList(-5,-4,-3,-2,-1,0,1,2,3));
    private static final Set<Double> R_ALLOWED =
            new HashSet<>(Arrays.asList(1.0,2.0,3.0,4.0,5.0));

    public Map<String,String> parseInput() throws Exception {
        int contentLen = parseInt(System.getenv("CONTENT_LENGTH"), 0);
        byte[] buf = new byte[Math.max(contentLen, 0)];
        int off = 0;
        while (off < contentLen) {
            int n = System.in.read(buf, off, contentLen - off);
            if (n < 0) break;
            off += n;
        }
        String body = new String(buf, 0, off, StandardCharsets.UTF_8);
        return parseUrlEncoded(body);
    }

    public Map<String,String> parseUrlEncoded(String s) throws UnsupportedEncodingException {
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

    public int parseX(Map<String,String> form) {
        String xs = require(form, "x");
        int x = Integer.parseInt(xs);
        if (!X_ALLOWED.contains(x)) throw new IllegalArgumentException("X not allowed");
        return x;
    }

    public double parseY(Map<String,String> form) {
        String yRaw = require(form, "y").replace(',', '.');

        int dot = yRaw.indexOf('.');
        if (dot >= 0) {
            String frac = yRaw.substring(dot + 1);
            if (frac.length() > 8) {
                throw new IllegalArgumentException("Слишком много знаков после запятой у Y (макс. 8)");
            }
        }

        double y = Double.parseDouble(yRaw);
        if (!(y > -3 && y < 3)) {
            throw new IllegalArgumentException("Y out of range (-3,3)");
        }
        return y;
    }

    public double parseR(Map<String,String> form) {
        String rs = require(form, "r").replace(',', '.');
        double r = Double.parseDouble(rs);
        if (!R_ALLOWED.contains(r)) throw new IllegalArgumentException("R not allowed");
        return r;
    }

    private static String require(Map<String,String> m, String k){
        String v = m.get(k);
        if (v == null || v.isEmpty()) throw new IllegalArgumentException("Missing " + k);
        return v;
    }

    private static int parseInt(String s, int def) {
        try {
            if (s == null || s.trim().isEmpty()) return def;
            return Integer.parseInt(s.trim());
        } catch (Exception e) { return def; }
    }
}