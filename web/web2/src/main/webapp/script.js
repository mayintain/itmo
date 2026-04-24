const canvas = document.getElementById('area-canvas');
const ctx    = canvas ? canvas.getContext('2d') : null;

const MAX_R  = 5;
const MARGIN = 16;
let   SCALE  = canvas
  ? (Math.min(canvas.width, canvas.height) / 2 - MARGIN) / MAX_R
  : 1;

const CX = canvas ? canvas.width  / 2 : 0;
const CY = canvas ? canvas.height / 2 : 0;

function recalcScale() {
  if (!canvas) return;
  SCALE = (Math.min(canvas.width, canvas.height) / 2 - MARGIN) / MAX_R;
}

function toCanvasX(x) { return CX + Number(x) * SCALE; }
function toCanvasY(y) { return CY - Number(y) * SCALE; }

function fromCanvasX(px) {
  return (px - CX) / SCALE;
}

function fromCanvasY(py) {
  return (CY - py) / SCALE; 
}

function handleCanvasClick(event) {
  if (!canvas) return;

  const rInput = document.getElementById('r-input');
  const yInput = document.getElementById('y-input');
  const form   = document.getElementById('point-form');

  if (!rInput || !yInput || !form) return;

  const rStr = (rInput.value || '').replace(/,/g, '.');
  const rVal = parseStrict(rStr);

  if (!clampValidation(rVal, 1, 4)) {
    markError(rInput, true);
    return;
  }

  // обрабатывает клик 
  const rect = canvas.getBoundingClientRect(); 
  const px = event.clientX - rect.left;
  const py = event.clientY - rect.top;

  const xReal = fromCanvasX(px);
  const yReal = fromCanvasY(py);

  let snappedX = Math.round(xReal); 
  if (snappedX < -5) snappedX = -5;
  if (snappedX >  3) snappedX = 3;

  const yRounded = Number(yReal.toFixed(4));

  const xRadios = form.querySelectorAll('input[name="x"]');
  xRadios.forEach(r => {
    r.checked = (Number(r.value) === snappedX);
  });

  yInput.value = yRounded.toString();

  form.submit();
}


function clearCanvas() {
  if (!ctx || !canvas) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function drawAxesBase() {
  if (!ctx || !canvas) return;

  ctx.save();

  ctx.fillStyle = '#f5f7ff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = '#000';
  ctx.lineWidth = 1;

  ctx.beginPath();
  ctx.moveTo(0,  CY); ctx.lineTo(canvas.width, CY); // x
  ctx.moveTo(CX, 0);  ctx.lineTo(CX, canvas.height); // y
  ctx.stroke();

  const ah = 6;
  ctx.beginPath();
  ctx.moveTo(canvas.width - ah, CY - ah / 2);
  ctx.lineTo(canvas.width, CY);
  ctx.lineTo(canvas.width - ah, CY + ah / 2);

  ctx.moveTo(CX - ah / 2, ah);
  ctx.lineTo(CX, 0);
  ctx.lineTo(CX + ah / 2, ah);
  ctx.stroke();

  ctx.strokeStyle = '#e2e8f0';
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let x = -MAX_R; x <= MAX_R; x++) {
    if (x === 0) continue;
    const px = toCanvasX(x);
    ctx.moveTo(px, 0);
    ctx.lineTo(px, canvas.height);
  }
  for (let y = -MAX_R; y <= MAX_R; y++) {
    if (y === 0) continue;
    const py = toCanvasY(y);
    ctx.moveTo(0, py);
    ctx.lineTo(canvas.width, py);
  }
  ctx.stroke();

  ctx.strokeStyle = '#000';
  ctx.beginPath();
  const minor = 5, major = 9;
  for (let x = -MAX_R; x <= MAX_R; x += 0.5) {
    const px = toCanvasX(x);
    const len = Math.abs(x % 1) < 1e-9 ? major : minor;
    ctx.moveTo(px, CY - len);
    ctx.lineTo(px, CY + len);
  }
  for (let y = -MAX_R; y <= MAX_R; y += 0.5) {
    const py = toCanvasY(y);
    const len = Math.abs(y % 1) < 1e-9 ? major : minor;
    ctx.moveTo(CX - len, py);
    ctx.lineTo(CX + len, py);
  }
  ctx.stroke();

  ctx.fillStyle = '#111';
  ctx.font = '12px monospace';

  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  for (let x = -MAX_R; x <= MAX_R; x++) {
    if (x === 0) continue;
    ctx.fillText(String(x), toCanvasX(x), CY + major + 2);
  }

  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';
  for (let y = -MAX_R; y <= MAX_R; y++) {
    if (y === 0) continue;
    ctx.fillText(String(y), CX - major - 4, toCanvasY(y));
  }

  ctx.restore();
}

function drawArea(r) {
  if (!ctx || !canvas) return;

  r = Number(r);
  const h = r / 2; 

  ctx.save();
  ctx.fillStyle = 'rgba(59, 130, 246, 0.35)';

//полукруг
  {
    const steps = 40;
    ctx.beginPath();
    ctx.moveTo(toCanvasX(0), toCanvasY(0));

    for (let i = 0; i <= steps; i++) {
      const a = Math.PI / 2 + (Math.PI / 2) * (i / steps); // от π/2 до π
      const x = r * Math.cos(a);
      const y = r * Math.sin(a);
      ctx.lineTo(toCanvasX(x), toCanvasY(y));
    }

    ctx.closePath();
    ctx.fill();
  }

//прямоугольник
  {
    ctx.beginPath();
    ctx.moveTo(toCanvasX(0),  toCanvasY(0));
    ctx.lineTo(toCanvasX(r),  toCanvasY(0));
    ctx.lineTo(toCanvasX(r),  toCanvasY(-h));
    ctx.lineTo(toCanvasX(0),  toCanvasY(-h));
    ctx.closePath();
    ctx.fill();
  }

//треугольник
  {
    ctx.beginPath();
    ctx.moveTo(toCanvasX(0),   toCanvasY(0));
    ctx.lineTo(toCanvasX(-h),  toCanvasY(0));
    ctx.lineTo(toCanvasX(0),   toCanvasY(-h));
    ctx.closePath();
    ctx.fill();
  }

  ctx.restore();
}


function drawPoint(x, y, hit) {
  if (!ctx) return;
  ctx.save();
  ctx.fillStyle = hit ? '#16a34a' : '#dc2626';
  ctx.beginPath();
  ctx.arc(toCanvasX(x), toCanvasY(y), 4, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function redrawArea() {
  clearCanvas();
  drawAxesBase();

  const rInput = document.getElementById('r-input');
  if (!rInput) return;

  const rStr = (rInput.value || '').replace(/,/g, '.');
  const rVal = parseStrict(rStr);

  if (clampValidation(rVal, 1, 4)) {
    drawArea(rVal);
  }
}

// валидация
function sanitizeNumericString(raw, { allowSign, maxFractionDigits }) {
  let v = String(raw).replace(/,/g, '.');

  v = v.replace(allowSign ? /[^0-9.\-]/g : /[^0-9.]/g, ''); 

  if (allowSign) {
    const neg = v.startsWith('-');
    v = v.replace(/-/g, '');
    if (neg) v = '-' + v;
  } else {
    v = v.replace(/-/g, '');
  }

  const firstDot = v.indexOf('.');
  if (firstDot !== -1) {
    v = v.slice(0, firstDot + 1) + v.slice(firstDot + 1).replace(/\./g, '');
  }

  if (v === '.' || (allowSign && (v === '-' || v === '-.'))) return v;

  const m = v.match(/^(-?\d+)(?:\.(\d*))?$/);
  if (!m) return v;

  const intPart = m[1];
  let fracPart = m[2] ?? '';

  if (fracPart.length > maxFractionDigits) {
    fracPart = fracPart.slice(0, maxFractionDigits);
  }

  if (v.includes('.') && fracPart === '') {
    return intPart + '.';
  }
  return fracPart ? `${intPart}.${fracPart}` : intPart;
}

function parseStrict(numStr) {
  if (!numStr || numStr === '-' || numStr === '.' || numStr === '-.') return NaN;
  return Number(numStr);
}

function clampValidation(value, min, max) {
  return Number.isFinite(value) && value >= min && value <= max;
}

function markError(el, isError) {
  if (!el) return;
  el.classList.toggle('error', !!isError);
}

function attachRealtimeSanitizer(inputEl, opts) {
  if (!inputEl) return;
  inputEl.addEventListener('input', () => {
    const cur = inputEl.value;
    const cleaned = sanitizeNumericString(cur, opts);
    if (cleaned !== cur) {
      const start = inputEl.selectionStart;
      const end   = inputEl.selectionEnd;
      inputEl.value = cleaned;
      if (start != null && end != null) {
        const shift = cleaned.length - cur.length;
        inputEl.setSelectionRange(start + shift, end + shift);
      }
    }
    markError(inputEl, false);
  });
}

function validateForm(event) {
  const form   = event.currentTarget;
  const xRadio = form.querySelector('input[name="x"]:checked');
  const yInput = document.getElementById('y-input');
  const rInput = document.getElementById('r-input');

  let ok = true;

  if (!xRadio) ok = false;

  const yStr = (yInput.value || '').replace(/,/g, '.');
  const yNum = parseStrict(yStr);
  const yValid = clampValidation(yNum, -5, 5);
  if (!yValid) {
    ok = false;
    markError(yInput, true);
  } else {
    markError(yInput, false);
  }

  const rStr = (rInput.value || '').replace(/,/g, '.');
  const rNum = parseStrict(rStr);
  const rValid = clampValidation(rNum, 1, 4);
  if (!rValid) {
    ok = false;
    markError(rInput, true);
  } else {
    markError(rInput, false);
  }

  if (!ok) {
    event.preventDefault();
    return false;
  }
  return true;
}

// инициализация
document.addEventListener('DOMContentLoaded', () => {
  const form   = document.getElementById('point-form');
  const yInput = document.getElementById('y-input');
  const rInput = document.getElementById('r-input');

  if (canvas && ctx) {
    recalcScale();
    redrawArea();

 
    if (Array.isArray(window.allPoints) && window.allPoints.length > 0) {
      window.allPoints.forEach(p => drawPoint(p.x, p.y, p.hit));
    } else if (window.lastPoint) {
      drawPoint(window.lastPoint.x, window.lastPoint.y, window.lastPoint.hit);
    }

    window.addEventListener('resize', () => {
      recalcScale();
      redrawArea();
      if (Array.isArray(window.allPoints) && window.allPoints.length > 0) {
        window.allPoints.forEach(p => drawPoint(p.x, p.y, p.hit));
      } else if (window.lastPoint) {
        drawPoint(window.lastPoint.x, window.lastPoint.y, window.lastPoint.hit);
      }
    });

    if (rInput) {
      rInput.addEventListener('input', () => {
        redrawArea();
        if (Array.isArray(window.allPoints) && window.allPoints.length > 0) {
          window.allPoints.forEach(p => drawPoint(p.x, p.y, p.hit));
        } else if (window.lastPoint) {
          drawPoint(window.lastPoint.x, window.lastPoint.y, window.lastPoint.hit);
        }
      });
    }

    canvas.addEventListener('click', handleCanvasClick);
  }

  attachRealtimeSanitizer(yInput, { allowSign: true,  maxFractionDigits: 8 });
  attachRealtimeSanitizer(rInput, { allowSign: false, maxFractionDigits: 8 });

  if (form) {
    form.addEventListener('submit', validateForm);
  }
});

