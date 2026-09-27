/**
 * What else a result's family carries (C40).
 *
 * **The grouping that spared the list from being flooded is invisible to the operator.** The
 * assisted route deduplicates by family — a group takes the position of its best member — so a
 * ring that exists in three sizes occupies one row instead of three. That is the right shape for
 * a list, and it silently drops the fact that the other two sizes exist, which is exactly the
 * fact an operator at the counter needs when the customer's finger is a size bigger.
 *
 * A pure function and not markup, for the same reason `free-query-states.ts` is one: the two
 * things that can go wrong here — naming a member with no variant label, and padding a
 * single-member group with an empty sentence — are wrong in the *computation*, and a test that
 * rendered a component and looked for a string would pass the day somebody fixed the string.
 */

import type { AssistedSearchResult, FreeQueryGroup } from '@/types/ai-search.types';

/**
 * How a member of a family is named in the sentence.
 *
 * The variant label is what tells one sibling from another — «18 mm», «talla M» — and it is
 * absent on a real share of the catalogue. Falling back to the SKU is not decoration: a row that
 * said «también en: , ,» would be worse than saying nothing, and the SKU is what an operator can
 * type into the search box or read off the label in the drawer.
 */
export function memberName(member: Pick<AssistedSearchResult, 'variantLabel' | 'sku'>): string {
  const label = member.variantLabel?.trim();
  return label ? label : member.sku;
}

/**
 * The other members of this result's family, in the order the service ranked them.
 *
 * **Never re-sorted and never re-grouped.** The order is retrieval's opinion; rearranging it here
 * would make the rank measure this code instead of the retrieval quality it is there to measure.
 */
export function familySiblings(
  group: Pick<FreeQueryGroup, 'members'>,
  productId: string,
): AssistedSearchResult[] {
  return group.members.filter((member) => member.productId !== productId);
}

/**
 * The sentence, or `null` when there is nothing to say.
 *
 * `null` and not an empty string: the caller renders nothing at all for it, so a group of one
 * produces no element rather than an empty one. A row padded with a blank line reads as a
 * rendering fault, and on a shop floor a rendering fault reads as a system nobody should trust.
 */
export function familyNote(
  group: Pick<FreeQueryGroup, 'familyLabel' | 'members'>,
  productId: string,
): string | null {
  const others = familySiblings(group, productId);
  if (others.length === 0) {
    return null;
  }

  const named = others.map(memberName).filter(Boolean);
  if (named.length === 0) {
    return null;
  }

  // The family is announced by name when it has one. ~58 % of the catalogue has no family at all,
  // and a group of several members without a label is possible, so the sentence has to work
  // without it rather than printing «la familia null».
  const family = group.familyLabel?.trim();
  return family
    ? `${family} también en: ${named.join(', ')}`
    : `También disponible en: ${named.join(', ')}`;
}
