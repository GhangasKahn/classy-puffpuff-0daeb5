# Orbital Prime — handoff

1. **Runnable project.** `/orbital-prime/` (also `/orbital`). Serve the folder; ES modules will not load from `file://`. Installable as a PWA over HTTPS — the service worker caches the app shell only and never caches live telemetry (stale data must never present as live).

2. **Governing concept.** The instrument between you and the sky.

3. **Signature interaction.** ISS lock writes AZ/EL/RANGE onto the plate, places a pip on the sky plot, and speaks FACE (cardinal, elevation, fist rule). AR path is optional glass for the same bearing.

4. **Motion inventory.** 12. See `MOTION_AND_COMPOSITION.md`.

5. **Public data sources used.**
   - Where The ISS At ` /v1/satellites/25544`
   - Celestrak GP (ISS TLE; Starship NAME query)
   - satellite.js SGP4 (CDN)
   - Open-Meteo current + hourly
   - RainViewer maps + tiles
   - NOAA SWPC planetary K-index (1-minute)

6. **Known limits.**
   - Camera HUD needs HTTPS. `content://` and `file://` stay FACE-only.
   - Celestrak may fail CORS in some browsers; passes then go unread while ISS lock still uses Where The ISS At.
   - Device compass heading is often missing or biased on desktop; FACE azimuth remains the command.
   - Magnitude is an estimate, labeled EST.
   - Starship is an empty catalog slot unless Celestrak has elements.
   - Mast is not sticky so FACE is never covered.

7. **Rubric (final audit).** No dimension below 8. Mean 8.6. See `AUDIT.md`.

8. **Not added.** Starlink trains, extra satellite programs, accounts, social, chat, secret APIs, blog, shop, waitlist, 3D Earth WebGL, fake live counts, extra marketing pages, scroll-jacking, native app rewrite.

No award is claimed. The plate was built and measured. It is not perfect.
