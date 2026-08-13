import { resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

/** Load ebay-sold-items config/env once. */
export async function loadEbayEnv() {
  const root = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
  await import(pathToFileURL(resolve(root, "ebay-sold-items/src/config.js")).href);
}
