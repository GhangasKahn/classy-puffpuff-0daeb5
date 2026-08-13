import { ebayFetch } from "../../../ebay-sold-items/src/ebay/client.js";
import { config } from "../../../ebay-sold-items/src/config.js";

let cachedTreeId = null;

/** GET /commerce/taxonomy/v1/get_default_category_tree_id?marketplace_id= */
export async function getDefaultCategoryTreeId(marketplaceId = config.marketplaceId) {
  if (cachedTreeId) return cachedTreeId;
  const { ok, status, json } = await ebayFetch(
    `/commerce/taxonomy/v1/get_default_category_tree_id`,
    { query: { marketplace_id: marketplaceId } }
  );
  if (!ok) {
    const err = new Error(
      `Taxonomy tree id failed (${status}): ${JSON.stringify(json).slice(0, 300)}`
    );
    err.payload = json;
    throw err;
  }
  cachedTreeId = String(json.categoryTreeId || json.category_tree_id);
  return cachedTreeId;
}

/**
 * Subtree under a category. Keep category_id focused (not marketplace root) — payloads are large.
 */
export async function getCategorySubtree(categoryId, treeId) {
  const tid = treeId || (await getDefaultCategoryTreeId());
  const { ok, status, json } = await ebayFetch(
    `/commerce/taxonomy/v1/category_tree/${tid}/get_category_subtree`,
    {
      query: { category_id: String(categoryId) },
      headers: { "Accept-Encoding": "gzip" },
    }
  );
  if (!ok) {
    const err = new Error(
      `getCategorySubtree failed (${status}): ${JSON.stringify(json).slice(0, 300)}`
    );
    err.status = status;
    err.payload = json;
    throw err;
  }
  return json;
}

/** Flatten leaf categories from a subtree response. */
export function collectLeaves(node, path = []) {
  const cat = node?.category || node;
  const id = cat?.categoryId || cat?.category_id;
  const name = cat?.categoryName || cat?.category_name || "";
  const here = id ? [...path, { id: String(id), name }] : path;
  const children =
    node?.childCategoryTreeNodes ||
    node?.child_category_tree_nodes ||
    node?.children ||
    [];
  if (!children.length) {
    return id ? [{ id: String(id), name, path: here }] : [];
  }
  return children.flatMap((ch) => collectLeaves(ch, here));
}
