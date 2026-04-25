package back; 

import jakarta.servlet.*;
import jakarta.servlet.http.*;
import jakarta.servlet.annotation.*;
import java.io.IOException;

@WebServlet("/controller")
public class ControllerServlet extends HttpServlet {

    @Override
        protected void doGet(HttpServletRequest req, HttpServletResponse res)
            throws ServletException, IOException {

            var all = ResultsBean.getInstance().getAll();
            req.setAttribute("results", all);

            if (!all.isEmpty()) {
                req.setAttribute("last", all.get(all.size()-1));
            }

                req.getRequestDispatcher("/index.jsp").forward(req, res);
            }


    @Override
        protected void doPost(HttpServletRequest req, HttpServletResponse res)
            throws ServletException, IOException {

                String x = req.getParameter("x");
                String y = req.getParameter("y");
                String r = req.getParameter("r");

                if (x == null || y == null || r == null) {
                    req.setAttribute("error", "Нужно заполнить X, Y, R");
                    req.getRequestDispatcher("/index.jsp").forward(req, res);
                } else {
                    req.getRequestDispatcher("/area-check").forward(req, res);
                }

            }
}