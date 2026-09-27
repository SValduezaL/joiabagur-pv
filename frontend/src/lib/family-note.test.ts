/**
 * What else a result's family carries (C40).
 *
 * The assisted route groups by family, which keeps one ring in three sizes from filling the list
 * — and drops the fact that the other two sizes exist. These tests pin the three ways of getting
 * that sentence wrong: naming a member that has no label, padding a group of one, and rearranging
 * the order retrieval produced.
 */

import { describe, expect, it } from 'vitest';

import { familyNote, familySiblings, memberName } from './family-note';
import type { AssistedSearchResult, FreeQueryGroup } from '@/types/ai-search.types';

function member(overrides: Partial<AssistedSearchResult> = {}): AssistedSearchResult {
  return {
    productId: 'prod-1',
    sku: 'JBG-0001',
    name: 'Aro Menorca',
    price: 39.9,
    quantityAtPointOfSale: 3,
    hasStock: true,
    primaryPhotoUrl: null,
    collectionName: null,
    score: 0.8,
    matchReasons: ['vector'],
    materials: ['plata'],
    familyId: 'fam-1',
    variantLabel: '18 mm',
    ...overrides,
  };
}

function group(overrides: Partial<FreeQueryGroup> = {}): FreeQueryGroup {
  return {
    familyId: 'fam-1',
    familyLabel: 'Aro Menorca',
    members: [
      member({ productId: 'prod-1', sku: 'JBG-0001', variantLabel: '18 mm' }),
      member({ productId: 'prod-2', sku: 'JBG-0002', variantLabel: '20 mm' }),
    ],
    ...overrides,
  };
}

describe('familyNote', () => {
  it('should state what else the family carries', () => {
    expect(familyNote(group(), 'prod-1')).toBe('Aro Menorca también en: 20 mm');
  });

  it('should name a member by its SKU when the variant label is missing', () => {
    // A real share of the catalogue carries no variant label. «también en: ,» would be worse than
    // silence, and the SKU is what an operator can read off the label in the drawer.
    const withoutLabel = group({
      members: [
        member({ productId: 'prod-1', variantLabel: '18 mm' }),
        member({ productId: 'prod-2', sku: 'JBG-0009', variantLabel: null }),
      ],
    });

    expect(familyNote(withoutLabel, 'prod-1')).toBe('Aro Menorca también en: JBG-0009');
  });

  it('should treat a blank variant label as absent', () => {
    const blank = group({
      members: [
        member({ productId: 'prod-1' }),
        member({ productId: 'prod-2', sku: 'JBG-0007', variantLabel: '   ' }),
      ],
    });

    expect(familyNote(blank, 'prod-1')).toContain('JBG-0007');
  });

  it('should state nothing for a single-member group', () => {
    // Null and not an empty string: the caller renders no element at all, so the row is not
    // padded with a blank line that reads as a rendering fault.
    expect(familyNote(group({ members: [member()] }), 'prod-1')).toBeNull();
  });

  it('should state nothing when the row is about the only other member', () => {
    expect(familySiblings(group({ members: [member()] }), 'prod-1')).toEqual([]);
  });

  it('should work without a family label rather than printing a null', () => {
    // ~58 % of the catalogue has no family, and a group of several members with no label is
    // reachable. The sentence has to hold without it.
    const unlabelled = group({ familyLabel: null });

    expect(familyNote(unlabelled, 'prod-1')).toBe('También disponible en: 20 mm');
  });

  it('should keep the order the service ranked the members in', () => {
    const three = group({
      members: [
        member({ productId: 'prod-1', variantLabel: 'A' }),
        member({ productId: 'prod-2', variantLabel: 'C' }),
        member({ productId: 'prod-3', variantLabel: 'B' }),
      ],
    });

    // C before B, because that is what retrieval said. Sorting here would make the rank measure
    // this function instead of the retrieval quality it exists to measure.
    expect(familyNote(three, 'prod-1')).toBe('Aro Menorca también en: C, B');
  });

  it('should name every sibling and never only the first', () => {
    const three = group({
      members: [
        member({ productId: 'prod-1', variantLabel: '18 mm' }),
        member({ productId: 'prod-2', variantLabel: '20 mm' }),
        member({ productId: 'prod-3', variantLabel: '22 mm' }),
      ],
    });

    expect(familyNote(three, 'prod-1')).toBe('Aro Menorca también en: 20 mm, 22 mm');
  });
});

describe('memberName', () => {
  it('should prefer the variant label', () => {
    expect(memberName({ variantLabel: '18 mm', sku: 'JBG-0001' })).toBe('18 mm');
  });

  it('should fall back to the SKU', () => {
    expect(memberName({ variantLabel: null, sku: 'JBG-0001' })).toBe('JBG-0001');
  });
});
