import useLiveAir from "./lib/useLiveAir";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import Readout from "./components/Readout";
import Manifesto from "./components/Manifesto";
import Artifacts from "./components/Artifacts";
import Evidence from "./components/Evidence";
import Audit from "./components/Audit";
import Close from "./components/Close";
import Footer from "./components/Footer";

/* Aegis Air — the front door.
   Persuasion arc: desire (hero) → evidence (readout, artifacts, record)
   → belief (manifesto) → objections (audit) → honesty (confession) → the ask. */
export default function App() {
  const live = useLiveAir();

  return (
    <div className="grain">
      <Navbar />
      <main>
        <Hero live={live} />
        <Readout live={live} />
        <Manifesto />
        <Artifacts live={live} />
        <Evidence />
        <Audit />
        <Close />
      </main>
      <Footer />
    </div>
  );
}
