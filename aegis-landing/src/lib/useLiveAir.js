import { useEffect, useState } from "react";

/* The landing page reads the real sky — same sources as the instrument.
   Default location matches the app: Kenmore / Buffalo, NY. */
const LAT = 42.9656, LON = -78.8703;

export default function useLiveAir() {
  const [live, setLive] = useState({
    ready: false,
    aqi: null, pm25: null, aod: null,
    windSpd: null, windDir: null, temp: null,
  });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [wx, aq] = await Promise.all([
          fetch(`https://api.open-meteo.com/v1/forecast?latitude=${LAT}&longitude=${LON}&current=temperature_2m,wind_speed_10m,wind_direction_10m&timezone=auto`).then(r => r.json()),
          fetch(`https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${LAT}&longitude=${LON}&current=us_aqi,pm2_5,aerosol_optical_depth&timezone=auto`).then(r => r.json()),
        ]);
        if (cancelled) return;
        setLive({
          ready: true,
          aqi: aq?.current?.us_aqi ?? null,
          pm25: aq?.current?.pm2_5 ?? null,
          aod: aq?.current?.aerosol_optical_depth ?? null,
          windSpd: wx?.current?.wind_speed_10m ?? null,
          windDir: wx?.current?.wind_direction_10m ?? null,
          temp: wx?.current?.temperature_2m ?? null,
        });
      } catch {
        if (!cancelled) setLive(l => ({ ...l, ready: true }));
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return live;
}

export function compass16(deg) {
  if (deg == null) return "—";
  const pts = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"];
  return pts[Math.round(deg / 22.5) % 16];
}
