/**
 * Hive comms — TASK CONTRACTs and replies. Not chat. Not scrape.
 */
import { nid, persist, listKind, playgroundBus } from "../playground/store.js";

export const TOS_CONSTRAINTS = [
  "no_html_scrape",
  "no_replica",
  "no_photo_copy",
  "no_invented_sold",
  "no_retail_arbitrage",
];

export function iso() {
  return new Date().toISOString();
}

export function makeContract({
  from = "brain",
  to,
  goal,
  inputs = {},
  tools = [],
  constraints = {},
  doneWhen,
  onFailure = "HOLD",
} = {}) {
  if (!to) throw Object.assign(new Error("TASK CONTRACT requires to"), { status: 400 });
  const id = nid("tc");
  return {
    id,
    kind: "TASK_CONTRACT",
    from,
    to,
    goal: goal || `Execute ${to} under MEUFT`,
    inputs,
    tools,
    constraints: {
      tos: TOS_CONSTRAINTS,
      capital: "HOLD_DEFAULT",
      ...constraints,
    },
    doneWhen: doneWhen || `IDENTITY output JSON from ${to}`,
    onFailure,
    meuft: { M: true, E: false, U: false, F: false, T: true },
    createdAt: iso(),
  };
}

export function postMessage({ from, to, type = "reply", contractId = null, payload = {} } = {}) {
  const at = iso();
  const msg = {
    id: nid("msg"),
    type,
    from: from || "hive",
    to: to || "brain",
    contractId,
    payload,
    at,
    createdAt: at,
    updatedAt: at,
  };
  persist("msg", msg);
  playgroundBus.emit("hive", msg);
  return msg;
}

export function postContract(contract) {
  return postMessage({
    from: contract.from,
    to: contract.to,
    type: "contract",
    contractId: contract.id,
    payload: contract,
  });
}

export function postReply({ from, to = "brain", contractId, payload }) {
  return postMessage({ from, to, type: "reply", contractId, payload });
}

export function listComms(limit = 80) {
  return listKind("msg", limit);
}

export function threadFor(contractId, limit = 40) {
  if (!contractId) return [];
  return listComms(200)
    .filter((m) => m.contractId === contractId)
    .slice(0, limit);
}
