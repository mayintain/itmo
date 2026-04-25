<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>

<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Результат проверки</title>

    <style>
        html, body {
            height: 100%;
            margin: 0;
        }

        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: linear-gradient(145deg, #4CA9DF, #292E91);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 22px;
            padding: 26px 30px 28px;
            box-shadow: 0 14px 35px rgba(0, 0, 0, 0.25);
            max-width: 460px;
            width: calc(100% - 32px);
            box-sizing: border-box;
            text-align: center;
            backdrop-filter: blur(12px);
        }

        h2 {
            margin: 0 0 18px;
            font-size: 22px;
            letter-spacing: 0.4px;
        }

        #result-table {
            width: 100%;
            border-collapse: collapse;
            margin: 0 auto 20px;
            border-radius: 20px;
            overflow: hidden;
            background: linear-gradient(
                    135deg,
                    rgba(255,255,255,0.9),
                    rgba(230,240,255,0.8)
            );
            box-shadow:
                0 4px 12px rgba(0, 0, 0, 0.18),
                inset 0 1px 3px rgba(255, 255, 255, 0.6);
        }

        #result-table th,
        #result-table td {
            border: 1px solid rgba(180, 180, 200, 0.45);
            padding: 9px 14px;
            text-align: center;
        }

        #result-table th {
            background: linear-gradient(135deg, #dbeafe, #bfdcff);
            color: #1e3a8a;
            text-shadow: 0 1px 2px rgba(255,255,255,0.6);
            font-weight: 700;
            font-size: 14px;
        }

        #result-table tr:hover td {
            background: linear-gradient(
                    135deg,
                    rgba(173,216,255,0.85),
                    rgba(255,255,255,0.9)
            );
        }

        .hit  { color: #16a34a; font-weight: 700; }
        .miss { color: #dc2626; font-weight: 700; }

        .btn-back {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border: none;
            border-radius: 40px;
            padding: 10px 18px;
            font-size: 14px;
            font-weight: 600;
            color: #fff;
            text-decoration: none;
            cursor: pointer;
            background: linear-gradient(145deg, #0f172a, #1e3a8a, #3b82f6);
            box-shadow: 0 3px 10px rgba(15, 23, 42, 0.6);
            transition: all 0.25s ease;
            margin-top: 4px;
        }

        .btn-back:hover {
            background: linear-gradient(135deg, #1e3a8a, #3b82f6);
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(30,64,175,0.7);
            filter: brightness(1.07);
        }

        .btn-back:active {
            transform: translateY(0);
            box-shadow: 0 2px 6px rgba(30,64,175,0.5);
            filter: brightness(0.96);
        }

        .btn-back .icon {
            font-size: 16px;
        }

        .gif-block {
            margin-top: 18px;
            display: flex;
            justify-content: center;
        }

        .gif-image {
            max-width: 260px;
            width: 100%;
            border-radius: 20px;
            box-shadow:
                0 8px 20px rgba(0,0,0,0.25),
                0 0 0 1px rgba(255,255,255,0.6);
            display: block;
        }
    </style>
</head>
<body>

<div class="card">
    <h2>Результат проверки точки</h2>

    <table id="result-table">
        <tr>
            <th>X</th>
            <td>${x}</td>
        </tr>
        <tr>
            <th>Y</th>
            <td>${y}</td>
        </tr>
        <tr>
            <th>R</th>
            <td>${r}</td>
        </tr>
        <tr>
            <th>Попадание</th>
            <td>
                <span class="${hit ? 'hit' : 'miss'}">
                    ${hit ? 'ПОПАДАНИЕ' : 'ПРОМАХ'}
                </span>
            </td>
        </tr>
    </table>

    <a class="btn-back" href="controller">
        Вернуться на форму
    </a>

    <div class="gif-block">
        <img
            class="gif-image"
            src="${pageContext.request.contextPath}/${hit ? 'img/hit.gif' : 'img/miss.gif'}"
            alt="${hit ? 'Попадание' : 'Промах'}"
        />
    </div>
</div>

</body>
</html>