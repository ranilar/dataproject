/**
 * Dashboard client. All scoring happens in the API; this file holds UI state,
 * sends it to /api/score and renders the response.
 */

const API_BASE = (window.API_BASE || '').replace(/\/$/, '');

// APPLICATION STATE
let PARAM_SPECS = [];
let COHORTS = {};
let activeCohortKey = 'HARMONIZED';
let userSex = 'ALL'; // 'ALL', 'M', 'F'
let userAge = 38;
let activeMinutes = 75;
const currentValues = {};
let lastResult = null;

const RADAR_LABELS = {
  sleep_hours: 'Sleep', stress_level: 'Stress', daily_steps: 'Steps', heart_rate: 'Heart Rate',
  endurance_level: 'Endurance', bmi: 'BMI', hydration_level: 'Hydration'
};

/**
 * API
 */
async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = body && body.detail;
    const message = typeof detail === 'string' ? detail
      : Array.isArray(detail) ? detail.map(d => `${d.loc.slice(1).join('.')}: ${d.msg}`).join('; ')
      : `HTTP ${res.status}`;
    throw new Error(message);
  }
  return body;
}

function showApiError(message) {
  const banner = document.getElementById('apiErrorBanner');
  if (message) {
    banner.innerHTML = `<strong>Scoring API unavailable.</strong> <span class="font-mono"></span>`;
    banner.querySelector('span').textContent = message;
    banner.classList.remove('hidden');
  } else {
    banner.classList.add('hidden');
  }
}

/**
 * RECALCULATION
 * Slider input fires faster than round-trips, so at most one request is in flight;
 * changes made meanwhile are coalesced into one follow-up request with the latest state.
 */
let requestInFlight = false;
let requestPending = false;

function recalculateAll() {
  if (requestInFlight) {
    requestPending = true;
    return;
  }
  requestInFlight = true;
  api('/api/score', {
    method: 'POST',
    body: JSON.stringify({
      values: currentValues,
      cohort: activeCohortKey,
      sex: userSex,
    })
  })
    .then(result => {
      showApiError(null);
      lastResult = result;
      renderResult(result);
    })
    .catch(err => showApiError(err.message))
    .finally(() => {
      requestInFlight = false;
      if (requestPending) {
        requestPending = false;
        recalculateAll();
      }
    });
}

function renderResult(result) {
  updateScoreIndex(result);
  updateSubScoresUI(result.sub_scores);
  updatePercentilesTable(result.percentiles);
  updateBehavioralROI(result.roi);
  drawRadarChart(result.sub_scores);
}

/**
 * FORMATTING
 */
function formatValue(id, val) {
  if (id === 'daily_steps') return Math.round(val).toLocaleString();
  return val.toFixed(id === 'heart_rate' ? 0 : 1);
}

function formatMean(id, val) {
  return id === 'daily_steps' ? Math.round(val).toLocaleString() : val.toFixed(1);
}

/**
 * INPUT HANDLERS
 */
function onSexChange(val) {
  userSex = val;

  // Auto-adapt hydration default if at baseline
  if (userSex === 'M' && currentValues.hydration_level < 3.2) {
    currentValues.hydration_level = 3.7;
  } else if (userSex === 'F' && currentValues.hydration_level > 3.2) {
    currentValues.hydration_level = 2.7;
  }

  renderSliders();
  recalculateAll();
}

function onSliderChange(id, value) {
  currentValues[id] = parseFloat(value);
  const displayElem = document.getElementById(`display_${id}`);
  if (displayElem) displayElem.innerText = formatValue(id, currentValues[id]);
  recalculateAll();
}

function onAgeChange(val) {
  userAge = parseInt(val);
  document.getElementById('ageDisplay').innerText = userAge;
}

function onActiveMinutesChange(val) {
  activeMinutes = parseInt(val);
  document.getElementById('activeMinsDisplay').innerText = activeMinutes;
}

function onCohortChange() {
  activeCohortKey = document.getElementById('cohortSelector').value;
  updateCohortLabels();
  renderSliders();
  recalculateAll();
}

function updateCohortLabels() {
  const cohort = COHORTS[activeCohortKey];
  document.getElementById('percentileCohortLabel').innerText = cohort.name;
}

/**
 * PRESETS (served by the API as "profiles")
 */
async function loadProfile(name) {
  try {
    const profile = await api(`/api/profiles/${encodeURIComponent(name)}?sex=${userSex}`);
    Object.assign(currentValues, profile.values);
    activeMinutes = profile.active_minutes;
    document.getElementById('activeMinutes').value = activeMinutes;
    document.getElementById('activeMinsDisplay').innerText = activeMinutes;
    renderSliders();
    recalculateAll();
  } catch (err) {
    showApiError(err.message);
  }
}

function applyPreset(name) {
  loadProfile(name);
}

// Back to the starting values: the dataset medians
function resetToMedian() {
  PARAM_SPECS.forEach(p => currentValues[p.id] = p.default);
  renderSliders();
  recalculateAll();
}

/**
 * RENDERING
 */
function renderSliders() {
  const container = document.getElementById('slidersContainer');
  container.innerHTML = '';
  const cohortMeans = COHORTS[activeCohortKey].means;

  PARAM_SPECS.forEach(p => {
    const card = document.createElement('div');
    card.className = 'py-2.5';
    card.id = `card_${p.id}`;

    const formattedMean = formatMean(p.id, cohortMeans[p.id] || 0);

    card.innerHTML = `
      <div class="flex items-baseline justify-between gap-2">
        <div>
          <label for="input_${p.id}" class="text-sm font-medium">${p.name}</label>
          <span class="block text-xs text-slate-500">${p.hint}</span>
        </div>
        <div class="text-right whitespace-nowrap">
          <span id="display_${p.id}" class="font-mono text-sm font-semibold">
            ${p.id === 'daily_steps' ? Math.round(currentValues[p.id]).toLocaleString() : currentValues[p.id].toFixed(1)}
          </span>
          <span class="text-xs text-slate-500">${p.unit}</span>
        </div>
      </div>

      <div>
        <input
          type="range"
          id="input_${p.id}"
          min="${p.min}"
          max="${p.max}"
          step="${p.step}"
          value="${currentValues[p.id]}"
          oninput="onSliderChange('${p.id}', this.value)"
        />
      </div>

      <div class="flex justify-between items-center text-[11px] text-slate-500 font-mono">
        <span>${p.id === 'daily_steps' ? p.min.toLocaleString() : p.min}</span>
        <span class="font-sans">Dataset mean: ${formattedMean}</span>
        <span>${p.id === 'daily_steps' ? p.max.toLocaleString() : p.max}</span>
      </div>
    `;
    container.appendChild(card);
  });
}

function updateScoreIndex(result) {
  document.getElementById('scoreIndex').innerText = `${result.score.toFixed(0)} / 100 Index`;
}

function updateSubScoresUI(subScores) {
  const container = document.getElementById('subScoresList');
  container.innerHTML = '';

  PARAM_SPECS.forEach(p => {
    const score = subScores[p.id];
    let barColor = 'bg-sky-500';
    if (score < 50) barColor = 'bg-rose-500';
    else if (score < 70) barColor = 'bg-amber-500';

    const row = document.createElement('div');
    row.className = 'space-y-1';
    row.innerHTML = `
      <div class="flex justify-between items-center text-xs">
        <span>${p.name}</span>
        <span class="font-mono">${score.toFixed(0)}</span>
      </div>
      <div class="w-full h-1.5 bg-slate-200">
        <div class="${barColor} h-full" style="width: ${score}%"></div>
      </div>
    `;
    container.appendChild(row);
  });
}

function updatePercentilesTable(percentiles) {
  const tbody = document.getElementById('percentilesTableBody');
  tbody.innerHTML = '';

  PARAM_SPECS.forEach(p => {
    const val = currentValues[p.id];
    const data = percentiles[p.id];

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="py-1.5 font-sans">${p.name}</td>
      <td class="py-1.5 font-semibold">${formatMean(p.id, val)} ${p.unit}</td>
      <td class="py-1.5 text-slate-500">${formatMean(p.id, data.mean)}</td>
      <td class="py-1.5 text-slate-500">${data.z > 0 ? '+' : ''}${data.z.toFixed(2)}σ</td>
      <td class="py-1.5 text-right text-slate-500">${data.pct.toFixed(0)}th %ile</td>
    `;
    tbody.appendChild(tr);
  });
}

function updateBehavioralROI(roi) {
  const recElement = document.getElementById('roiText');
  if (roi) {
    recElement.innerHTML = `
      <strong>Highest-Leverage Habit:</strong> Focus on <strong>${roi.label}</strong>.
      This adjustment yields an estimated <strong>+${roi.gain.toFixed(1)} points</strong> improvement to the overall score.
    `;
  } else {
    recElement.innerHTML = `
      <strong>Well Balanced:</strong> No single change would improve your score by more than 0.4 points.
    `;
  }
}

function drawRadarChart(subScores) {
  const canvas = document.getElementById('radarCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = 88;
  const totalAxes = PARAM_SPECS.length;
  const angleSlice = (Math.PI * 2) / totalAxes;

  ctx.clearRect(0, 0, width, height);

  [0.25, 0.5, 0.75, 1.0].forEach(level => {
    ctx.beginPath();
    for (let i = 0; i < totalAxes; i++) {
      const angle = i * angleSlice - Math.PI / 2;
      const x = centerX + Math.cos(angle) * (radius * level);
      const y = centerY + Math.sin(angle) * (radius * level);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    ctx.stroke();
  });

  ctx.font = '10px Inter, sans-serif';
  ctx.fillStyle = '#64748b';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  PARAM_SPECS.forEach((p, i) => {
    const angle = i * angleSlice - Math.PI / 2;
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(centerX + Math.cos(angle) * radius, centerY + Math.sin(angle) * radius);
    ctx.strokeStyle = '#e2e8f0';
    ctx.stroke();
    ctx.fillText(RADAR_LABELS[p.id] || '', centerX + Math.cos(angle) * (radius + 16), centerY + Math.sin(angle) * (radius + 16));
  });

  const point = (p, i) => {
    const angle = i * angleSlice - Math.PI / 2;
    const norm = Math.max(0.1, Math.min(1.0, (subScores[p.id] || 50) / 100));
    return [centerX + Math.cos(angle) * (radius * norm), centerY + Math.sin(angle) * (radius * norm)];
  };

  ctx.beginPath();
  PARAM_SPECS.forEach((p, i) => {
    const [x, y] = point(p, i);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = 'rgba(14, 165, 233, 0.25)';
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = '#0284c7';
  ctx.stroke();

  PARAM_SPECS.forEach((p, i) => {
    const [x, y] = point(p, i);
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fillStyle = '#0284c7';
    ctx.fill();
  });
}

/**
 * DISCLAIMER (shown on every page load; the Info button reopens it)
 */
const disclaimerDialog = document.getElementById('disclaimerDialog');

function openDisclaimer() {
  if (!disclaimerDialog.open) disclaimerDialog.showModal();
}

// Clicking the backdrop (outside the dialog box) closes it
disclaimerDialog.addEventListener('click', e => {
  if (e.target === disclaimerDialog) disclaimerDialog.close();
});

openDisclaimer();

window.onload = async function() {
  try {
    const config = await api('/api/config');
    PARAM_SPECS = config.params;
    COHORTS = config.cohorts;
    PARAM_SPECS.forEach(p => currentValues[p.id] = p.default);
    updateCohortLabels();
    renderSliders();
    recalculateAll();
  } catch (err) {
    showApiError(err.message);
  }
};
