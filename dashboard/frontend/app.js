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
let userMood = 'Neutral';
let autoCalculateEndurance = true;
let userAge = 38;
let activeMinutes = 75;
const currentValues = {};
let lastResult = null;

const RADAR_LABELS = {
  sleep_hours: 'Sleep', stress_level: 'Stress', daily_steps: 'Steps', heart_rate: 'Heart Rate',
  endurance_level: 'Endurance', bmi: 'BMI', hydration_level: 'Hydration'
};

const GAUGE_STYLES = {
  emerald: { stroke: 'url(#scoreGradientEmerald)', badge: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' },
  sky: { stroke: 'url(#scoreGradientSky)', badge: 'bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300' },
  amber: { stroke: 'url(#scoreGradientAmber)', badge: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300' },
  rose: { stroke: 'url(#scoreGradientRose)', badge: 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300' }
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
      mood: userMood,
      age: userAge,
      active_minutes: activeMinutes,
      auto_endurance: autoCalculateEndurance
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
  if (autoCalculateEndurance) {
    currentValues.endurance_level = result.values.endurance_level;
    const display = document.getElementById('display_endurance_level');
    const input = document.getElementById('input_endurance_level');
    if (display) display.innerText = currentValues.endurance_level.toFixed(1);
    if (input) input.value = currentValues.endurance_level;
  }
  updateMainScoreGauge(result);
  updateSubScoresUI(result.sub_scores);
  updateAlertsUI(result.alerts);
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
  recalculateAll();
}

function onActiveMinutesChange(val) {
  activeMinutes = parseInt(val);
  document.getElementById('activeMinsDisplay').innerText = activeMinutes;
  recalculateAll();
}

function onAutoEnduranceToggle() {
  autoCalculateEndurance = document.getElementById('autoEnduranceToggle').checked;
  renderSliders();
  recalculateAll();
}

function setMood(mood) {
  userMood = mood;
  const moods = ['Happy', 'Neutral', 'Sad', 'Stressed'];
  moods.forEach(m => {
    const btn = document.getElementById(`moodBtn_${m}`);
    if (!btn) return;
    if (m === mood) {
      btn.className = 'mood-btn flex items-center justify-center gap-2 p-2 rounded-xl border-2 border-sky-500 bg-sky-50 dark:bg-sky-950/40 text-xs font-bold text-sky-800 dark:text-sky-200 shadow-sm transition';
    } else {
      btn.className = 'mood-btn flex items-center justify-center gap-2 p-2 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-slate-400 text-xs font-semibold text-slate-700 dark:text-slate-300 transition';
    }
  });

  const badge = document.getElementById('moodEffectBadge');
  if (mood === 'Happy') {
    badge.innerText = 'Recovery Bonus Active (+5 pts)';
    badge.className = 'text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-300/40';
  } else if (mood === 'Stressed' || mood === 'Sad') {
    badge.innerText = 'Burnout Multiplier Active (+25%)';
    badge.className = 'text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300 border border-rose-300/40';
  } else {
    badge.innerText = 'Neutral Baseline';
    badge.className = 'text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700';
  }

  recalculateAll();
}

function onCohortChange() {
  activeCohortKey = document.getElementById('cohortSelector').value;
  updateCohortLabels();
  renderSliders();
  recalculateAll();
}

function updateCohortLabels() {
  const cohort = COHORTS[activeCohortKey];
  document.getElementById('cohortSummaryLabel').innerText = `${cohort.name} (N = ${cohort.count.toLocaleString()})`;
  document.getElementById('percentileCohortLabel').innerText = cohort.name;
}

/**
 * PRESETS & SAMPLE LOGS (served by the API as "profiles")
 */
async function loadProfile(name) {
  try {
    const profile = await api(`/api/profiles/${encodeURIComponent(name)}?sex=${userSex}`);
    Object.assign(currentValues, profile.values);
    activeMinutes = profile.active_minutes;
    document.getElementById('activeMinutes').value = activeMinutes;
    document.getElementById('activeMinsDisplay').innerText = activeMinutes;
    renderSliders();
    setMood(profile.mood); // triggers recalculation
  } catch (err) {
    showApiError(err.message);
  }
}

function applyPreset(name) {
  loadProfile(name);
}

function loadSampleLog(name) {
  loadProfile(name);
}

function resetToMedian() {
  loadProfile('clinical_med');
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
    card.className = 'bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-200/70 dark:border-slate-800 transition-all';
    card.id = `card_${p.id}`;

    const isEnduranceLocked = (p.id === 'endurance_level' && autoCalculateEndurance);
    const formattedMean = formatMean(p.id, cohortMeans[p.id] || 0);

    card.innerHTML = `
      <div class="flex items-center justify-between gap-2 mb-1">
        <div class="flex items-center gap-1.5">
          <label for="input_${p.id}" class="text-xs font-bold text-slate-800 dark:text-slate-100">${p.name}</label>
          ${isEnduranceLocked ? '<span class="text-[9px] font-mono bg-sky-100 dark:bg-sky-950 text-sky-700 dark:text-sky-300 px-1 rounded">Auto</span>' : ''}
          <span class="text-[10px] text-slate-400 font-normal">(${p.hint})</span>
        </div>
        <div class="text-right">
          <span id="display_${p.id}" class="font-mono text-sm font-bold text-sky-600 dark:text-sky-400">
            ${p.id === 'daily_steps' ? Math.round(currentValues[p.id]).toLocaleString() : currentValues[p.id].toFixed(1)}
          </span>
          <span class="text-[11px] text-slate-500 dark:text-slate-400">${p.unit}</span>
        </div>
      </div>

      <div class="mt-1">
        <input
          type="range"
          id="input_${p.id}"
          min="${p.min}"
          max="${p.max}"
          step="${p.step}"
          value="${currentValues[p.id]}"
          ${isEnduranceLocked ? 'disabled' : ''}
          oninput="onSliderChange('${p.id}', this.value)"
        />
      </div>

      <div class="flex justify-between items-center mt-1 text-[10px] text-slate-400 font-mono">
        <span>${p.id === 'daily_steps' ? p.min.toLocaleString() : p.min}</span>
        <span class="text-slate-500 font-sans font-medium">Cohort μ: ${formattedMean}</span>
        <span>${p.id === 'daily_steps' ? p.max.toLocaleString() : p.max}</span>
      </div>
    `;
    container.appendChild(card);
  });
}

function updateMainScoreGauge(result) {
  const circle = document.getElementById('scoreGaugeCircle');
  const style = GAUGE_STYLES[result.verdict.tier];

  const maxOffset = 427.2;
  circle.style.strokeDashoffset = maxOffset - (result.score / 100) * maxOffset;
  circle.setAttribute('stroke', style.stroke);
  document.getElementById('mainScoreValue').innerText = result.score.toFixed(1);

  const badge = document.getElementById('scoreBadge');
  badge.className = `text-xs font-semibold px-2.5 py-0.5 rounded-full ${style.badge}`;
  badge.innerText = `${result.score.toFixed(0)} / 100 Index`;
  document.getElementById('verdictHeadline').innerText = result.verdict.title;
  document.getElementById('verdictSubtext').innerText = result.verdict.description;
}

function updateSubScoresUI(subScores) {
  const container = document.getElementById('subScoresList');
  container.innerHTML = '';

  PARAM_SPECS.forEach(p => {
    const score = subScores[p.id];
    let barColor = 'bg-sky-500';
    if (score >= 85) barColor = 'bg-emerald-500';
    else if (score < 50) barColor = 'bg-rose-500';
    else if (score < 70) barColor = 'bg-amber-500';

    const row = document.createElement('div');
    row.className = 'space-y-1';
    row.innerHTML = `
      <div class="flex justify-between items-center text-xs">
        <span class="font-medium text-slate-700 dark:text-slate-300">${p.name}</span>
        <span class="font-mono font-bold text-slate-800 dark:text-slate-200">${score.toFixed(0)} <span class="text-slate-400 font-normal">/100</span></span>
      </div>
      <div class="w-full h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
        <div class="${barColor} h-full rounded-full transition-all duration-300" style="width: ${score}%"></div>
      </div>
    `;
    container.appendChild(row);
  });
}

function updateAlertsUI(alerts) {
  const container = document.getElementById('alertsContainer');
  container.innerHTML = '';

  alerts.forEach(alert => {
    const isDanger = alert.type === 'danger';
    const isSuccess = alert.type === 'success';
    const colorClasses = isDanger
      ? 'bg-rose-50 border-rose-200 text-rose-900 dark:bg-rose-950/40 dark:border-rose-900/60 dark:text-rose-200'
      : isSuccess
      ? 'bg-emerald-50 border-emerald-200 text-emerald-900 dark:bg-emerald-950/40 dark:border-emerald-900/60 dark:text-emerald-200'
      : 'bg-amber-50 border-amber-200 text-amber-900 dark:bg-amber-950/40 dark:border-amber-900/60 dark:text-amber-200';

    const badgeClasses = isDanger ? 'bg-rose-500' : isSuccess ? 'bg-emerald-500' : 'bg-amber-500';

    const alertDiv = document.createElement('div');
    alertDiv.className = `p-2.5 rounded-xl border text-xs ${colorClasses}`;
    alertDiv.innerHTML = `
      <div class="flex items-center justify-between font-bold mb-0.5">
        <div class="flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full ${badgeClasses}"></span>
          <span>${alert.title}</span>
        </div>
        <span>${alert.deduction > 0 ? `-${alert.deduction.toFixed(1)} pts` : `+${Math.abs(alert.deduction).toFixed(1)} pts`}</span>
      </div>
      <p class="text-[11px] leading-relaxed opacity-90">${alert.description}</p>
    `;
    container.appendChild(alertDiv);
  });
}

function updatePercentilesTable(percentiles) {
  const tbody = document.getElementById('percentilesTableBody');
  tbody.innerHTML = '';

  PARAM_SPECS.forEach(p => {
    const val = currentValues[p.id];
    const data = percentiles[p.id];

    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors';
    tr.innerHTML = `
      <td class="py-1.5 text-slate-700 dark:text-slate-300 font-sans font-medium">${p.name}</td>
      <td class="py-1.5 text-sky-600 dark:text-sky-400 font-bold">${formatMean(p.id, val)} ${p.unit}</td>
      <td class="py-1.5 text-slate-400">${formatMean(p.id, data.mean)}</td>
      <td class="py-1.5 ${data.z > 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'}">${data.z > 0 ? '+' : ''}${data.z.toFixed(2)}σ</td>
      <td class="py-1.5 text-right ${data.pct > 75 ? 'text-emerald-500 font-bold' : data.pct < 25 ? 'text-rose-500 font-semibold' : 'text-slate-500'}">
        ${data.pct.toFixed(0)}th %ile
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function updateBehavioralROI(roi) {
  const recElement = document.getElementById('roiText');
  if (roi) {
    recElement.innerHTML = `
      <strong>Highest-Leverage Habit:</strong> Focus on <span class="text-sky-600 dark:text-sky-400 font-bold">${roi.label}</span>.
      This adjustment yields an estimated <strong class="text-emerald-600 dark:text-emerald-400">+${roi.gain.toFixed(1)} points</strong> improvement to the overall score.
    `;
  } else {
    recElement.innerHTML = `
      <strong>Well-Balanced Equilibrium:</strong> Your physiological parameters are currently balanced.
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
  const isDark = document.documentElement.classList.contains('dark');

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
    ctx.strokeStyle = isDark ? '#334155' : '#e2e8f0';
    ctx.lineWidth = 1;
    ctx.stroke();
  });

  ctx.font = '10px Inter, sans-serif';
  ctx.fillStyle = isDark ? '#94a3b8' : '#64748b';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  PARAM_SPECS.forEach((p, i) => {
    const angle = i * angleSlice - Math.PI / 2;
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(centerX + Math.cos(angle) * radius, centerY + Math.sin(angle) * radius);
    ctx.strokeStyle = isDark ? '#334155' : '#e2e8f0';
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

function toggleTheme() {
  const isDark = document.documentElement.classList.toggle('dark');
  const icon = document.getElementById('themeIcon');
  if (isDark) {
    icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />`;
  } else {
    icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />`;
  }
  if (lastResult) drawRadarChart(lastResult.sub_scores);
}

if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
  document.documentElement.classList.add('dark');
}

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
