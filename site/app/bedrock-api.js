/**
 * BEDROCK client API — Phase 0+1 production surface
 * Talks to the Cloudflare Worker: passkeys + Tier-1 vault sync.
 * Ciphertext only leaves the device. Passphrase never leaves the device.
 */
(function (root) {
  "use strict";

  var STORAGE_KEY = "bd_cloud";
  var DEFAULTS = {
    url: "",
    access_token: "",
    refresh_token: "",
    userId: "",
    device_id: "",
    enabled: false,
    lastSync: null,
    vaultVersion: 0,
  };

  function b64(buf) {
    var u8 = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
    var s = "";
    for (var i = 0; i < u8.length; i++) s += String.fromCharCode(u8[i]);
    return btoa(s);
  }
  function unb64(str) {
    return Uint8Array.from(atob(str), function (c) {
      return c.charCodeAt(0);
    });
  }
  function b64url(buf) {
    return b64(buf).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }
  function unb64url(s) {
    var pad = "===".slice((s.length + 3) % 4);
    return unb64((s + pad).replace(/-/g, "+").replace(/_/g, "/"));
  }

  /** Bucket ciphertext length so the server cannot infer vault richness from size. */
  var PAD_BUCKETS = [16 * 1024, 64 * 1024, 256 * 1024, 1024 * 1024, 2 * 1024 * 1024];
  function padBytes(u8) {
    var n = u8.length + 4; // length prefix
    var bucket = PAD_BUCKETS[PAD_BUCKETS.length - 1];
    for (var i = 0; i < PAD_BUCKETS.length; i++) {
      if (n <= PAD_BUCKETS[i]) {
        bucket = PAD_BUCKETS[i];
        break;
      }
    }
    if (n > bucket) throw new Error("vault_too_large");
    var out = new Uint8Array(bucket);
    out[0] = (u8.length >>> 24) & 255;
    out[1] = (u8.length >>> 16) & 255;
    out[2] = (u8.length >>> 8) & 255;
    out[3] = u8.length & 255;
    out.set(u8, 4);
    // remaining bytes already zero (padding)
    return out;
  }
  function unpadBytes(u8) {
    var len = (u8[0] << 24) | (u8[1] << 16) | (u8[2] << 8) | u8[3];
    if (len < 0 || len + 4 > u8.length) throw new Error("pad_corrupt");
    return u8.slice(4, 4 + len);
  }

  var VAULT_ITERS = 600000; // OWASP minimum for PBKDF2-SHA256

  async function deriveKey(pass, salt, iters) {
    var base = await crypto.subtle.importKey(
      "raw",
      new TextEncoder().encode(pass),
      "PBKDF2",
      false,
      ["deriveKey"]
    );
    return crypto.subtle.deriveKey(
      { name: "PBKDF2", salt: salt, iterations: iters || VAULT_ITERS, hash: "SHA-256" },
      base,
      { name: "AES-GCM", length: 256 },
      false,
      ["encrypt", "decrypt"]
    );
  }

  async function encryptPayload(pass, obj) {
    var iters = VAULT_ITERS;
    var salt = crypto.getRandomValues(new Uint8Array(16));
    var iv = crypto.getRandomValues(new Uint8Array(12));
    var key = await deriveKey(pass, salt, iters);
    var raw = new TextEncoder().encode(JSON.stringify(obj));
    var padded = padBytes(raw);
    var ct = await crypto.subtle.encrypt({ name: "AES-GCM", iv: iv }, key, padded);
    return {
      app: "BEDROCK",
      v: 2,
      alg: "AES-256-GCM",
      kdf: "PBKDF2-SHA256",
      iters: iters,
      salt: b64(salt),
      iv: b64(iv),
      ct: b64(ct),
      pad: "bucket-v1",
    };
  }

  async function decryptPayload(pass, blob) {
    var key = await deriveKey(pass, unb64(blob.salt), blob.iters || VAULT_ITERS);
    var pt = new Uint8Array(
      await crypto.subtle.decrypt({ name: "AES-GCM", iv: unb64(blob.iv) }, key, unb64(blob.ct))
    );
    var raw = blob.pad === "bucket-v1" || blob.v >= 2 ? unpadBytes(pt) : pt;
    return JSON.parse(new TextDecoder().decode(raw));
  }

  function getSession() {
    try {
      return Object.assign({}, DEFAULTS, JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"));
    } catch (e) {
      return Object.assign({}, DEFAULTS);
    }
  }
  function setSession(s) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
    } catch (e) {}
  }

  function baseUrl(s) {
    return String(s.url || "").replace(/\/$/, "");
  }

  async function api(path, opts) {
    opts = opts || {};
    var s = getSession();
    var url = baseUrl(s) + path;
    if (!baseUrl(s)) throw new Error("no_backend_url");
    var headers = Object.assign({ "content-type": "application/json" }, opts.headers || {});
    if (s.access_token && !opts.noAuth) headers.authorization = "Bearer " + s.access_token;
    var res = await fetch(url, {
      method: opts.method || "GET",
      headers: headers,
      body: opts.body != null ? JSON.stringify(opts.body) : undefined,
      credentials: "omit",
    });
    if (res.status === 401 && !opts.noRefresh && s.refresh_token) {
      var refreshed = await refresh();
      if (refreshed.ok) return api(path, Object.assign({}, opts, { noRefresh: true }));
    }
    var text = await res.text();
    var data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch (e) {
      data = { raw: text };
    }
    if (!res.ok) {
      var err = new Error((data && data.error) || "http_" + res.status);
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  function bufferToB64url(buf) {
    return b64url(buf instanceof ArrayBuffer ? new Uint8Array(buf) : buf);
  }

  function publicKeyCredentialToJSON(cred) {
    var response = cred.response;
    var out = {
      id: cred.id,
      rawId: bufferToB64url(cred.rawId),
      type: cred.type,
      clientExtensionResults: cred.getClientExtensionResults
        ? cred.getClientExtensionResults()
        : {},
      response: {},
    };
    if (response.attestationObject) {
      out.response = {
        clientDataJSON: bufferToB64url(response.clientDataJSON),
        attestationObject: bufferToB64url(response.attestationObject),
        transports:
          typeof response.getTransports === "function" ? response.getTransports() : undefined,
      };
    } else {
      out.response = {
        clientDataJSON: bufferToB64url(response.clientDataJSON),
        authenticatorData: bufferToB64url(response.authenticatorData),
        signature: bufferToB64url(response.signature),
        userHandle: response.userHandle ? bufferToB64url(response.userHandle) : undefined,
      };
    }
    return out;
  }

  function prepCreateOptions(options) {
    var o = JSON.parse(JSON.stringify(options));
    o.challenge = unb64url(options.challenge);
    if (o.user && typeof o.user.id === "string") o.user.id = unb64url(o.user.id);
    if (o.excludeCredentials) {
      o.excludeCredentials = o.excludeCredentials.map(function (c) {
        return Object.assign({}, c, { id: unb64url(c.id) });
      });
    }
    return o;
  }
  function prepRequestOptions(options) {
    var o = JSON.parse(JSON.stringify(options));
    o.challenge = unb64url(options.challenge);
    if (o.allowCredentials) {
      o.allowCredentials = o.allowCredentials.map(function (c) {
        return Object.assign({}, c, { id: unb64url(c.id) });
      });
    }
    return o;
  }

  function applySession(tokens, userId) {
    var s = getSession();
    var next = Object.assign({}, s, {
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token,
      device_id: tokens.device_id || s.device_id,
      userId: userId || s.userId,
      enabled: true,
    });
    setSession(next);
    return next;
  }

  async function register() {
    if (!window.PublicKeyCredential) throw new Error("webauthn_unsupported");
    var options = await api("/auth/register/options", { method: "POST", body: {}, noAuth: true });
    var userId = options.userId;
    var cred = await navigator.credentials.create({
      publicKey: prepCreateOptions(options),
    });
    if (!cred) throw new Error("cancelled");
    var verified = await api("/auth/register/verify", {
      method: "POST",
      noAuth: true,
      body: { userId: userId, response: publicKeyCredentialToJSON(cred) },
    });
    return applySession(verified, verified.user_id || userId);
  }

  async function login() {
    if (!window.PublicKeyCredential) throw new Error("webauthn_unsupported");
    var s = getSession();
    var body = s.userId ? { userId: s.userId } : {};
    var options = await api("/auth/login/options", { method: "POST", body: body, noAuth: true });
    var cred = await navigator.credentials.get({
      publicKey: prepRequestOptions(options),
    });
    if (!cred) throw new Error("cancelled");
    var verified = await api("/auth/login/verify", {
      method: "POST",
      noAuth: true,
      body: { response: publicKeyCredentialToJSON(cred) },
    });
    return applySession(verified, verified.user_id);
  }

  async function refresh() {
    var s = getSession();
    if (!s.refresh_token) return { ok: false };
    try {
      var data = await api("/auth/refresh", {
        method: "POST",
        noAuth: true,
        noRefresh: true,
        body: { refresh_token: s.refresh_token },
      });
      applySession(data, s.userId);
      return { ok: true };
    } catch (e) {
      if (e.message === "token_reuse" || e.status === 401) {
        var wiped = Object.assign({}, s, {
          access_token: "",
          refresh_token: "",
          enabled: false,
        });
        setSession(wiped);
      }
      return { ok: false, error: e.message };
    }
  }

  async function logout() {
    var s = getSession();
    try {
      await api("/auth/logout", {
        method: "POST",
        body: { refresh_token: s.refresh_token || undefined },
      });
    } catch (e) {}
    setSession(
      Object.assign({}, s, {
        access_token: "",
        refresh_token: "",
        enabled: false,
        device_id: "",
      })
    );
  }

  async function healthz() {
    return api("/healthz", { noAuth: true, noRefresh: true });
  }

  async function vaultLatest() {
    return api("/vault/latest");
  }

  async function vaultHistory() {
    return api("/vault/history");
  }

  async function pushVault(passphrase, stateObj) {
    if (!passphrase || passphrase.length < 8) throw new Error("passphrase_weak");
    var blob = await encryptPayload(passphrase, stateObj);
    var latest = await vaultLatest();
    var base = latest.version || 0;
    // Wire format for Worker: ciphertext + iv are the outer AES envelope of the JSON blob string
    var wireIv = crypto.getRandomValues(new Uint8Array(12));
    // Outer transport layer is just the UTF-8 JSON of the already-encrypted vault blob,
    // wrapped once more? No — doctrine: server stores client ciphertext.
    // We send the vault blob's ct/iv directly (Tier-1). Metadata (salt/iters) must travel
    // inside an opaque envelope the server cannot parse — so we encrypt the *entire blob JSON*
    // with a one-shot random key? Simpler production approach: send the whole JSON blob as
    // bytes under a random AES key is overkill. Instead pack blob JSON as the ciphertext
    // payload with a random IV (AES-GCM with a key derived from passphrase already done).
    // Server only needs opaque bytes — we send `ciphertext = UTF-8(JSON.stringify(blob))`
    // with a random IV and a hash; the "iv" field is unused for decryption of content
    // (content carries its own iv). Use a dummy random IV for the wire schema.
    var payloadBytes = new TextEncoder().encode(JSON.stringify(blob));
    var padded = padBytes(payloadBytes);
    var data = await api("/vault", {
      method: "POST",
      body: {
        expected_base_version: base,
        ciphertext: b64url(padded),
        iv: b64url(wireIv),
      },
    });
    var s = getSession();
    setSession(
      Object.assign({}, s, { lastSync: Date.now(), vaultVersion: data.version })
    );
    return data;
  }

  async function pullVault(passphrase) {
    if (!passphrase) throw new Error("passphrase_required");
    var latest = await vaultLatest();
    if (!latest || !latest.ciphertext) return { empty: true, version: 0 };
    var padded = unb64url(latest.ciphertext);
    var payloadBytes = unpadBytes(padded);
    var blob = JSON.parse(new TextDecoder().decode(payloadBytes));
    var state = await decryptPayload(passphrase, blob);
    var s = getSession();
    setSession(
      Object.assign({}, s, { lastSync: Date.now(), vaultVersion: latest.version })
    );
    return { empty: false, version: latest.version, state: state };
  }

  async function listDevices() {
    return api("/auth/devices");
  }
  async function removeDevice(id) {
    return api("/auth/devices/" + encodeURIComponent(id), { method: "DELETE" });
  }
  async function pullInbox() {
    return api("/auth/inbox");
  }

  root.BedrockAPI = {
    VAULT_ITERS: VAULT_ITERS,
    PAD_BUCKETS: PAD_BUCKETS,
    getSession: getSession,
    setSession: setSession,
    healthz: healthz,
    register: register,
    login: login,
    logout: logout,
    refresh: refresh,
    pushVault: pushVault,
    pullVault: pullVault,
    vaultLatest: vaultLatest,
    vaultHistory: vaultHistory,
    listDevices: listDevices,
    removeDevice: removeDevice,
    pullInbox: pullInbox,
    encryptPayload: encryptPayload,
    decryptPayload: decryptPayload,
    padBytes: padBytes,
    unpadBytes: unpadBytes,
  };
})(typeof window !== "undefined" ? window : globalThis);
