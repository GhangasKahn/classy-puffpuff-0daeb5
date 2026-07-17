"use strict";
/* ============================================================
   AEGIS AIR — on-device ML. No cloud, no keys, no uploads.
   Every model is small, transparent and prints its weights.
   These find patterns in modeled data + the user's own logs.
   They are NOT medical inference.
   ============================================================ */

const AegisML = (() => {

  /* ---------- linear algebra (tiny, dense) ---------- */
  function matMul(A, B) {
    const n = A.length, m = B[0].length, k = B.length;
    const C = Array.from({ length: n }, () => new Float64Array(m));
    for (let i = 0; i < n; i++) for (let p = 0; p < k; p++) {
      const a = A[i][p];
      if (a === 0) continue;
      for (let j = 0; j < m; j++) C[i][j] += a * B[p][j];
    }
    return C;
  }
  function transpose(A) {
    return A[0].map((_, j) => A.map(r => r[j]));
  }
  /* solve (X'X + λI) w = X'y via Gaussian elimination */
  function ridgeFit(X, y, lambda = 1.0) {
    const Xt = transpose(X);
    const G = matMul(Xt, X);
    const d = G.length;
    for (let i = 0; i < d; i++) G[i][i] += lambda;
    const b = Xt.map(row => row.reduce((s, v, i) => s + v * y[i], 0));
    // gaussian elimination with partial pivot
    const M = G.map((r, i) => [...r, b[i]]);
    for (let col = 0; col < d; col++) {
      let piv = col;
      for (let r = col + 1; r < d; r++) if (Math.abs(M[r][col]) > Math.abs(M[piv][col])) piv = r;
      [M[col], M[piv]] = [M[piv], M[col]];
      if (Math.abs(M[col][col]) < 1e-12) continue;
      for (let r = 0; r < d; r++) {
        if (r === col) continue;
        const f = M[r][col] / M[col][col];
        for (let c = col; c <= d; c++) M[r][c] -= f * M[col][c];
      }
    }
    return M.map((row, i) => Math.abs(row[i]) < 1e-12 ? 0 : row[d] / row[i]);
  }

  /* ---------- NOWCAST: ridge regression on PM2.5 history ----------
     Features per hour t: [1, lag1, lag2, lag24, trend6, sin(hod), cos(hod)]
     Trained on past-7-day CAMS series; recursive 24 h rollout. */
  const NC_FEATS = ["BIAS", "LAG-1H", "LAG-2H", "LAG-24H", "TREND-6H", "SIN(HOD)", "COS(HOD)"];

  function ncRow(series, t, hodOf) {
    const hod = hodOf(t) / 24 * 2 * Math.PI;
    const trend = (series[t - 1] - series[t - 7]) / 6;
    return [1, series[t - 1], series[t - 2], series[t - 24], trend, Math.sin(hod), Math.cos(hod)];
  }

  function trainNowcast(times, values) {
    // values: hourly pm2_5, aligned with ISO time strings
    const series = values.map(v => v == null ? 0 : v);
    const hodOf = (t) => new Date(times[t]).getHours();
    const X = [], y = [];
    for (let t = 25; t < series.length; t++) {
      if (values[t] == null) continue;
      X.push(ncRow(series, t, hodOf));
      y.push(series[t]);
    }
    if (X.length < 48) return null;

    // holdout = last 24 samples
    const cut = X.length - 24;
    const w = ridgeFit(X.slice(0, cut), y.slice(0, cut), 1.0);
    const predict = (row) => row.reduce((s, v, i) => s + v * w[i], 0);

    let sse = 0;
    for (let i = cut; i < X.length; i++) {
      const e = predict(X[i]) - y[i]; sse += e * e;
    }
    const rmse = Math.sqrt(sse / 24);

    // recursive rollout 24 h beyond the end of the series.
    // Recursive AR rollouts can drift when the lag-1 weight ≈ 1, so each
    // step is damped toward the recent mean and capped vs observed history.
    const ext = [...series];
    const t0 = series.length;
    const out = [];
    const recent = series.slice(-72).filter(v => v > 0);
    const recentMean = recent.reduce((s, v) => s + v, 0) / Math.max(recent.length, 1);
    const cap = Math.max(...recent, 10) * 1.5;
    for (let h = 0; h < 24; h++) {
      const t = t0 + h;
      const hod = (new Date(times[times.length - 1]).getHours() + 1 + h) % 24;
      const row = [1, ext[t - 1], ext[t - 2], ext[t - 24], (ext[t - 1] - ext[t - 7]) / 6,
                   Math.sin(hod / 24 * 2 * Math.PI), Math.cos(hod / 24 * 2 * Math.PI)];
      const damp = 0.06; // pull each step slightly toward the 72 h mean
      let p = predict(row) * (1 - damp) + recentMean * damp;
      p = Math.min(Math.max(0, p), cap);
      ext.push(p); out.push(p);
    }
    return { weights: w, featNames: NC_FEATS, rmse, forecast: out };
  }

  /* ---------- ANOMALY SENTINEL: robust z vs same-hour 7-day baseline ---------- */
  function median(a) { const s = [...a].sort((x, y) => x - y); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; }
  function sentinel(times, values, current) {
    if (current == null) return null;
    const nowH = new Date().getHours();
    const sameHour = [];
    for (let i = 0; i < times.length; i++) {
      if (values[i] == null) continue;
      const h = new Date(times[i]).getHours();
      if (Math.abs(h - nowH) <= 1) sameHour.push(values[i]);
    }
    if (sameHour.length < 8) return null;
    const med = median(sameHour);
    const mad = median(sameHour.map(v => Math.abs(v - med))) || 0.5;
    const z = (current - med) / (1.4826 * mad);
    return { z, median: med, n: sameHour.length };
  }

  /* ---------- PERSONAL PATTERN LEARNER: logistic regression ----------
     y = any respiratory symptom reported; X = [1, pm25, hrDev, outdoorMin]
     Standardized features, gradient descent, L2. Needs ≥8 varied rows. */
  const PPL_FEATS = ["BIAS", "PM2.5 @ LOG", "HR DEVIATION", "OUTDOOR MIN"];
  const RESP = ["cough", "wheeze", "sob", "chestTight", "throat"];

  function trainPersonal(checkins, hrBaseline) {
    const rows = [];
    for (const c of checkins) {
      const pm = c.context?.pm25;
      if (pm == null) continue;
      const hrDev = (c.hr && hrBaseline) ? (c.hr - hrBaseline) / hrBaseline : 0;
      const outdoor = c.outdoorMin ?? 0;
      const y = (c.symptoms || []).some(s => RESP.includes(s)) || (c.emergency || []).length ? 1 : 0;
      rows.push({ x: [pm, hrDev, outdoor], y });
    }
    const n = rows.length;
    const pos = rows.filter(r => r.y === 1).length;
    if (n < 8 || pos === 0 || pos === n) {
      return { trained: false, n, pos, need: Math.max(0, 8 - n) };
    }
    // standardize
    const dims = 3;
    const mu = [0, 0, 0], sd = [1, 1, 1];
    for (let d = 0; d < dims; d++) {
      mu[d] = rows.reduce((s, r) => s + r.x[d], 0) / n;
      sd[d] = Math.sqrt(rows.reduce((s, r) => s + (r.x[d] - mu[d]) ** 2, 0) / n) || 1;
    }
    const X = rows.map(r => [1, ...r.x.map((v, d) => (v - mu[d]) / sd[d])]);
    const Y = rows.map(r => r.y);
    let w = [0, 0, 0, 0];
    const lr = 0.3, l2 = 0.02;
    for (let iter = 0; iter < 600; iter++) {
      const g = [0, 0, 0, 0];
      for (let i = 0; i < n; i++) {
        const z = X[i].reduce((s, v, d) => s + v * w[d], 0);
        const p = 1 / (1 + Math.exp(-z));
        for (let d = 0; d < 4; d++) g[d] += (p - Y[i]) * X[i][d];
      }
      for (let d = 0; d < 4; d++) w[d] -= lr * (g[d] / n + (d ? l2 * w[d] : 0));
    }
    let correct = 0;
    for (let i = 0; i < n; i++) {
      const p = 1 / (1 + Math.exp(-X[i].reduce((s, v, d) => s + v * w[d], 0)));
      if ((p >= 0.5 ? 1 : 0) === Y[i]) correct++;
    }
    return { trained: true, n, pos, weights: w, featNames: PPL_FEATS, acc: correct / n, mu, sd };
  }

  /* ---------- K-MEANS fire clustering (lat/lon, haversine-ish) ---------- */
  function kmeansFires(fires, kMax = 4) {
    if (fires.length < 6) return [];
    const k = Math.min(kMax, Math.max(2, Math.round(Math.sqrt(fires.length / 12))));
    let cents = fires.slice(0, k).map(f => [f.lat, f.lon]);
    let assign = new Array(fires.length).fill(0);
    for (let iter = 0; iter < 24; iter++) {
      let moved = false;
      fires.forEach((f, i) => {
        let best = 0, bd = 1e18;
        cents.forEach((c, j) => {
          const dLat = f.lat - c[0], dLon = (f.lon - c[1]) * Math.cos(f.lat * Math.PI / 180);
          const d = dLat * dLat + dLon * dLon;
          if (d < bd) { bd = d; best = j; }
        });
        if (assign[i] !== best) { assign[i] = best; moved = true; }
      });
      cents = cents.map((c, j) => {
        const members = fires.filter((_, i) => assign[i] === j);
        if (!members.length) return c;
        return [members.reduce((s, f) => s + f.lat, 0) / members.length,
                members.reduce((s, f) => s + f.lon, 0) / members.length];
      });
      if (!moved) break;
    }
    return cents.map((c, j) => ({
      lat: c[0], lon: c[1],
      count: fires.filter((_, i) => assign[i] === j).length,
    })).filter(c => c.count > 0).sort((a, b) => b.count - a.count);
  }

  return { trainNowcast, sentinel, trainPersonal, kmeansFires };
})();
