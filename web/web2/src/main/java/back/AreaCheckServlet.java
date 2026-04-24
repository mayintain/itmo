package back;

import jakarta.servlet.*;
import jakarta.servlet.annotation.*;
import jakarta.servlet.http.*;
import java.io.IOException;

@WebServlet("/area-check")
public class AreaCheckServlet extends HttpServlet {

    @Override 
    protected void doPost(HttpServletRequest req, HttpServletResponse res)
        throws ServletException, IOException {

            String sx = req.getParameter("x");
            String sy = req.getParameter("y");
            String sr = req.getParameter("r");

            if (sx == null || sy == null || sr == null) {
                req.setAttribute("error", "Отсутствуют параметры X, Y, R");
                req.getRequestDispatcher("/index.jsp").forward(req, res);
                return;
            } 

            double x, y, r; 
            try {
                x = Double.parseDouble(sx);
                y = Double.parseDouble(sy);
                r = Double.parseDouble(sr);
            } catch (NumberFormatException e) {
                req.setAttribute("error", "Параметры должны быть числами"); 
                req.getRequestDispatcher("/index.jsp").forward(req, res);
                return;
            }

            boolean inRange = x >= -5 && x <= 3 && y>= -5 && y <= 5 && r >= 1 && r <= 4;
            if (!inRange) {
                req.setAttribute("error", "Значения вне диапазона");
                req.getRequestDispatcher("/index.jsp").forward(req, res);
                return;
            }

            boolean hit = HitBean.computeHit(x, y, r);
            
            HitBean hitBean = new HitBean(x, y, r, hit);
            ResultsBean.getInstance().add(hitBean);


            req.setAttribute("x", x);
            req.setAttribute("y", y);
            req.setAttribute("r", r);
            req.setAttribute("hit", hit);
            
            req.setAttribute("last", hitBean);
            req.setAttribute("results", ResultsBean.getInstance().getAll());

            req.getRequestDispatcher("/results.jsp").forward(req, res);

    
        }

}