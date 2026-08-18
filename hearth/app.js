/* Hearth OS phone kitchen. Data stays on this device. */
(function () {
  "use strict";

  const PIN_DEFAULT = "4829";
  const CAP = 110;
  const CHICKEN_SALE_MAX = 1.29;
  const PLACEHOLDER_KG = 70;
  const STORE = "hearth-os-v1";
  const SYMPTOM = ["flu", "vomit", "headache", "cancer", "diarrhea", "nausea", "migraine", "constipat", "diagnosis", "stomach"];
  const PUBLIC_ACK = "Kitchen extras added to the list.";
  const LAW = "House law forbids that ingredient.";
  const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

  const CATALOG = [
    { key: "chicken_quarters", name: "Chicken leg quarters", store: "aldi", unit: "lb", price: 1.49, protein: 17, kcal: 190 },
    { key: "jasmine_rice", name: "Jasmine rice", store: "aldi", unit: "5 lb bag", price: 3.49, protein: 30, kcal: 7700 },
    { key: "potatoes", name: "Russet potatoes", store: "aldi", unit: "5 lb bag", price: 2.99, protein: 20, kcal: 1750 },
    { key: "eggs", name: "Large eggs", store: "aldi", unit: "dozen", price: 2.85, protein: 72, kcal: 840 },
    { key: "cabbage", name: "Green cabbage", store: "aldi", unit: "head", price: 1.49, protein: 8, kcal: 170 },
    { key: "onions", name: "Yellow onions", store: "aldi", unit: "3 lb bag", price: 1.29, protein: 6, kcal: 250 },
    { key: "carrots", name: "Carrots", store: "aldi", unit: "2 lb bag", price: 1.49, protein: 4, kcal: 320 },
    { key: "butter", name: "Store-brand butter", store: "aldi", unit: "lb", price: 3.49, protein: 0, kcal: 1628 },
    { key: "milk", name: "Whole milk", store: "aldi", unit: "gallon", price: 2.79, protein: 32, kcal: 2400 },
    { key: "beans_canned", name: "Canned beans", store: "aldi", unit: "can", price: 0.89, protein: 15, kcal: 350 },
    { key: "oats", name: "Rolled oats", store: "aldi", unit: "42 oz", price: 2.49, protein: 50, kcal: 1800 },
    { key: "yogurt", name: "Plain yogurt", store: "aldi", unit: "32 oz", price: 2.99, protein: 40, kcal: 560 },
    { key: "frozen_veg", name: "Frozen mixed vegetables", store: "aldi", unit: "12 oz", price: 1.15, protein: 6, kcal: 150 },
    { key: "oil", name: "Vegetable oil", store: "aldi", unit: "48 oz", price: 2.99, protein: 0, kcal: 3840 },
    { key: "bananas", name: "Bananas", store: "aldi", unit: "lb", price: 0.49, protein: 1, kcal: 89 },
    { key: "apples", name: "Apples", store: "aldi", unit: "lb", price: 1.29, protein: 0.5, kcal: 52 },
    { key: "broth", name: "Chicken broth", store: "aldi", unit: "32 oz", price: 1.29, protein: 5, kcal: 80 },
    { key: "ginger", name: "Fresh ginger", store: "walmart", unit: "lb", price: 3.48, protein: 2, kcal: 80 },
    { key: "quinoa", name: "Quinoa", store: "wegmans", unit: "1 lb", price: 4.99, protein: 24, kcal: 680 },
  ];

  const WEEK_QTY = {
    chicken_quarters: 12, jasmine_rice: 2, potatoes: 3, eggs: 3, cabbage: 2, onions: 1,
    carrots: 1, butter: 2, milk: 2, beans_canned: 8, oats: 1, yogurt: 2, frozen_veg: 4,
    oil: 1, bananas: 2, apples: 1, broth: 1,
  };

  const MENU = [
    [["Oatmeal and eggs", "Cook oats in milk. Cook eggs until firm."], ["Jasmine rice, beans, and cabbage", "Warm rice and beans. Steam cabbage."], ["Roast chicken, potatoes, jasmine rice", "Roast chicken. Roast potatoes. Steam rice."]],
    [["Eggs and potatoes", "Cook eggs until firm. Pan potatoes."], ["Chicken and jasmine rice", "Reheat chicken with rice."], ["Chicken, cabbage, potatoes", "Simmer chicken. Boil potatoes. Steam cabbage."]],
    [["Yogurt, oats, and banana", "Stir oats into yogurt. Slice banana."], ["Bean and potato plate", "Warm beans. Boil potatoes."], ["Chicken quarters, jasmine rice, carrots", "Roast chicken. Steam rice. Cook carrots."]],
    [["Eggs, oats, and apples", "Cook eggs until firm. Cook oats. Slice apple."], ["Rice and leftover chicken", "Reheat fully. Serve with jasmine rice."], ["Chicken, potatoes, frozen vegetables", "Roast chicken. Roast potatoes. Heat vegetables."]],
    [["Potatoes and eggs", "Pan potatoes. Cook eggs until firm."], ["Jasmine rice and beans", "Warm rice and beans with onion."], ["Chicken, cabbage, jasmine rice", "Roast chicken. Steam cabbage and rice."]],
    [["Oatmeal, milk, and banana", "Cook oats in milk. Slice banana."], ["Chicken potato bowl", "Reheat chicken. Boil potatoes."], ["Roast chicken, potatoes, carrots", "Roast chicken and potatoes. Cook carrots."]],
    [["Eggs and yogurt", "Cook eggs until firm. Plain yogurt on the side."], ["Jasmine rice, beans, cabbage", "Warm rice and beans. Steam cabbage."], ["Chicken, jasmine rice, potatoes", "Roast chicken. Steam rice. Roast potatoes."]],
  ];

  const QUIET_MAP = [
    { keys: ["stomach", "flu", "vomit", "diarrhea", "nausea"], adds: { bananas: 2, broth: 2, ginger: 0.25 } },
    { keys: ["headache", "migraine"], adds: { ginger: 0.25, apples: 2 } },
    { keys: ["constipat"], adds: { apples: 2, cabbage: 1 } },
  ];

  let db = null;
  let tab = "home";
  let room = "house";
  let listening = false;
  let rec = null;
  const keys = new Map();

  const $ = (id) => document.getElementById(id);
  const cat = (key) => CATALOG.find((c) => c.key === key);

  function todayISO() {
    const d = new Date();
    return d.toISOString().slice(0, 10);
  }
  function mondayISO(d) {
    const x = d ? new Date(d) : new Date();
    const day = (x.getDay() + 6) % 7;
    x.setDate(x.getDate() - day);
    return x.toISOString().slice(0, 10);
  }
  function hasSymptom(text) {
    const t = (text || "").toLowerCase();
    return SYMPTOM.some((w) => t.includes(w));
  }
  function isBanned(text) {
    const t = text || "";
    return /kerrygold|\bketo\b|organ\s*meat|\boffal\b|sweetbread|\btripe\b|gizzard|\bliver\b|\bkidney\b|beef\s+heart|chicken\s+heart|heart\s+meat/i.test(t);
  }
  function inferQuiet(text) {
    const blob = (text || "").toLowerCase();
    const found = {};
    QUIET_MAP.forEach((row) => {
      if (row.keys.some((k) => blob.includes(k))) {
        Object.keys(row.adds).forEach((k) => {
          found[k] = (found[k] || 0) + row.adds[k];
        });
      }
    });
    return found;
  }
  function escapeHtml(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function defaultState() {
    return {
      pin: PIN_DEFAULT,
      people: [
        { id: 1, alias: "Oak", energyFirst: false, softFood: false, weightKg: null },
        { id: 2, alias: "Maple", energyFirst: false, softFood: false, weightKg: null },
        { id: 3, alias: "Birch", energyFirst: false, softFood: false, weightKg: null },
      ],
      ads: {
        chicken_quarters: { store: "tops", price: 0.99, saleEnds: "2026-08-22" },
      },
      quiet: {},
      items: [],
      meals: [],
      weekStart: mondayISO(),
      house: [],
      private: { 1: [], 2: [], 3: [] },
      receipts: [],
      currentPersonId: 1,
      speak: true,
    };
  }

  function load() {
    try {
      const raw = localStorage.getItem(STORE);
      db = raw ? Object.assign(defaultState(), JSON.parse(raw)) : defaultState();
    } catch {
      db = defaultState();
    }
    if (!db.items.length) buildWeek();
  }
  function save() {
    localStorage.setItem(STORE, JSON.stringify(db));
  }

  function resolveItem(item) {
    const ad = db.ads[item.key];
    let store = item.store;
    let price = item.price;
    let note = "";
    let saleEnds = null;
    if (ad) {
      store = ad.store;
      price = ad.price;
      saleEnds = ad.saleEnds || null;
    }
    if (item.key === "chicken_quarters") {
      const live = !saleEnds || saleEnds >= todayISO();
      if (live && price <= CHICKEN_SALE_MAX) {
        store = "tops";
        note = "";
      } else if (!live) {
        store = item.store;
        note = "not live";
      } else {
        store = item.store;
      }
    }
    return { ...item, store, price, note };
  }

  function cookExtra() {
    const parts = [];
    if (db.people.some((p) => p.energyFirst)) parts.push("Cook eggs and meat until fully done.");
    if (db.people.some((p) => p.softFood)) parts.push("Mash or simmer until soft. Shred meat.");
    return parts.join(" ");
  }

  function buildWeek() {
    const extra = cookExtra();
    db.weekStart = mondayISO();
    db.meals = [];
    MENU.forEach((slots, dayIndex) => {
      ["breakfast", "lunch", "dinner"].forEach((slot, i) => {
        db.meals.push({
          dayIndex,
          dayName: DAYS[dayIndex],
          slot,
          title: slots[i][0],
          notes: (slots[i][1] + (extra ? " " + extra : "")).trim(),
        });
      });
    });
    const qty = Object.assign({}, WEEK_QTY);
    Object.keys(db.quiet).forEach((k) => {
      qty[k] = (qty[k] || 0) + db.quiet[k];
    });
    const checked = {};
    (db.items || []).forEach((it) => {
      if (it.checked) checked[it.key] = true;
    });
    db.items = Object.keys(qty).map((key) => {
      const base = cat(key);
      const r = resolveItem(base);
      return {
        key,
        name: r.name,
        qty: qty[key],
        unit: r.unit,
        store: r.store,
        price: r.price,
        note: r.note || "",
        protein: r.protein,
        checked: !!checked[key],
      };
    });
    save();
  }

  function person() {
    return db.people.find((p) => p.id === db.currentPersonId) || db.people[0];
  }
  function needOf(p) {
    const known = p.weightKg != null && p.weightKg !== "";
    const w = known ? Number(p.weightKg) : PLACEHOLDER_KG;
    let protein = 0;
    let kcal = 0;
    if (p.energyFirst) {
      protein = Math.max(protein, 1.2 * w);
      kcal = Math.max(kcal, 25 * w);
    }
    const bits = ["estimate"];
    if (!known) bits.push("weight unknown");
    return { protein: Math.round(protein * 10) / 10, kcal: Math.round(kcal * 10) / 10, known, w, label: bits.join(", "), energyFirst: p.energyFirst };
  }
  function tonight() {
    const dinners = db.meals.filter((m) => m.slot === "dinner");
    const start = new Date(db.weekStart + "T12:00:00");
    const offset = Math.floor((Date.now() - start.getTime()) / 86400000);
    const upcoming = dinners.filter((m) => m.dayIndex >= Math.max(0, offset));
    return upcoming[0] || dinners[0];
  }
  function cartTotal() {
    return db.items.reduce((s, i) => s + i.qty * i.price, 0);
  }
  function proteinEst() {
    return db.items.reduce((s, i) => s + (i.protein || 0) * i.qty, 0);
  }

  function toast(msg) {
    const el = $("toast");
    el.hidden = false;
    el.textContent = msg;
    clearTimeout(toast._t);
    toast._t = setTimeout(() => {
      el.hidden = true;
    }, 2800);
  }
  function speak(text) {
    if (!db.speak) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!window.speechSynthesis) return;
    try {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.rate = 1.02;
      u.pitch = 1;
      window.speechSynthesis.speak(u);
    } catch (_) { /* iOS may block */ }
  }

  async function deriveKey(personId) {
    const cache = keys.get(personId);
    if (cache) return cache;
    const enc = new TextEncoder();
    const base = await crypto.subtle.importKey("raw", enc.encode(db.pin), "PBKDF2", false, ["deriveKey"]);
    const key = await crypto.subtle.deriveKey(
      { name: "PBKDF2", salt: enc.encode("hearth-private-" + personId), iterations: 40000, hash: "SHA-256" },
      base,
      { name: "AES-GCM", length: 256 },
      false,
      ["encrypt", "decrypt"]
    );
    keys.set(personId, key);
    return key;
  }
  async function encryptBody(personId, text) {
    const key = await deriveKey(personId);
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const buf = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, new TextEncoder().encode(text));
    const both = new Uint8Array(iv.length + buf.byteLength);
    both.set(iv);
    both.set(new Uint8Array(buf), iv.length);
    let bin = "";
    both.forEach((b) => {
      bin += String.fromCharCode(b);
    });
    return btoa(bin);
  }
  async function decryptBody(personId, token) {
    try {
      const key = await deriveKey(personId);
      const raw = Uint8Array.from(atob(token), (c) => c.charCodeAt(0));
      const iv = raw.slice(0, 12);
      const data = raw.slice(12);
      const buf = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, key, data);
      return new TextDecoder().decode(buf);
    } catch {
      return "";
    }
  }

  function agentFor(text, inPrivate) {
    const t = (text || "").toLowerCase();
    if (inPrivate && inferQuiet(t) && Object.keys(inferQuiet(t)).length) return "Care";
    if (/price|ad|tops|circular|scout/.test(t)) return "Scout";
    if (/cap|budget|dollar|receipt/.test(t)) return "Budget";
    return "Kitchen";
  }

  function handleText(text, inPrivate) {
    if (isBanned(text)) return LAW;
    const lower = (text || "").toLowerCase();
    if (inPrivate) {
      const adds = inferQuiet(text);
      const keysFound = Object.keys(adds);
      if (keysFound.length) {
        keysFound.forEach((k) => {
          db.quiet[k] = (db.quiet[k] || 0) + adds[k];
        });
        buildWeek();
        return PUBLIC_ACK;
      }
    }
    if (/build|week|plan|shop|cook/.test(lower)) {
      buildWeek();
      return "Kitchen built the week from the house engines. Scout prices are seeds until you correct them under Money.";
    }
    if (inPrivate) return "Care heard you. Say if you need the list restocked.";
    return "Kitchen is here. Say “build this week” or correct a price under Money.";
  }

  async function postMessage(text) {
    const p = person();
    const inPrivate = room === "private";
    const agent = agentFor(text, inPrivate);
    const reply = handleText(text, inPrivate);
    if (inPrivate) {
      const mine = db.private[p.id] || [];
      mine.push({ alias: p.alias, body: await encryptBody(p.id, text), agentName: null, t: Date.now() });
      mine.push({ alias: agent, body: await encryptBody(p.id, reply), agentName: agent, t: Date.now() + 1 });
      db.private[p.id] = mine;
    } else {
      db.house.push({ alias: p.alias, body: text, agentName: null, t: Date.now() });
      db.house.push({ alias: agent, body: reply, agentName: agent, t: Date.now() + 1 });
    }
    save();
    speak(reply);
    toast(reply);
    render();
  }

  function groupedShop() {
    const g = {};
    db.items.forEach((i) => {
      (g[i.store] || (g[i.store] = [])).push(i);
    });
    return g;
  }

  function renderHome() {
    const p = person();
    const n = needOf(p);
    const dinner = tonight();
    const total = cartTotal();
    const stores = [...new Set(db.items.map((i) => i.store))].join(", ");
    $("view").innerHTML = `
      <p class="eyebrow">${escapeHtml(p.alias)}</p>
      <h1>Tonight</h1>
      <div class="card">
        <p class="lede">${dinner ? escapeHtml(dinner.dayName + " dinner: " + dinner.title) : "Rebuild the week."}</p>
        <p class="muted">${dinner ? escapeHtml(dinner.notes) : ""}</p>
      </div>
      <div class="card">
        <h2>This week</h2>
        <p class="figure">$${total.toFixed(2)} <span class="muted">of $${CAP}</span></p>
        <p class="muted">Stores: ${escapeHtml(stores)}</p>
        <button type="button" class="solid" id="rebuild">Rebuild week</button>
      </div>
      <div class="card flags">
        <h2>Your plate (estimate)</h2>
        <p>${escapeHtml(n.label)}</p>
        ${n.energyFirst ? `<p>Protein floor ${n.protein} g · energy floor ${n.kcal} kcal. Estimate only.</p>` : `<p>No extra floors set. Weight ${n.known ? n.w + " kg" : "unknown, 70 kg placeholder"}.</p>`}
        <label class="check"><input type="checkbox" id="energy" ${p.energyFirst ? "checked" : ""}> Calories and protein first</label>
        <label class="check"><input type="checkbox" id="soft" ${p.softFood ? "checked" : ""}> Soft cook sheet</label>
        <label for="kg">Weight kg (optional)</label>
        <input id="kg" type="number" inputmode="decimal" step="0.1" min="1" value="${p.weightKg || ""}">
        <button type="button" class="solid" id="save-flags">Save flags</button>
      </div>
      <h2>Holding the phone</h2>
      <div class="row" id="switcher"></div>
      <p class="hint">Talk: tap Talk, then say “build this week” or, in Private, that you cannot keep dinner down. The list only shows food names.</p>
    `;
    db.people.forEach((pe) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = pe.id === p.id ? "solid" : "text-btn";
      b.textContent = pe.alias;
      if (pe.id === p.id) b.setAttribute("aria-current", "true");
      b.onclick = () => {
        db.currentPersonId = pe.id;
        save();
        render();
      };
      $("switcher").appendChild(b);
    });
    $("rebuild").onclick = () => {
      buildWeek();
      toast("Week rebuilt.");
      speak("Week rebuilt.");
      render();
    };
    $("save-flags").onclick = () => {
      p.energyFirst = $("energy").checked;
      p.softFood = $("soft").checked;
      const kg = $("kg").value.trim();
      p.weightKg = kg ? Number(kg) : null;
      buildWeek();
      toast("Flags saved.");
      render();
    };
  }

  async function renderRooms() {
    const p = person();
    let msgs = [];
    if (room === "private") {
      const rows = db.private[p.id] || [];
      for (const m of rows) {
        msgs.push({
          alias: m.agentName ? m.alias : m.alias,
          agentName: m.agentName,
          body: await decryptBody(p.id, m.body),
        });
      }
    } else {
      msgs = db.house.map((m) => ({ alias: m.alias, agentName: m.agentName, body: m.body }));
    }
    $("view").innerHTML = `
      <p class="eyebrow">Two rooms</p>
      <h1>${room === "private" ? "Private" : "House"}</h1>
      <p class="muted">${room === "private" ? "You and the named agents. Encrypted on this phone. The house cannot open this." : "Aliases only. Agents are Kitchen, Scout, Budget, Care."}</p>
      <div class="pills">
        <button type="button" data-room="house" ${room === "house" ? 'aria-current="true"' : ""}>House</button>
        <button type="button" data-room="private" ${room === "private" ? 'aria-current="true"' : ""}>Private</button>
      </div>
      <ol class="thread" id="thread"></ol>
      <form class="composer" id="send-form">
        <label for="draft">Message or talk</label>
        <textarea id="draft" rows="3" required placeholder="${room === "private" ? "Private note to Care" : "Build this week. Use Tops chicken if it is still $0.99."}"></textarea>
        <div class="row">
          <button type="button" class="text-btn" id="mic-room">Talk</button>
          <button type="submit" class="solid">Send</button>
        </div>
      </form>
    `;
    const thread = $("thread");
    msgs.forEach((m) => {
      const li = document.createElement("li");
      li.className = "bubble";
      const who = document.createElement("p");
      who.className = "eyebrow";
      who.textContent = m.agentName ? "Agent · " + m.agentName : m.alias;
      const body = document.createElement("p");
      body.textContent = m.body;
      li.appendChild(who);
      li.appendChild(body);
      thread.appendChild(li);
    });
    if (!msgs.length) {
      const li = document.createElement("li");
      li.className = "muted";
      li.textContent = "No messages yet.";
      thread.appendChild(li);
    }
    $("view").querySelectorAll("[data-room]").forEach((btn) => {
      btn.onclick = () => {
        room = btn.getAttribute("data-room");
        render();
      };
    });
    $("mic-room").onclick = () => startVoice($("draft"));
    $("send-form").onsubmit = (e) => {
      e.preventDefault();
      const text = $("draft").value.trim();
      if (!text) return;
      postMessage(text);
    };
  }

  function renderShop() {
    const groups = groupedShop();
    const total = cartTotal();
    let html = `<p class="eyebrow">Week of ${escapeHtml(db.weekStart)}</p><h1>Shop</h1>
      <p class="figure">$${total.toFixed(2)} <span class="muted">of $${CAP}</span></p>
      <p class="muted">Protein from the cart: ${proteinEst().toFixed(1)} g (estimate)</p>
      <button type="button" class="solid" id="rebuild2">Rebuild week</button>`;
    Object.keys(groups).forEach((store) => {
      const sub = groups[store].reduce((s, i) => s + i.qty * i.price, 0);
      html += `<section><h2>${escapeHtml(store)} · $${sub.toFixed(2)}</h2><ul class="shop-list">`;
      groups[store].forEach((item, idx) => {
        html += `<li><button type="button" class="check-btn ${item.checked ? "done" : ""}" data-key="${escapeHtml(item.key)}"><span class="box"></span><span><strong>${escapeHtml(item.name)}</strong><span class="muted"> ${item.qty} ${escapeHtml(item.unit)} · $${item.price.toFixed(2)}${item.note ? " · " + escapeHtml(item.note) : ""}</span></span></button></li>`;
      });
      html += "</ul></section>";
    });
    $("view").innerHTML = html;
    $("rebuild2").onclick = () => {
      buildWeek();
      toast("Week rebuilt.");
      render();
    };
    $("view").querySelectorAll("[data-key]").forEach((btn) => {
      btn.onclick = () => {
        const item = db.items.find((i) => i.key === btn.getAttribute("data-key"));
        if (item) item.checked = !item.checked;
        save();
        render();
      };
    });
  }

  function renderCook() {
    const days = {};
    db.meals.forEach((m) => {
      days[m.dayIndex] = days[m.dayIndex] || { name: m.dayName, meals: [] };
      days[m.dayIndex].meals.push(m);
    });
    let html = `<p class="eyebrow">Week of ${escapeHtml(db.weekStart)}</p><h1>Cook sheet</h1><p class="muted">Jasmine rice and potatoes. Numbers on Shop are estimates. This is not medical advice.</p>`;
    Object.keys(days).forEach((k) => {
      const day = days[k];
      html += `<section class="day"><h2>${escapeHtml(day.name)}</h2>`;
      day.meals.forEach((m) => {
        html += `<article><p class="slot">${escapeHtml(m.slot)}</p><h3>${escapeHtml(m.title)}</h3><p>${escapeHtml(m.notes)}</p></article>`;
      });
      html += "</section>";
    });
    $("view").innerHTML = html;
  }

  function renderMoney() {
    $("view").innerHTML = `
      <h1>Money</h1>
      <p class="muted">Seed prices are the floor. Correct one price. This phone does not fetch a live circular.</p>
      <div class="card">
        <h2>Correct a price</h2>
        <label for="ckey">Item</label>
        <select id="ckey">${CATALOG.map((c) => `<option value="${c.key}">${escapeHtml(c.name)}</option>`).join("")}</select>
        <label for="cstore">Store</label>
        <select id="cstore">
          <option value="tops">Tops</option><option value="aldi">Aldi</option>
          <option value="walmart">Walmart</option><option value="wegmans">Wegmans</option>
        </select>
        <label for="cprice">Price</label>
        <input id="cprice" type="number" inputmode="decimal" step="0.01" min="0">
        <label for="cends">Sale ends (optional)</label>
        <input id="cends" type="date">
        <button type="button" class="solid" id="save-ad">Save price</button>
      </div>
      <div class="card">
        <h2>Log a receipt</h2>
        <label for="rstore">Store</label><input id="rstore">
        <label for="ramount">Amount</label><input id="ramount" type="number" inputmode="decimal" step="0.01">
        <label for="rdate">Date</label><input id="rdate" type="date">
        <button type="button" class="solid" id="save-r">Save receipt</button>
      </div>
      <div class="card">
        <h2>PIN for this phone</h2>
        <label for="npin">New PIN</label>
        <input id="npin" type="password" inputmode="numeric" maxlength="12">
        <button type="button" class="solid" id="save-pin">Change PIN</button>
      </div>
      <ul id="receipts"></ul>
    `;
    $("rdate").value = todayISO();
    const ul = $("receipts");
    (db.receipts || []).slice().reverse().forEach((r) => {
      const li = document.createElement("li");
      li.textContent = `${r.date} · ${r.store} · $${Number(r.amount).toFixed(2)}`;
      ul.appendChild(li);
    });
    $("save-ad").onclick = () => {
      const key = $("ckey").value;
      db.ads[key] = { store: $("cstore").value, price: Number($("cprice").value), saleEnds: $("cends").value || null };
      buildWeek();
      toast("Price saved.");
      render();
    };
    $("save-r").onclick = () => {
      db.receipts.push({ store: $("rstore").value || "store", amount: Number($("ramount").value || 0), date: $("rdate").value || todayISO() });
      save();
      toast("Receipt saved.");
      render();
    };
    $("save-pin").onclick = () => {
      const next = $("npin").value.trim();
      if (next.length < 4) {
        toast("Use at least four digits.");
        return;
      }
      db.pin = next;
      keys.clear();
      save();
      toast("PIN changed on this phone.");
    };
  }

  function setTab(name) {
    tab = name;
    document.querySelectorAll(".tabs button").forEach((b) => {
      b.setAttribute("aria-current", b.getAttribute("data-tab") === tab ? "true" : "false");
    });
    $("who").textContent = person().alias + " · " + tab;
    const fn = { home: renderHome, rooms: renderRooms, shop: renderShop, cook: renderCook, money: renderMoney }[tab];
    return Promise.resolve(fn());
  }
  function render() {
    return setTab(tab);
  }

  function SpeechCtor() {
    return window.SpeechRecognition || window.webkitSpeechRecognition;
  }
  function startVoice(target) {
    const Ctor = SpeechCtor();
    if (!Ctor) {
      toast("Voice needs Safari or Chrome on this phone.");
      return;
    }
    if (listening && rec) {
      rec.stop();
      return;
    }
    rec = new Ctor();
    rec.lang = "en-US";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.continuous = false;
    listening = true;
    $("mic-top").classList.add("live");
    $("mic-top").textContent = "Listening";
    toast("Listening…");
    rec.onresult = (ev) => {
      const text = (ev.results[0][0].transcript || "").trim();
      if (!text) return;
      tab = "rooms";
      postMessage(text);
    };
    rec.onerror = () => {
      toast("Voice did not catch that. Type it.");
    };
    rec.onend = () => {
      listening = false;
      $("mic-top").classList.remove("live");
      $("mic-top").textContent = "Talk";
    };
    try {
      rec.start();
    } catch {
      toast("Tap Talk again.");
      listening = false;
    }
  }

  function showApp() {
    $("login").hidden = true;
    $("app").hidden = false;
    tab = "home";
    render();
  }

  function fillPeople() {
    const sel = $("person");
    sel.innerHTML = "";
    load();
    db.people.forEach((p) => {
      const o = document.createElement("option");
      o.value = String(p.id);
      o.textContent = p.alias;
      sel.appendChild(o);
    });
  }

  function boot() {
    fillPeople();
    $("open-btn").onclick = () => {
      const pin = $("pin").value.trim();
      if (pin !== db.pin) {
        $("login-error").hidden = false;
        $("login-error").textContent = "PIN did not match. Try again.";
        return;
      }
      db.currentPersonId = Number($("person").value);
      save();
      showApp();
    };
    $("pin").addEventListener("keydown", (e) => {
      if (e.key === "Enter") $("open-btn").click();
    });
    $("lock-btn").onclick = () => {
      $("app").hidden = true;
      $("login").hidden = false;
      $("pin").value = "";
    };
    $("mic-top").onclick = () => startVoice(tab === "rooms" ? $("draft") : null);
    document.querySelectorAll(".tabs button").forEach((b) => {
      b.onclick = () => {
        tab = b.getAttribute("data-tab");
        render();
      };
    });
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("sw.js").catch(() => {});
    }
  }

  boot();
})();
