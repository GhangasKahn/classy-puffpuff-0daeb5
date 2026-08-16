/* Pass quality and ISS residual.
   Logistic scorer on live features. Prior coefficients, not a chatbot,
   not fitted on synthetic history. Residual is SGP4 vs WhereTheISS. */

const RE_KM = 6378.137;

export function sigmoid(z) {
  if (z > 20) return 1;
  if (z < -20) return 0;
  return 1 / (1 + Math.exp(-z));
}

/**
 * Features (all measured or propagated, never invented):
 *   elNorm     peak elevation / 80°, capped
 *   magNorm    brighter ISS ≈ 1 (mag −2 → 1, mag +4 → 0)
 *   clear      1 − cloud/100
 *   dry        1 if precip 0, else decays
 *   visNorm    visibility / 20 km, capped
 *   naked      1 if night + illuminated + el≥10
 *   day        1 if sun ≥ −6°
 *   eclipsed   1 if in shadow
 *
 * logit = −1.15 + 2.35 el + 1.70 mag + 2.10 clear + 1.40 dry
 *         + 0.70 vis + 2.00 naked − 1.60 day − 2.80 eclipsed
 */
export function scorePass(p, wx = {}, kp = null) {
  const elNorm = Math.max(0, Math.min(1, (p.maxEl ?? 0) / 80));
  const mag = p.mag;
  const magNorm = mag == null ? 0.5 : Math.max(0, Math.min(1, (4 - mag) / 6));
  const cloud = wx.cloud ?? wx.cloud_cover;
  const clear = cloud == null ? 0.5 : Math.max(0, Math.min(1, 1 - cloud / 100));
  const precip = wx.precip ?? wx.precipitation ?? 0;
  const dry = precip <= 0 ? 1 : precip < 0.2 ? 0.45 : precip < 1 ? 0.15 : 0;
  const vis = wx.vis ?? wx.visibility;
  const visNorm = vis == null ? 0.5 : Math.max(0, Math.min(1, vis / 20000));
  const naked = p.eye === "NAKED-EYE" ? 1 : 0;
  const day = p.eye === "DAY" ? 1 : 0;
  const eclipsed = p.eye === "ECLIPSED" || p.eclipsed ? 1 : 0;
  const kpPen = kp != null && kp >= 7 ? 0.15 : 0;

  const z =
    -1.15 +
    2.35 * elNorm +
    1.70 * magNorm +
    2.10 * clear +
    1.40 * dry +
    0.70 * visNorm +
    2.00 * naked -
    1.60 * day -
    2.80 * eclipsed -
    kpPen;

  const pGo = sigmoid(z);
  return {
    p: pGo,
    pct: Math.round(pGo * 100),
    z,
    features: { elNorm, magNorm, clear, dry, visNorm, naked, day, eclipsed }
  };
}

export function haversineKm(lat1, lon1, lat2, lon2) {
  const D = Math.PI / 180;
  const φ1 = lat1 * D, φ2 = lat2 * D;
  const dφ = (lat2 - lat1) * D;
  const dλ = (lon2 - lon1) * D;
  const a = Math.sin(dφ / 2) ** 2 + Math.cos(φ1) * Math.cos(φ2) * Math.sin(dλ / 2) ** 2;
  return 2 * RE_KM * Math.asin(Math.min(1, Math.sqrt(a)));
}

/** 3-D residual between live ISS and SGP4 at the same moment. */
export function issResidual(iss, sgp4) {
  if (!iss || !sgp4) return null;
  const ground = haversineKm(iss.latitude, iss.longitude, sgp4.lat, sgp4.lon);
  const dAlt = Math.abs((iss.altitude ?? 0) - (sgp4.altKm ?? 0));
  const km = Math.hypot(ground, dAlt);
  let grade = "LOCK";
  if (km > 80) grade = "STALE";
  else if (km > 25) grade = "DRIFT";
  return { km, ground, dAlt, grade };
}

export function wxSlice(hourly, ms) {
  if (!hourly?.time) return {};
  const iso = new Date(ms).toISOString().slice(0, 13);
  let idx = hourly.time.findIndex((t) => t.startsWith(iso));
  if (idx < 0) idx = hourly.time.findIndex((t) => new Date(t).getTime() >= ms);
  if (idx < 0) return {};
  return {
    cloud: hourly.cloud_cover?.[idx],
    precip: hourly.precipitation?.[idx],
    vis: hourly.visibility?.[idx]
  };
}
