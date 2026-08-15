/* SHINOBI//82 KAGE — dossier interactions.
   Vanilla, scoped, no dependencies. Every value rendered here comes from the
   Rev A target tables; spine values between stations are linear interpolation. */
(function () {
  "use strict";
  document.documentElement.classList.remove("no-js");

  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- chapter index (mobile disclosure) ---------- */
  var toggle = document.getElementById("nav-toggle");
  var index = document.getElementById("chapter-index");
  if (toggle && index) {
    var closeIndex = function () {
      index.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    };
    toggle.addEventListener("click", function () {
      var open = index.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && index.classList.contains("is-open")) {
        closeIndex();
        toggle.focus();
      }
    });
    document.addEventListener("click", function (e) {
      if (index.classList.contains("is-open") &&
          !index.contains(e.target) && e.target !== toggle && !toggle.contains(e.target)) {
        closeIndex();
      }
    });
    index.addEventListener("click", function (e) {
      if (e.target.closest("a")) closeIndex();
    });
  }

  /* ---------- scrollspy ---------- */
  var navLinks = {};
  document.querySelectorAll(".topbar__index a").forEach(function (a) {
    navLinks[a.getAttribute("href").slice(1)] = a;
  });
  if ("IntersectionObserver" in window) {
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var link = navLinks[entry.target.id];
        if (!link) return;
        if (entry.isIntersecting) {
          Object.keys(navLinks).forEach(function (k) { navLinks[k].removeAttribute("aria-current"); });
          link.setAttribute("aria-current", "true");
        }
      });
    }, { rootMargin: "-35% 0px -55% 0px" });
    Object.keys(navLinks).forEach(function (id) {
      var el = document.getElementById(id);
      if (el) spy.observe(el);
    });
  }

  /* ---------- reveal on view (disabled under reduced motion by CSS) ---------- */
  if ("IntersectionObserver" in window && !reducedMotion) {
    var reveal = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-inview");
          reveal.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });
    document.querySelectorAll(".reveal, .chapter").forEach(function (el) { reveal.observe(el); });
  } else {
    document.querySelectorAll(".reveal, .chapter").forEach(function (el) { el.classList.add("is-inview"); });
  }

  /* ---------- the section room ---------- */
  var slider = document.getElementById("station");
  if (slider) {
    // Rev A target stations: [mm from heel, spine mm]
    var SPINE = [[0, 1.55], [41, 1.15], [75, 0.60], [82, 0.60]];
    var ZONES = [
      {
        max: 21, name: "Heel zone · 0–21 mm", short: "heel zone",
        angles: "15° omote / 17° ura — reinforced",
        omote: 15, ura: 17, be: "0.16 mm",
        job: "Tendons, joint separation, cartilage, and dead-accurate joinery marking."
      },
      {
        max: 70, name: "Belly zone · 21–70 mm", short: "belly zone",
        angles: "12° omote / 14° ura — main edge",
        omote: 12, ura: 14, be: "0.10–0.13 mm",
        job: "Skinning and fish work — the thinnest geometry, tuned for skin release without tearing."
      },
      {
        max: 82, name: "Kissaki zone · 70–82 mm", short: "kissaki zone",
        angles: "12° omote / 14° ura — semi-flex",
        omote: 12, ura: 14, be: "0.10–0.13 mm",
        job: "Pinbone tracing, caping, fins and dovetail layout. Tip flex target 2.5–3.5 mm at 10 N."
      }
    ];

    var spineAt = function (x) {
      for (var i = 1; i < SPINE.length; i++) {
        if (x <= SPINE[i][0]) {
          var a = SPINE[i - 1], b = SPINE[i];
          return a[1] + (b[1] - a[1]) * ((x - a[0]) / (b[0] - a[0]));
        }
      }
      return SPINE[SPINE.length - 1][1];
    };
    // Visual profile-height model only (heel 15.2 mm, continuous taper); not a readout value.
    var heightAt = function (x) {
      return Math.max(5, 15.2 - 10.2 * Math.pow(x / 82, 1.25));
    };
    var zoneAt = function (x) {
      for (var i = 0; i < ZONES.length; i++) { if (x <= ZONES[i].max) return ZONES[i]; }
      return ZONES[ZONES.length - 1];
    };

    var el = function (id) { return document.getElementById(id); };
    var planeLine = el("plane-line"), planeFlag = el("plane-flag");
    var shape = el("section-shape"), clipPath = el("section-clip-path");
    var lamLine = el("lam-line"), lamLabel = el("lam-label");
    var spineDim = el("spine-dim"), spineLabel = el("spine-label");
    var omoteLabel = el("omote-label"), uraLabel = el("ura-label");
    var roZone = el("ro-zone"), roStation = el("ro-station"), roAngles = el("ro-angles"),
        roBe = el("ro-be"), roSpine = el("ro-spine"), roJob = el("ro-job");
    var handedNote = el("handed-note");
    var zoneButtons = Array.prototype.slice.call(document.querySelectorAll(".chipbtn"));

    var handed = "right";

    var SCALE = 13;   // px per mm in the section view
    var CX = 130, Y0 = 26;

    var render = function () {
      var x = Number(slider.value);
      var zone = zoneAt(x);
      var w = spineAt(x);
      var h = heightAt(x);
      var s = handed === "right" ? 1 : -1;

      // profile plane (profile view: 6 px per mm, heel at px 30)
      var px = 30 + x * 6;
      planeLine.setAttribute("d", "M" + px + " 12 L" + px + " 138");
      planeFlag.setAttribute("x", px);
      planeFlag.textContent = x + " mm";

      // cross-section wedge
      var sw = (w * SCALE) / 2;
      var ay = Y0 + h * SCALE;
      var ax = CX - s * 6;
      var bulge = 8 + h * 1.1;
      var d =
        "M" + (CX - s * sw) + " " + Y0 +
        " L" + (CX + s * sw) + " " + Y0 +
        " Q" + (CX + s * (sw + bulge)) + " " + (Y0 + h * SCALE * 0.42) + " " + ax + " " + ay +
        " Q" + (CX - s * (sw + 1)) + " " + (Y0 + h * SCALE * 0.5) + " " + (CX - s * sw) + " " + Y0 + " Z";
      shape.setAttribute("d", d);
      clipPath.setAttribute("d", d);

      // lamination boundary (7.2 mm nominal rail height, measured from the apex)
      var yLam = ay - 7.2 * SCALE;
      var lamVisible = yLam > Y0 + 6;
      lamLine.style.display = lamVisible ? "" : "none";
      lamLabel.style.display = lamVisible ? "" : "none";
      if (lamVisible) {
        lamLine.setAttribute("y1", yLam); lamLine.setAttribute("y2", yLam);
        lamLabel.setAttribute("y", yLam - 5);
      }

      // dimensions + labels
      spineDim.setAttribute("d", "M" + (CX - sw) + " 18 L" + (CX + sw) + " 18");
      spineLabel.textContent = w.toFixed(2) + " mm spine";
      omoteLabel.textContent = "omote " + zone.omote + "°";
      uraLabel.textContent = "ura " + zone.ura + "°";
      omoteLabel.setAttribute("x", ax + s * 44);
      omoteLabel.setAttribute("y", ay - 8);
      omoteLabel.setAttribute("text-anchor", s > 0 ? "start" : "end");
      uraLabel.setAttribute("x", ax - s * 44);
      uraLabel.setAttribute("y", ay + 14);
      uraLabel.setAttribute("text-anchor", s > 0 ? "end" : "start");

      // readout
      roZone.textContent = zone.name;
      roStation.textContent = x + " mm from heel";
      roAngles.textContent = zone.angles;
      roBe.textContent = zone.be;
      roSpine.textContent = w.toFixed(2) + " mm (interpolated)";
      roJob.textContent = zone.job;
      slider.setAttribute("aria-valuetext", x + " millimetres from heel, " + zone.short);

      // zone buttons reflect the active zone
      zoneButtons.forEach(function (btn) {
        var bx = Number(btn.getAttribute("data-station"));
        btn.setAttribute("aria-pressed", String(zoneAt(bx) === zone));
      });
    };

    slider.addEventListener("input", render);
    zoneButtons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        slider.value = btn.getAttribute("data-station");
        render();
        slider.focus();
      });
    });
    document.querySelectorAll('input[name="handed"]').forEach(function (radio) {
      radio.addEventListener("change", function () {
        handed = radio.value;
        handedNote.textContent = handed === "left"
          ? "Left-hand shown. The mirror is complete — blade, ura and lamination are all reversed. A left-hand order is a mirrored blade, never a re-sharpened right-hand one."
          : "A kataba grind is handed: the left-hand version is a full mirror — blade, ura and lamination — not the same blade sharpened from the other side.";
        render();
      });
    });
    render();
  }

  /* ---------- copy the decision brief ---------- */
  var copyBtn = document.getElementById("copy-brief");
  var copyStatus = document.getElementById("copy-status");
  var briefText = document.getElementById("brief-text");
  if (copyBtn && briefText) {
    copyBtn.addEventListener("click", function () {
      var text = briefText.textContent;
      var done = function () { copyStatus.textContent = "Copied — paste it into the thread."; };
      var fail = function () {
        copyStatus.textContent = "Copy failed — the brief text is just below.";
        var details = briefText.closest("details");
        if (details) details.open = true;
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, fail);
      } else {
        fail();
      }
    });
  }
})();
