package back;

public class HitBean {
    private double x;
    private double y;
    private double r;
    private boolean hit;

    public HitBean() {}

    public HitBean(double x, double y, double r, boolean hit) {
        this.x = x; 
        this.y = y; 
        this.r = r; 
        this.hit = hit;
    }

    public static boolean computeHit(double x, double y, double r) {
        double h = r / 2.0;

        boolean inSector = (x <= 0) && (y >= 0) && (x*x + y*y <= r*r);
        boolean inRect   = (x >= 0) && (y <= 0) && (x <= r) && (-h <= y);
        boolean inTri    = (x <= 0) && (y <= 0) && (x + y >= -h);

        return inSector || inRect || inTri;
    }

    public double getX() { return x; }
    public double getY() { return y; }
    public double getR() { return r; }
    public boolean isHit() { return hit; }
 
    public void setX(double x) { this.x = x; }
    public void setY(double y) { this.y = y; }
    public void setR(double r) { this.r = r; }
    public void setHit(boolean hit) { this.hit = hit; }

}