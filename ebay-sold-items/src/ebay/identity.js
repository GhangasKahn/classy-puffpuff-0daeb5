/**
 * eBay identity helpers.
 * Browse is moving usernames → immutable user IDs for some developers;
 * never assume seller.username is present.
 */
export function sellerHandle(seller) {
  if (seller == null) return "";
  if (typeof seller === "string") return seller.trim();
  return String(seller.username || seller.userId || seller.legacyUserId || "").trim();
}
