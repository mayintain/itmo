public class HitChecker {
    public static boolean isHit(double x, double y, double R) {
        boolean rect   = (x >= -R && x <= 0 && y >= 0 && y <= R/2.0);
        boolean circle = (x <= 0 && y <= 0 && (x*x + y*y) <= (R*R));
        boolean tri    = (x >= 0 && y >= 0 && y <= (-0.5 * x + R/2.0));
        return rect || circle || tri;
    }
}