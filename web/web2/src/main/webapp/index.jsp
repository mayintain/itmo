<%@page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core"%> 

<!DOCTYPE html>
<html lang="ru">
<head> 
    <meta charset="UTF-8">
    <title> ЛР2 </title>

    <link rel="stylesheet" href="<c:url value='/styles.css' />">

</head> 
<body>
    <header> 
        <div class="fio"> ФИО: <b> Антонова Анна Игоревна </b>, 
        Группа <b> P3232 </b>,
        Вариант <b> 65548 </b> </div>
    </header> 


    <table class="layout">
        <tr>
            <td style="width:46%">
                <h3>Ввод данных</h3>

    <c:if test="${not empty error}">
        <div> ${error} </div>
    </c:if>

     <form id="point-form" method="post" action="<c:url value='/controller'/>">
        <div class="controls">
            <label> Значение Х: </label>
            <div id="x-buttons">
                <label class="btn x-btn">
                    <input type="radio" name="x" value="-5" required>
                    <span>-5</span>
                </label>

                <label class="btn x-btn">
                    <input type="radio" name="x" value="-4">
                    <span>-4</span>
                </label>

                <label class="btn x-btn">
                    <input type="radio" name="x" value="-3">
                    <span>-3</span>
                </label>

                <label class="btn x-btn">
                    <input type="radio" name="x" value="-2">
                    <span>-2</span>
                </label>

                <label class="btn x-btn">
                    <input type="radio" name="x" value="-1">
                    <span>-1</span>
                </label>

                <label class="btn x-btn">
                    <input type="radio" name="x" value="0">
                    <span>0</span>
                </label>

                <label class="btn x-btn">
                    <input type="radio" name="x" value="1">
                    <span>1</span>
                </label>

                <label class="btn x-btn">
                    <input type="radio" name="x" value="2">
                    <span>2</span>
                </label>

                <label class="btn x-btn">
                    <input type="radio" name="x" value="3">
                    <span>3</span>
                </label>
            </div>
        </div>

        <div style="margin-top:10px">
            <label>Y (−5 … 5): 
                <input id="y-input" type="text" name="y" placeholder="например, 1.25" required>
            </label>
        </div>

        <div style="margin-top:10px">
            <label>R (1 … 4): 
                <input id="r-input" type="text" name="r" placeholder="например, 1.25" value="${not empty last ? last.r : ''}" required>
            </label>
        </div>

        <div style="margin-top:12px">
            <button type="submit" class="check-btn">Проверить</button>
        </div>
    </form>

    
    <div class="canvas-wrap">
        <canvas id="area-canvas" width="380" height="380"></canvas>
    </div>

    </td>
        <td>
      <h3>История проверок</h3> 

    <c:choose>
        <c:when test="${empty results}">
            <p> Пока пусто </p>
        </c:when>
    <c:otherwise>
        <table id="history">
            <thead>
                <tr>
                    <th>#</th>
                    <th>X</th>
                    <th>Y</th>
                    <th>R</th>
                    <th>Попадание</th>
                </tr>
            </thead>
        <tbody>
            <c:forEach var="h" items="${results}" varStatus="s">
                <tr>
                    <td> ${s.index + 1} </td>
                    <td> ${h.x} </td>
                    <td> ${h.y} </td>
                    <td> ${h.r} </td>
                    <td> ${h.hit ? 'Да' : 'Нет'} </td>
                </tr>
            </c:forEach>
        </tbody>
        </table>

        <script> 
            window.allPoints = [ 
                <c:forEach var="h" items="${results}" varStatus="st">
                {
                    x: ${h.x}, 
                    y: ${h.y}, 
                    r: ${h.r}, 
                    hit: ${h.hit}
                }<c:if test="${!st.last}">,</c:if>
            </c:forEach>
            ];
        </script> 
    </c:otherwise>
    </c:choose>

<c:if test="${not empty last}">
    <script>
        window.lastPoint = {
            x: ${last.x},
            y: ${last.y},
            r: ${last.r},
            hit: ${last.hit}
        };
    </script>
</c:if>

    </td>
  </tr>
</table>

<script src="<c:url value='/script.js'/>"> </script>
</body>
</html>
