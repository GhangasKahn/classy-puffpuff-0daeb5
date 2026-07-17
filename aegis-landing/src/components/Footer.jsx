const APP_URL = "/aegis-air-mvp/";

export default function Footer() {
  return (
    <footer className="rounded-t-[3.5rem] border-t border-line bg-deep">
      <div className="mx-auto grid max-w-6xl gap-12 px-6 py-16 md:grid-cols-4 md:px-10">
        <div className="md:col-span-2">
          <div className="text-xl font-extrabold tracking-tight">
            Aegis <span className="text-air">Air</span>
          </div>
          <p className="mt-3 max-w-sm text-sm leading-relaxed text-muted">
            A personal exposure instrument for wildfire smoke. Local-first, transparent, free.
            Not a medical device — and honest about it.
          </p>
          <div className="mt-6 flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.2em] text-muted">
            <span className="pulse-dot inline-block h-2 w-2 rounded-full bg-[#34d399]" aria-hidden="true" />
            System operational — models responding
          </div>
        </div>
        <nav aria-label="Site">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted">Instrument</div>
          <ul className="mt-4 space-y-2.5 text-sm">
            <li><a className="lift text-ink/80 hover:text-ink" href={APP_URL}>Open the app</a></li>
            <li><a className="lift text-ink/80 hover:text-ink" href="#instrument">The three dials</a></li>
            <li><a className="lift text-ink/80 hover:text-ink" href="#method">The method</a></li>
            <li><a className="lift text-ink/80 hover:text-ink" href="#proof">The record</a></li>
          </ul>
        </nav>
        <nav aria-label="Sources">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted">Data sources</div>
          <ul className="mt-4 space-y-2.5 text-sm">
            <li><a className="lift text-ink/80 hover:text-ink" href="https://open-meteo.com/" target="_blank" rel="noopener noreferrer">Open-Meteo</a></li>
            <li><a className="lift text-ink/80 hover:text-ink" href="https://atmosphere.copernicus.eu/" target="_blank" rel="noopener noreferrer">CAMS / Copernicus</a></li>
            <li><a className="lift text-ink/80 hover:text-ink" href="https://eonet.gsfc.nasa.gov/" target="_blank" rel="noopener noreferrer">NASA EONET</a></li>
            <li><a className="lift text-ink/80 hover:text-ink" href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a></li>
          </ul>
        </nav>
      </div>
      <div className="border-t border-line/60">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-6 py-6 font-mono text-[11px] text-muted md:px-10">
          <span>© {new Date().getFullYear()} Aegis Air — research prototype, not medical advice</span>
          <span className="readout">v0.2 · local-first · zero telemetry</span>
        </div>
      </div>
    </footer>
  );
}
