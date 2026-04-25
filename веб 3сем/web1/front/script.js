const API = '/api/point';

const canvas  = document.getElementById('area-canvas');
const ctx     = canvas.getContext('2d');

const MAX_R   = 5;
const MARGIN  = 16;
let   SCALE   = (Math.min(canvas.width, canvas.height) / 2 - MARGIN) / MAX_R;

const CX = canvas.width / 2, CY = canvas.height / 2;

const xButtons = document.getElementById('x-buttons');
const xHidden  = document.getElementById('x-value');

let currentR = null;


// валидация

xButtons.addEventListener('click', (e) => {
  if (e.target.matches('button[data-x]')) {
    xHidden.value = e.target.getAttribute('data-x');
    [...xButtons.querySelectorAll('button')].forEach(b => b.classList.remove('primary'));
    e.target.classList.add('primary');
  }
});

function validNumber(str) {
  if (str.trim() === '') return false;
  if (!/^[+-]?\d+(\.\d+)?$/.test(str)) return false; 
  return Number.isFinite(Number(str));
}

function validateAll() {
  const yEl  = document.getElementById('y-input');
  const yStr = yEl.value.replace(',', '.');

  yEl.classList.remove('error');

  if (!validNumber(yStr)) { yEl.classList.add('error'); return false; }

  const y = Number(yStr);
  if (!(y > -3 && y < 3)) { yEl.classList.add('error'); return false; }

  if (xHidden.value === '') return false;
  return true;
}

function setupInputValidation() {
  const yInput = document.getElementById('y-input');
  if (!yInput) return;

  yInput.addEventListener('input', function () {
    let v = this.value;

    v = v.replace(/,/g, '.');

    v = v.replace(/[^0-9.\-]/g, '');

    v = v.replace(/(?!^)-/g, '');
    if (v.lastIndexOf('-') > 0) v = v.replace(/-/g, '');
    if (v.includes('-') && v[0] !== '-') v = '-' + v.replace(/-/g, '');

    const firstDot = v.indexOf('.');
    if (firstDot !== -1) {
      v = v.substring(0, firstDot + 1) + v.substring(firstDot + 1).replace(/\./g, '');
    }

    if (v === '-' || v === '.' || v === '-.') {
      this.value = v;
      return;
    }

    const m = v.match(/^(-?\d+)(?:\.(\d*))?$/);
    if (m) {
      const intPart  = m[1];
      let   fracPart = m[2] ?? '';

      if (fracPart.length > 8) {
        fracPart = fracPart.slice(0, 8);
      }

      if (v.includes('.') && fracPart === '') {
        v = intPart + '.';
      } else {
        v = fracPart ? `${intPart}.${fracPart}` : intPart;
      }
    }

    this.value = v;
  });
}


// график

function recalcScale() {
  SCALE = (Math.min(canvas.width, canvas.height) / 2 - MARGIN) / MAX_R;
}
function toCanvasX(x){ return CX + Number(x) * SCALE; }
function toCanvasY(y){ return CY - Number(y) * SCALE; } // в canvas ось Y направлена вниз
function clearCanvas(){ ctx.clearRect(0, 0, canvas.width, canvas.height); }

function drawAxesBase() {
  ctx.strokeStyle = '#000';
  ctx.lineWidth   = 1;


  // оси X/Y
  ctx.beginPath();
  ctx.moveTo(0,  CY); ctx.lineTo(canvas.width, CY);
  ctx.moveTo(CX, 0);  ctx.lineTo(CX, canvas.height);
  ctx.stroke();

  // стрелки
  const ah = 6;
  ctx.beginPath();
  ctx.moveTo(canvas.width - ah, CY - ah/2); ctx.lineTo(canvas.width, CY); ctx.lineTo(canvas.width - ah, CY + ah/2);
  ctx.moveTo(CX - ah/2, ah);                ctx.lineTo(CX, 0);            ctx.lineTo(CX + ah/2, ah);
  ctx.stroke();


  ctx.save();
  ctx.strokeStyle = '#dcdcdc';
  ctx.lineWidth   = 1;
  ctx.beginPath();
  for (let x = -MAX_R; x <= MAX_R; x += 1) {
    if (x === 0) continue;
    const px = toCanvasX(x);
    ctx.moveTo(px, 0); ctx.lineTo(px, canvas.height);
  }
  for (let y = -MAX_R; y <= MAX_R; y += 1) {
    if (y === 0) continue;
    const py = toCanvasY(y);
    ctx.moveTo(0, py); ctx.lineTo(canvas.width, py);
  }
  ctx.stroke();
  ctx.restore();

  // риски 
  ctx.beginPath();
  const minor = 6, major = 10;
  for (let x = -MAX_R; x <= MAX_R; x += 0.5) {
    const px  = toCanvasX(x);
    const len = (Math.abs(x % 1) < 1e-9) ? major : minor;
    ctx.moveTo(px,  CY - len); ctx.lineTo(px,  CY + len);
  }
  for (let y = -MAX_R; y <= MAX_R; y += 0.5) {
    const py  = toCanvasY(y);
    const len = (Math.abs(y % 1) < 1e-9) ? major : minor;
    ctx.moveTo(CX - len, py); ctx.lineTo(CX + len, py);
  }
  ctx.stroke();

  // подписи по осям
  ctx.font = '12px monospace';
  ctx.fillStyle = '#222';

  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  for (let x = -MAX_R; x <= MAX_R; x += 1) {
    if (x === 0) continue;
    ctx.fillText(String(x), toCanvasX(x), CY + major + 2);
  }

  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';
  for (let y = -MAX_R; y <= MAX_R; y += 1) {
    if (y === 0) continue;
    ctx.fillText(String(y), CX - major - 4, toCanvasY(y));
  }
}

function drawArea(r) {
  r = Number(r);
  clearCanvas();

    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, '#1e3a8a');   
    gradient.addColorStop(0.5, '#3b82f6'); 
    gradient.addColorStop(1, '#60a5fa');   
    ctx.fillStyle = gradient;

    ctx.shadowColor = 'rgba(96, 165, 250, 0.5)'; 
    ctx.shadowBlur = 20; 

  // прямоугольник 
  ctx.beginPath();
  ctx.moveTo(toCanvasX(-r), toCanvasY(0));
  ctx.lineTo(toCanvasX(0),  toCanvasY(0));
  ctx.lineTo(toCanvasX(0),  toCanvasY(r/2));
  ctx.lineTo(toCanvasX(-r), toCanvasY(r/2));
  ctx.closePath();
  ctx.fill();

  // четверть круга 
  ctx.beginPath();
  ctx.moveTo(toCanvasX(0), toCanvasY(0));
  ctx.arc(toCanvasX(0), toCanvasY(0), r * SCALE, Math.PI, 0.5 * Math.PI, true);
  ctx.closePath();
  ctx.fill();

  // треугольник
  ctx.beginPath();
  ctx.moveTo(toCanvasX(0),  toCanvasY(0));
  ctx.lineTo(toCanvasX(r),  toCanvasY(0));
  ctx.lineTo(toCanvasX(0),  toCanvasY(r/2));
  ctx.closePath();
  ctx.fill();

  ctx.shadowColor = 'transparent';
  ctx.shadowBlur = 0;

  drawAxesBase();
}

function drawPoint(x, y) {
  ctx.fillStyle = 'black';
  ctx.beginPath();
  ctx.arc(toCanvasX(x), toCanvasY(y), 4, 0, Math.PI * 2);
  ctx.fill();
}

function drawLastPoint() {
  const saved = JSON.parse(localStorage.getItem('results') || '[]');
  if (!saved.length) return;
  const it = saved[saved.length - 1];
  drawPoint(it.x, it.y);
}



function addRow(data) {
  const tr = document.createElement('tr');
  tr.innerHTML = `<td>${data.x}</td>
                  <td>${data.y}</td>
                  <td>${data.r}</td>
                  <td>${data.hit ? 'Да' : 'Нет'}</td>
                  <td>${data.serverTime}</td>
                  <td>${data.scriptTimeMs}</td>`;
  document.getElementById('history-body').prepend(tr);
}
function renderHistory(list) {
  const tb = document.getElementById('history-body');
  tb.innerHTML = '';
  [...list].reverse().forEach(addRow);
}


// отправка формы
document.getElementById('point-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!validateAll()) {
    alert('Проверь X и Y: X — выберите кнопку, Y — число из (-3, 3).');
    return;
  }

  const x    = xHidden.value;
  const y    = document.getElementById('y-input').value.replace(',', '.');
  const rSel = document.getElementById('r-select');
  const r    = rSel.value;

  try {
    const resp = await fetch(API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
      body: new URLSearchParams({ x, y, r, action: 'check' })
    });
    const data = await resp.json();

    if (data && data.error) {
      alert(data.error);
      return;
    }

    addRow(data);

    // сохраняем локальную историю
    const saved = JSON.parse(localStorage.getItem('results') || '[]');
    saved.push({
      x: Number(data.x), y: Number(data.y), r: Number(data.r),
      hit: !!data.hit, serverTime: data.serverTime
    });
    localStorage.setItem('results', JSON.stringify(saved));

    // перерисовка области и точки под актуальный R
    currentR   = Number(data.r);
    rSel.value = String(currentR);
    drawArea(currentR);
    drawPoint(data.x, data.y);

    
    try {
      const r2 = await fetch(API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
        body: new URLSearchParams({ action: 'history' })
      });
      const h = await r2.json();
      if (Array.isArray(h.history)) renderHistory(h.history);
    } catch {}
  } catch (err) {
    alert('Ошибка загрузки');
    console.error(err);
  }
});

// очистка истории
document.getElementById('clear-btn').addEventListener('click', async () => {
  document.getElementById('history-body').innerHTML = '';
  try {
    await fetch(API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
      body: new URLSearchParams({ action: 'clear' })
    });
  } catch {}
  localStorage.removeItem('results');
  if (currentR == null) currentR = Number(document.getElementById('r-select').value);
  drawArea(currentR);
});



document.addEventListener('DOMContentLoaded', async () => {
  const rSel = document.getElementById('r-select');

  const saved = JSON.parse(localStorage.getItem('results') || '[]');
  if (saved.length) {
    currentR   = Number(saved[saved.length - 1].r);
    rSel.value = String(currentR);
  } else {
    currentR   = Number(rSel.value);
  }

  drawArea(currentR);
  drawLastPoint();

  try {
    const resp = await fetch(API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
      body: new URLSearchParams({ action: 'history' })
    });
    const data = await resp.json();
    if (Array.isArray(data.history)) {
      renderHistory(data.history);
      if (!saved.length && data.history.length) {
        const last = data.history[0];
        drawPoint(last.x, last.y);
      }
    }
  } catch {}

  setupInputValidation();
});

// ресайз
window.addEventListener('resize', () => {
  recalcScale();
  if (currentR == null) {
    const rSel = document.getElementById('r-select');
    currentR = Number(rSel.value);
  }
  drawArea(currentR);
  drawLastPoint();
});