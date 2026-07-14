/**
 * BEDROCK Quant Engine — God-tier client math stack
 * Pure JS. No network. Deterministic when seeded.
 * Hedge-fund / QPE primitives for the LAB surface.
 *
 * Modules: RNG · distributions · stochastic calculus · portfolio ·
 * entropy/LLN · chaos · game theory · options/greeks · capital rotation ·
 * ML · RL · convexity
 */
(function (root) {
  "use strict";

  /* ===================== seeded RNG (Mulberry32) ===================== */
  function makeRng(seed) {
    var s = (seed >>> 0) || 1;
    return function () {
      s |= 0;
      s = (s + 0x6d2b79f5) | 0;
      var t = Math.imul(s ^ (s >>> 15), 1 | s);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function gauss(rng) {
    var u = 0, v = 0;
    while (u === 0) u = rng();
    while (v === 0) v = rng();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }

  function studentT(rng, df) {
    var z = gauss(rng);
    var s = 0;
    for (var i = 0; i < df; i++) {
      var g = gauss(rng);
      s += g * g;
    }
    return z / Math.sqrt(s / df);
  }

  function poisson(rng, lambda) {
    var L = Math.exp(-lambda), k = 0, p = 1;
    do {
      k++;
      p *= rng();
    } while (p > L);
    return k - 1;
  }

  /* ===================== linear algebra (small n) ===================== */
  function zeros(n) {
    return Array(n).fill(0);
  }
  function matZeros(n, m) {
    var A = [];
    for (var i = 0; i < n; i++) A.push(zeros(m));
    return A;
  }
  function dot(a, b) {
    var s = 0;
    for (var i = 0; i < a.length; i++) s += a[i] * b[i];
    return s;
  }
  function matVec(A, x) {
    return A.map(function (row) {
      return dot(row, x);
    });
  }
  function transpose(A) {
    var n = A.length, m = A[0].length, T = matZeros(m, n);
    for (var i = 0; i < n; i++) for (var j = 0; j < m; j++) T[j][i] = A[i][j];
    return T;
  }
  function matMul(A, B) {
    var n = A.length, p = B[0].length, m = B.length, C = matZeros(n, p);
    for (var i = 0; i < n; i++)
      for (var j = 0; j < p; j++) {
        var s = 0;
        for (var k = 0; k < m; k++) s += A[i][k] * B[k][j];
        C[i][j] = s;
      }
    return C;
  }
  /** Cholesky of SPD matrix; returns L (lower) or null */
  function cholesky(S) {
    var n = S.length, L = matZeros(n, n);
    for (var i = 0; i < n; i++) {
      for (var j = 0; j <= i; j++) {
        var s = S[i][j];
        for (var k = 0; k < j; k++) s -= L[i][k] * L[j][k];
        if (i === j) {
          if (s <= 1e-14) return null;
          L[i][j] = Math.sqrt(s);
        } else L[i][j] = s / L[j][j];
      }
    }
    return L;
  }
  function solveLower(L, b) {
    var n = L.length, x = zeros(n);
    for (var i = 0; i < n; i++) {
      var s = b[i];
      for (var j = 0; j < i; j++) s -= L[i][j] * x[j];
      x[i] = s / L[i][i];
    }
    return x;
  }
  function solveUpper(U, b) {
    var n = U.length, x = zeros(n);
    for (var i = n - 1; i >= 0; i--) {
      var s = b[i];
      for (var j = i + 1; j < n; j++) s -= U[i][j] * x[j];
      x[i] = s / U[i][i];
    }
    return x;
  }
  function solveSPD(S, b) {
    var L = cholesky(S);
    if (!L) return null;
    var y = solveLower(L, b);
    return solveUpper(transpose(L), y);
  }
  function invSPD(S) {
    var n = S.length, I = matZeros(n, n), out = matZeros(n, n);
    for (var i = 0; i < n; i++) I[i][i] = 1;
    for (var c = 0; c < n; c++) {
      var col = solveSPD(S, I[c]);
      if (!col) return null;
      for (var r = 0; r < n; r++) out[r][c] = col[r];
    }
    return out;
  }

  /* ===================== stats ===================== */
  function mean(xs) {
    if (!xs.length) return 0;
    var s = 0;
    for (var i = 0; i < xs.length; i++) s += xs[i];
    return s / xs.length;
  }
  function variance(xs, ddof) {
    ddof = ddof == null ? 1 : ddof;
    var m = mean(xs), s = 0;
    for (var i = 0; i < xs.length; i++) {
      var d = xs[i] - m;
      s += d * d;
    }
    return s / Math.max(1, xs.length - ddof);
  }
  function std(xs, ddof) {
    return Math.sqrt(variance(xs, ddof));
  }
  function percentile(xs, p) {
    var a = xs.slice().sort(function (x, y) {
      return x - y;
    });
    if (!a.length) return NaN;
    var i = Math.min(a.length - 1, Math.max(0, Math.floor(p * (a.length - 1))));
    return a[i];
  }
  function covMatrix(returnsCols) {
    // returnsCols: array of series (each asset's returns), same length
    var n = returnsCols.length, T = returnsCols[0].length;
    var means = returnsCols.map(mean);
    var S = matZeros(n, n);
    for (var i = 0; i < n; i++)
      for (var j = i; j < n; j++) {
        var s = 0;
        for (var t = 0; t < T; t++) s += (returnsCols[i][t] - means[i]) * (returnsCols[j][t] - means[j]);
        S[i][j] = S[j][i] = s / Math.max(1, T - 1);
      }
    return S;
  }
  function corrMatrix(S) {
    var n = S.length, R = matZeros(n, n);
    for (var i = 0; i < n; i++)
      for (var j = 0; j < n; j++) {
        var d = Math.sqrt(S[i][i] * S[j][j]);
        R[i][j] = d > 0 ? S[i][j] / d : 0;
      }
    return R;
  }

  /* ===================== entropy · LLN ===================== */
  function shannonEntropy(weights) {
    var H = 0;
    for (var i = 0; i < weights.length; i++) {
      var w = weights[i];
      if (w > 0) H -= w * Math.log(w);
    }
    return H;
  }
  function effectiveBets(weights) {
    return Math.exp(shannonEntropy(weights));
  }
  function renyiEntropy(weights, alpha) {
    alpha = alpha == null ? 2 : alpha;
    if (Math.abs(alpha - 1) < 1e-9) return shannonEntropy(weights);
    var s = 0;
    for (var i = 0; i < weights.length; i++) if (weights[i] > 0) s += Math.pow(weights[i], alpha);
    return Math.log(s) / (1 - alpha);
  }
  function klDivergence(p, q) {
    var d = 0;
    for (var i = 0; i < p.length; i++) {
      if (p[i] > 0) d += p[i] * Math.log(p[i] / Math.max(q[i], 1e-15));
    }
    return d;
  }
  /** Law of large numbers: running mean of i.i.d. samples vs true μ */
  function llnExperiment(opts) {
    opts = opts || {};
    var rng = makeRng(opts.seed || 42);
    var n = opts.n || 2000;
    var trueMu = opts.mu != null ? opts.mu : 0.08;
    var trueSig = opts.sigma != null ? opts.sigma : 0.15;
    var run = [], err = [];
    var sum = 0;
    for (var i = 1; i <= n; i++) {
      sum += trueMu + trueSig * gauss(rng);
      var m = sum / i;
      run.push(m);
      err.push(Math.abs(m - trueMu));
    }
    return {
      trueMu: trueMu,
      runningMean: run,
      absError: err,
      finalMean: run[n - 1],
      finalError: err[n - 1],
      chebyshevBound: function (eps) {
        return trueSig * trueSig / (eps * eps); // n needed so P(|X̄−μ|≥ε) ≤ σ²/(nε²)
      },
    };
  }

  /* ===================== stochastic calculus ===================== */
  /** Geometric Brownian Motion path */
  function gbmPath(opts) {
    opts = opts || {};
    var rng = makeRng(opts.seed || 1);
    var S0 = opts.S0 != null ? opts.S0 : 100;
    var mu = opts.mu != null ? opts.mu : 0.08;
    var sigma = opts.sigma != null ? opts.sigma : 0.2;
    var T = opts.T != null ? opts.T : 1;
    var steps = opts.steps || 252;
    var dt = T / steps;
    var path = [S0], S = S0;
    for (var i = 0; i < steps; i++) {
      S = S * Math.exp((mu - 0.5 * sigma * sigma) * dt + sigma * Math.sqrt(dt) * gauss(rng));
      path.push(S);
    }
    return path;
  }
  /** Merton jump-diffusion */
  function mertonJumpPath(opts) {
    opts = opts || {};
    var rng = makeRng(opts.seed || 2);
    var S0 = opts.S0 != null ? opts.S0 : 100;
    var mu = opts.mu != null ? opts.mu : 0.08;
    var sigma = opts.sigma != null ? opts.sigma : 0.2;
    var lambda = opts.lambda != null ? opts.lambda : 0.5; // jumps / year
    var jumpMu = opts.jumpMu != null ? opts.jumpMu : -0.1;
    var jumpSig = opts.jumpSig != null ? opts.jumpSig : 0.2;
    var T = opts.T != null ? opts.T : 1;
    var steps = opts.steps || 252;
    var dt = T / steps;
    var k = Math.exp(jumpMu + 0.5 * jumpSig * jumpSig) - 1; // compensator E[J-1]
    var path = [S0], S = S0;
    for (var i = 0; i < steps; i++) {
      var nJ = poisson(rng, lambda * dt);
      var jSum = 0;
      for (var j = 0; j < nJ; j++) jSum += jumpMu + jumpSig * gauss(rng);
      S =
        S *
        Math.exp((mu - lambda * k - 0.5 * sigma * sigma) * dt + sigma * Math.sqrt(dt) * gauss(rng) + jSum);
      path.push(S);
    }
    return path;
  }
  /** Ornstein–Uhlenbeck (mean-reverting rates / residual) */
  function ouPath(opts) {
    opts = opts || {};
    var rng = makeRng(opts.seed || 3);
    var x0 = opts.x0 != null ? opts.x0 : 0;
    var theta = opts.theta != null ? opts.theta : 0.5; // speed
    var mu = opts.mu != null ? opts.mu : 0;
    var sigma = opts.sigma != null ? opts.sigma : 0.1;
    var T = opts.T != null ? opts.T : 5;
    var steps = opts.steps || 500;
    var dt = T / steps;
    var path = [x0], x = x0;
    for (var i = 0; i < steps; i++) {
      x = x + theta * (mu - x) * dt + sigma * Math.sqrt(dt) * gauss(rng);
      path.push(x);
    }
    return path;
  }
  /** Heston stochastic vol (Euler–Maruyama, reflecting vol) */
  function hestonPath(opts) {
    opts = opts || {};
    var rng = makeRng(opts.seed || 4);
    var S0 = opts.S0 != null ? opts.S0 : 100;
    var v0 = opts.v0 != null ? opts.v0 : 0.04;
    var mu = opts.mu != null ? opts.mu : 0.05;
    var kappa = opts.kappa != null ? opts.kappa : 2;
    var theta = opts.theta != null ? opts.theta : 0.04;
    var xi = opts.xi != null ? opts.xi : 0.3;
    var rho = opts.rho != null ? opts.rho : -0.7;
    var T = opts.T != null ? opts.T : 1;
    var steps = opts.steps || 252;
    var dt = T / steps;
    var S = S0, v = v0, pathS = [S0], pathV = [v0];
    for (var i = 0; i < steps; i++) {
      var z1 = gauss(rng);
      var z2 = rho * z1 + Math.sqrt(1 - rho * rho) * gauss(rng);
      v = Math.max(1e-8, v + kappa * (theta - v) * dt + xi * Math.sqrt(Math.max(v, 0) * dt) * z2);
      S = S * Math.exp((mu - 0.5 * v) * dt + Math.sqrt(v * dt) * z1);
      pathS.push(S);
      pathV.push(v);
    }
    return { S: pathS, v: pathV };
  }

  /* ===================== portfolio engineering ===================== */
  function normalizeWeights(w) {
    var s = 0, i;
    for (i = 0; i < w.length; i++) s += Math.max(0, w[i]);
    if (s <= 0) return w.map(function () {
      return 1 / w.length;
    });
    return w.map(function (x) {
      return Math.max(0, x) / s;
    });
  }
  function portReturn(w, mu) {
    return dot(w, mu);
  }
  function portVar(w, S) {
    return dot(w, matVec(S, w));
  }
  function sharpe(w, mu, S, rf) {
    rf = rf || 0;
    var sig = Math.sqrt(Math.max(portVar(w, S), 0));
    return sig > 0 ? (portReturn(w, mu) - rf) / sig : 0;
  }
  /** Analytic max-Sharpe / tangency (no short if project) */
  function maxSharpe(mu, S, rf, longOnly) {
    rf = rf || 0;
    var n = mu.length;
    var excess = mu.map(function (m) {
      return m - rf;
    });
    var inv = invSPD(S);
    if (!inv) {
      return normalizeWeights(zeros(n).map(function () {
        return 1;
      }));
    }
    var raw = matVec(inv, excess);
    if (longOnly) raw = raw.map(function (x) {
      return Math.max(0, x);
    });
    return normalizeWeights(raw);
  }
  /** Minimum variance */
  function minVariance(S, longOnly) {
    var n = S.length;
    var ones = zeros(n).map(function () {
      return 1;
    });
    var inv = invSPD(S);
    if (!inv) return normalizeWeights(ones);
    var raw = matVec(inv, ones);
    if (longOnly) raw = raw.map(function (x) {
      return Math.max(0, x);
    });
    return normalizeWeights(raw);
  }
  /** Risk parity (iterative): w_i * (Σw)_i equal */
  function riskParity(S, iters) {
    iters = iters || 500;
    var n = S.length;
    var w = zeros(n).map(function () {
      return 1 / n;
    });
    for (var t = 0; t < iters; t++) {
      var mrc = matVec(S, w);
      var rc = w.map(function (wi, i) {
        return wi * mrc[i];
      });
      var target = mean(rc);
      w = w.map(function (wi, i) {
        return wi * Math.sqrt(target / Math.max(rc[i], 1e-18));
      });
      w = normalizeWeights(w);
    }
    return w;
  }
  /** Kelly / fractional Kelly for multi-asset (approx: Σ^{-1} μ) */
  function kellyWeights(mu, S, fraction) {
    fraction = fraction == null ? 0.5 : fraction;
    var inv = invSPD(S);
    if (!inv) return normalizeWeights(mu.map(function () {
      return 1;
    }));
    var raw = matVec(inv, mu).map(function (x) {
      return x * fraction;
    });
    // allow leverage but soft-cap gross
    var gross = raw.reduce(function (a, b) {
      return a + Math.abs(b);
    }, 0);
    if (gross > 2) raw = raw.map(function (x) {
      return (x / gross) * 2;
    });
    return raw;
  }
  /** Historical CVaR (Expected Shortfall) of portfolio returns */
  function cvar(returns, alpha) {
    alpha = alpha == null ? 0.05 : alpha;
    var a = returns.slice().sort(function (x, y) {
      return x - y;
    });
    var k = Math.max(1, Math.floor(alpha * a.length));
    var s = 0;
    for (var i = 0; i < k; i++) s += a[i];
    return { var: a[k - 1], cvar: s / k };
  }
  /** Simulate correlated asset returns via Cholesky */
  function simulateReturns(mu, S, nObs, seed) {
    var rng = makeRng(seed || 7);
    var n = mu.length;
    var L = cholesky(S);
    if (!L) {
      // fallback diagonal
      L = matZeros(n, n);
      for (var i = 0; i < n; i++) L[i][i] = Math.sqrt(Math.max(S[i][i], 1e-12));
    }
    var cols = [];
    for (var a = 0; a < n; a++) cols.push([]);
    for (var t = 0; t < nObs; t++) {
      var z = zeros(n).map(function () {
        return gauss(rng);
      });
      var e = matVec(L, z);
      for (var j = 0; j < n; j++) cols[j].push(mu[j] + e[j]);
    }
    return cols;
  }

  /* ===================== options · greeks · hedge ===================== */
  function normCdf(x) {
    // Abramowitz–Stegun approximation
    var t = 1 / (1 + 0.2316419 * Math.abs(x));
    var d = 0.3989422804014327 * Math.exp(-0.5 * x * x);
    var p =
      d *
      t *
      (0.319381530 +
        t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))));
    return x > 0 ? 1 - p : p;
  }
  function normPdf(x) {
    return Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
  }
  function blackScholes(opts) {
    var S = opts.S, K = opts.K, T = opts.T, r = opts.r != null ? opts.r : 0.03, q = opts.q || 0, sigma = opts.sigma, type = opts.type || "call";
    if (T <= 0) {
      var intrinsic = type === "call" ? Math.max(S - K, 0) : Math.max(K - S, 0);
      return { price: intrinsic, delta: type === "call" ? (S > K ? 1 : 0) : (S < K ? -1 : 0), gamma: 0, vega: 0, theta: 0, rho: 0 };
    }
    var sqrtT = Math.sqrt(T);
    var d1 = (Math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * sqrtT);
    var d2 = d1 - sigma * sqrtT;
    var dfq = Math.exp(-q * T), dfr = Math.exp(-r * T);
    var price =
      type === "call"
        ? S * dfq * normCdf(d1) - K * dfr * normCdf(d2)
        : K * dfr * normCdf(-d2) - S * dfq * normCdf(-d1);
    var delta = type === "call" ? dfq * normCdf(d1) : dfq * (normCdf(d1) - 1);
    var gamma = (dfq * normPdf(d1)) / (S * sigma * sqrtT);
    var vega = (S * dfq * normPdf(d1) * sqrtT) / 100; // per 1 vol point
    var theta =
      type === "call"
        ? (-(S * dfq * normPdf(d1) * sigma) / (2 * sqrtT) - r * K * dfr * normCdf(d2) + q * S * dfq * normCdf(d1)) / 365
        : (-(S * dfq * normPdf(d1) * sigma) / (2 * sqrtT) + r * K * dfr * normCdf(-d2) - q * S * dfq * normCdf(-d1)) / 365;
    var rho =
      type === "call"
        ? (K * T * dfr * normCdf(d2)) / 100
        : (-K * T * dfr * normCdf(-d2)) / 100;
    return { price: price, delta: delta, gamma: gamma, vega: vega, theta: theta, rho: rho, d1: d1, d2: d2 };
  }
  /** Static delta-hedge: shares to hold per short option */
  function deltaHedgeLeg(bs, contracts, multiplier) {
    contracts = contracts == null ? 1 : contracts;
    multiplier = multiplier || 100;
    return {
      shares: -bs.delta * contracts * multiplier,
      gammaShares: -bs.gamma * contracts * multiplier,
      note: "short option → hedge with +Δ shares (sign flips for long option)",
    };
  }

  /* ===================== bond convexity ===================== */
  function bondCashflows(face, couponRate, years, freq) {
    freq = freq || 2;
    var n = Math.round(years * freq);
    var c = (face * couponRate) / freq;
    var cfs = [];
    for (var i = 1; i <= n; i++) cfs.push({ t: i / freq, cf: i === n ? c + face : c });
    return cfs;
  }
  function bondMetrics(face, couponRate, years, ytm, freq) {
    freq = freq || 2;
    var cfs = bondCashflows(face, couponRate, years, freq);
    var price = 0, dur = 0, conv = 0;
    for (var i = 0; i < cfs.length; i++) {
      var df = Math.pow(1 + ytm / freq, -cfs[i].t * freq);
      var pv = cfs[i].cf * df;
      price += pv;
      dur += cfs[i].t * pv;
      conv += cfs[i].t * (cfs[i].t + 1 / freq) * pv;
    }
    var macD = dur / price;
    var modD = macD / (1 + ytm / freq);
    var convexity = conv / (price * Math.pow(1 + ytm / freq, 2));
    return { price: price, macaulay: macD, modified: modD, convexity: convexity };
  }

  /* ===================== chaos theory ===================== */
  function logisticMap(opts) {
    opts = opts || {};
    var r = opts.r != null ? opts.r : 3.9;
    var x = opts.x0 != null ? opts.x0 : 0.5;
    var n = opts.n || 200;
    var path = [x];
    for (var i = 0; i < n; i++) {
      x = r * x * (1 - x);
      path.push(x);
    }
    return path;
  }
  /** Largest Lyapunov exponent estimate for logistic map */
  function lyapunovLogistic(r, n, x0) {
    n = n || 5000;
    x0 = x0 == null ? 0.5 : x0;
    var x = x0, sum = 0;
    for (var i = 0; i < n; i++) {
      x = r * x * (1 - x);
      sum += Math.log(Math.abs(r - 2 * r * x) + 1e-15);
    }
    return sum / n;
  }
  /** Lorenz attractor (Euler) — returns {x,y,z} */
  function lorenz(opts) {
    opts = opts || {};
    var sigma = opts.sigma != null ? opts.sigma : 10;
    var rho = opts.rho != null ? opts.rho : 28;
    var beta = opts.beta != null ? opts.beta : 8 / 3;
    var dt = opts.dt || 0.01;
    var steps = opts.steps || 3000;
    var x = opts.x0 != null ? opts.x0 : 0.1;
    var y = opts.y0 != null ? opts.y0 : 0;
    var z = opts.z0 != null ? opts.z0 : 0;
    var X = [x], Y = [y], Z = [z];
    for (var i = 0; i < steps; i++) {
      var dx = sigma * (y - x);
      var dy = x * (rho - z) - y;
      var dz = x * y - beta * z;
      x += dx * dt;
      y += dy * dt;
      z += dz * dt;
      X.push(x);
      Y.push(y);
      Z.push(z);
    }
    return { x: X, y: Y, z: Z };
  }

  /* ===================== game theory ===================== */
  /** 2x2 zero-sum: solve mixed Nash for row player payoff matrix A */
  function mixedNash2x2(A) {
    // A = [[a,b],[c,d]] row payoffs
    var a = A[0][0], b = A[0][1], c = A[1][0], d = A[1][1];
    var den = a - b - c + d;
    if (Math.abs(den) < 1e-12) {
      return { p: [0.5, 0.5], q: [0.5, 0.5], value: (a + d) / 2, pure: false };
    }
    var q = (d - c) / den; // col plays col0 with q
    var p = (d - b) / den; // row plays row0 with p
    q = Math.max(0, Math.min(1, q));
    p = Math.max(0, Math.min(1, p));
    var value = p * q * a + p * (1 - q) * b + (1 - p) * q * c + (1 - p) * (1 - q) * d;
    return { p: [p, 1 - p], q: [q, 1 - q], value: value, pure: false };
  }
  /** Hawk–Dove / Chicken stylized capital contest */
  function hawkDove(V, C) {
    V = V == null ? 2 : V;
    C = C == null ? 4 : C;
    // payoff matrix for row: Hawk vs Dove
    var A = [
      [(V - C) / 2, V],
      [0, V / 2],
    ];
    var nash = mixedNash2x2(A);
    return { matrix: A, nash: nash, interpretation: "p[0]=P(Hawk) in ESS mixed strategy" };
  }
  /** Portfolio game: aggressive vs defensive allocation vs market states */
  function allocationGame() {
    // rows: Aggressive / Defensive; cols: Bull / Bear
    var A = [
      [0.25, -0.35],
      [0.08, -0.05],
    ];
    return { matrix: A, nash: mixedNash2x2(A), labels: { rows: ["Aggressive", "Defensive"], cols: ["Bull", "Bear"] } };
  }

  /* ===================== capital rotation ===================== */
  /**
   * Regime from trailing return / vol → rotate weights across Risk-On / Neutral / Risk-Off sleeves
   * sleeves: { riskOn, core, defense } target mixes
   */
  function capitalRotation(opts) {
    opts = opts || {};
    var ret = opts.trailingReturn != null ? opts.trailingReturn : 0.05;
    var vol = opts.trailingVol != null ? opts.trailingVol : 0.15;
    var sharpeProxy = vol > 0 ? ret / vol : 0;
    var regime;
    if (sharpeProxy > 0.5 && vol < 0.22) regime = "RISK_ON";
    else if (sharpeProxy < 0 || vol > 0.35) regime = "RISK_OFF";
    else regime = "NEUTRAL";
    var sleeves = {
      RISK_ON: { equities: 0.7, credit: 0.15, cash: 0.05, hedge: 0.1 },
      NEUTRAL: { equities: 0.5, credit: 0.25, cash: 0.1, hedge: 0.15 },
      RISK_OFF: { equities: 0.25, credit: 0.25, cash: 0.3, hedge: 0.2 },
    };
    return {
      regime: regime,
      sharpeProxy: sharpeProxy,
      weights: sleeves[regime],
      note: "Heuristic sleeve rotation — not a prediction. Hedge sleeve = convexity budget (puts / long-vol).",
    };
  }

  /* ===================== ML (tiny, pure JS) ===================== */
  function ols(X, y) {
    // X: n×p (with intercept column if desired), y: n
    var Xt = transpose(X);
    var XtX = matMul(Xt, X);
    var Xty = matVec(Xt, y);
    // ridge tiny for stability
    for (var i = 0; i < XtX.length; i++) XtX[i][i] += 1e-8;
    var beta = solveSPD(XtX, Xty);
    if (!beta) return null;
    var yhat = matVec(X, beta);
    var ssRes = 0, ssTot = 0, ym = mean(y);
    for (var j = 0; j < y.length; j++) {
      ssRes += (y[j] - yhat[j]) * (y[j] - yhat[j]);
      ssTot += (y[j] - ym) * (y[j] - ym);
    }
    return { beta: beta, r2: ssTot > 0 ? 1 - ssRes / ssTot : 0, yhat: yhat };
  }
  /** Logistic regression via gradient descent */
  function logisticGD(X, y, opts) {
    opts = opts || {};
    var lr = opts.lr || 0.1, epochs = opts.epochs || 800, l2 = opts.l2 || 0.001;
    var p = X[0].length, n = X.length;
    var w = zeros(p);
    function sig(z) {
      return 1 / (1 + Math.exp(-Math.max(-30, Math.min(30, z))));
    }
    for (var e = 0; e < epochs; e++) {
      var grad = zeros(p);
      for (var i = 0; i < n; i++) {
        var pred = sig(dot(w, X[i]));
        var err = pred - y[i];
        for (var j = 0; j < p; j++) grad[j] += err * X[i][j];
      }
      for (var k = 0; k < p; k++) w[k] -= (lr / n) * (grad[k] + l2 * w[k]);
    }
    return { w: w, predict: function (x) {
      return sig(dot(w, x));
    } };
  }
  /** Tiny MLP: 1 hidden layer, tanh, MSE regression */
  function mlpTrain(X, y, opts) {
    opts = opts || {};
    var rng = makeRng(opts.seed || 99);
    var h = opts.hidden || 8, lr = opts.lr || 0.05, epochs = opts.epochs || 600;
    var n = X.length, din = X[0].length;
    var W1 = matZeros(h, din), b1 = zeros(h), W2 = zeros(h), b2 = 0;
    for (var i = 0; i < h; i++) {
      for (var j = 0; j < din; j++) W1[i][j] = (rng() * 2 - 1) * 0.5;
      W2[i] = (rng() * 2 - 1) * 0.5;
    }
    function forward(x) {
      var hid = zeros(h);
      for (var a = 0; a < h; a++) hid[a] = Math.tanh(dot(W1[a], x) + b1[a]);
      return { hid: hid, y: dot(W2, hid) + b2 };
    }
    for (var e = 0; e < epochs; e++) {
      for (var t = 0; t < n; t++) {
        var f = forward(X[t]);
        var err = f.y - y[t];
        // dW2
        for (var a2 = 0; a2 < h; a2++) {
          var dW2 = err * f.hid[a2];
          var dHid = err * W2[a2] * (1 - f.hid[a2] * f.hid[a2]);
          W2[a2] -= lr * dW2;
          b1[a2] -= lr * dHid;
          for (var j2 = 0; j2 < din; j2++) W1[a2][j2] -= lr * dHid * X[t][j2];
        }
        b2 -= lr * err;
      }
    }
    return {
      predict: function (x) {
        return forward(x).y;
      },
      forward: forward,
    };
  }

  /* ===================== RL ===================== */
  /** Multi-armed bandit UCB1 */
  function ucb1(rewardFn, arms, pulls, seed) {
    var rng = makeRng(seed || 11);
    var n = arms, counts = zeros(n), values = zeros(n), hist = [];
    for (var t = 0; t < pulls; t++) {
      var a, best = -Infinity;
      if (t < n) a = t;
      else {
        a = 0;
        for (var i = 0; i < n; i++) {
          var bonus = Math.sqrt((2 * Math.log(t + 1)) / counts[i]);
          var score = values[i] + bonus;
          if (score > best) {
            best = score;
            a = i;
          }
        }
      }
      var r = rewardFn(a, rng);
      counts[a]++;
      values[a] += (r - values[a]) / counts[a];
      hist.push({ t: t, arm: a, reward: r });
    }
    return { counts: counts, values: values, hist: hist };
  }
  /** Tabular Q-learning on synthetic regime MDP (cash / equity / hedge) */
  function qLearnCapital(opts) {
    opts = opts || {};
    var rng = makeRng(opts.seed || 13);
    var episodes = opts.episodes || 400;
    var actions = ["EQUITY", "BALANCED", "HEDGE"]; // capital posture
    var states = ["BULL", "CHOP", "BEAR"];
    var Q = {};
    states.forEach(function (s) {
      Q[s] = {};
      actions.forEach(function (a) {
        Q[s][a] = 0;
      });
    });
    var alpha = 0.15, gamma = 0.9, eps = 0.2;
    function reward(s, a, rng2) {
      var base =
        s === "BULL" ? { EQUITY: 0.12, BALANCED: 0.07, HEDGE: 0.02 } :
        s === "BEAR" ? { EQUITY: -0.15, BALANCED: -0.04, HEDGE: 0.08 } :
                       { EQUITY: 0.02, BALANCED: 0.03, HEDGE: 0.01 };
      return base[a] + 0.02 * gauss(rng2);
    }
    function nextState(s, rng2) {
      var u = rng2();
      if (s === "BULL") return u < 0.7 ? "BULL" : u < 0.9 ? "CHOP" : "BEAR";
      if (s === "BEAR") return u < 0.65 ? "BEAR" : u < 0.9 ? "CHOP" : "BULL";
      return u < 0.4 ? "CHOP" : u < 0.7 ? "BULL" : "BEAR";
    }
    var log = [];
    for (var e = 0; e < episodes; e++) {
      var s = states[Math.floor(rng() * 3)];
      for (var t = 0; t < 24; t++) {
        var a;
        if (rng() < eps) a = actions[Math.floor(rng() * 3)];
        else {
          a = actions[0];
          var best = -Infinity;
          for (var k = 0; k < actions.length; k++) {
            if (Q[s][actions[k]] > best) {
              best = Q[s][actions[k]];
              a = actions[k];
            }
          }
        }
        var r = reward(s, a, rng);
        var s2 = nextState(s, rng);
        var maxQ = Math.max(Q[s2].EQUITY, Q[s2].BALANCED, Q[s2].HEDGE);
        Q[s][a] += alpha * (r + gamma * maxQ - Q[s][a]);
        s = s2;
      }
      if (e % 50 === 0) log.push({ episode: e, Q: JSON.parse(JSON.stringify(Q)) });
    }
    var policy = {};
    states.forEach(function (s) {
      var bestA = actions[0], bestV = -Infinity;
      actions.forEach(function (a) {
        if (Q[s][a] > bestV) {
          bestV = Q[s][a];
          bestA = a;
        }
      });
      policy[s] = bestA;
    });
    return { Q: Q, policy: policy, log: log };
  }

  /* ===================== demo market factory ===================== */
  function demoUniverse(seed) {
    // 4 assets: Equity, Credit, Commodity, Hedge (long-vol-ish)
    var mu = [0.09, 0.045, 0.06, 0.02];
    var vols = [0.18, 0.06, 0.22, 0.28];
    var corr = [
      [1, 0.35, 0.25, -0.35],
      [0.35, 1, 0.1, -0.15],
      [0.25, 0.1, 1, -0.05],
      [-0.35, -0.15, -0.05, 1],
    ];
    var n = 4;
    var S = matZeros(n, n);
    for (var i = 0; i < n; i++)
      for (var j = 0; j < n; j++) S[i][j] = corr[i][j] * vols[i] * vols[j];
    var rets = simulateReturns(mu, S, 504, seed || 21); // ~2y daily
    return {
      names: ["EQUITY", "CREDIT", "COMMODITY", "HEDGE"],
      mu: mu,
      vols: vols,
      S: S,
      corr: corr,
      returns: rets,
    };
  }

  function portfolioSuite(seed) {
    var u = demoUniverse(seed);
    var wEq = normalizeWeights([1, 0, 0, 0]);
    var wMv = minVariance(u.S, true);
    var wRp = riskParity(u.S);
    var wMs = maxSharpe(u.mu, u.S, 0.02, true);
    var wKel = kellyWeights(u.mu, u.S, 0.25);
    var wKelN = normalizeWeights(wKel.map(function (x) {
      return Math.max(0, x);
    }));
    function metrics(w) {
      var pr = portReturn(w, u.mu);
      var pv = portVar(w, u.S);
      var pathR = [];
      for (var t = 0; t < u.returns[0].length; t++) {
        var r = 0;
        for (var i = 0; i < w.length; i++) r += w[i] * u.returns[i][t];
        pathR.push(r);
      }
      var es = cvar(pathR, 0.05);
      return {
        weights: w,
        mu: pr,
        vol: Math.sqrt(pv),
        sharpe: sharpe(w, u.mu, u.S, 0.02),
        entropy: shannonEntropy(w),
        effectiveBets: effectiveBets(w),
        var5: es.var,
        cvar5: es.cvar,
      };
    }
    return {
      universe: u,
      books: {
        equityHeavy: metrics(wEq),
        minVar: metrics(wMv),
        riskParity: metrics(wRp),
        maxSharpe: metrics(wMs),
        fractionalKelly: metrics(wKelN),
      },
      rotation: capitalRotation({
        trailingReturn: mean(u.returns[0].slice(-63)),
        trailingVol: std(u.returns[0].slice(-63)) * Math.sqrt(252),
      }),
    };
  }

  root.BedrockQuant = {
    makeRng: makeRng,
    gauss: gauss,
    studentT: studentT,
    mean: mean,
    std: std,
    variance: variance,
    percentile: percentile,
    covMatrix: covMatrix,
    corrMatrix: corrMatrix,
    shannonEntropy: shannonEntropy,
    renyiEntropy: renyiEntropy,
    effectiveBets: effectiveBets,
    klDivergence: klDivergence,
    llnExperiment: llnExperiment,
    gbmPath: gbmPath,
    mertonJumpPath: mertonJumpPath,
    ouPath: ouPath,
    hestonPath: hestonPath,
    normalizeWeights: normalizeWeights,
    portReturn: portReturn,
    portVar: portVar,
    sharpe: sharpe,
    maxSharpe: maxSharpe,
    minVariance: minVariance,
    riskParity: riskParity,
    kellyWeights: kellyWeights,
    cvar: cvar,
    simulateReturns: simulateReturns,
    blackScholes: blackScholes,
    deltaHedgeLeg: deltaHedgeLeg,
    bondMetrics: bondMetrics,
    logisticMap: logisticMap,
    lyapunovLogistic: lyapunovLogistic,
    lorenz: lorenz,
    mixedNash2x2: mixedNash2x2,
    hawkDove: hawkDove,
    allocationGame: allocationGame,
    capitalRotation: capitalRotation,
    ols: ols,
    logisticGD: logisticGD,
    mlpTrain: mlpTrain,
    ucb1: ucb1,
    qLearnCapital: qLearnCapital,
    demoUniverse: demoUniverse,
    portfolioSuite: portfolioSuite,
    version: "1.0.0-godtier",
  };
})(typeof window !== "undefined" ? window : globalThis);
