/**
 * Assisted search result row (EP14 / C21).
 *
 * The subject is the origin badge. Until C21 it was one decision taken once for the whole
 * response from `aiAvailable`, which was honest only while every result came from the same
 * branch. C21 fuses a vector branch and two lexical ones and serves the lexical branch alone
 * when the embedding provider fails, so a response-wide badge would print "semantic match"
 * over results no semantic search produced — claiming a capability that did not run.
 */
import { describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';

import {
  AssistedSearchResultRow,
  originLabel,
  resultOrigin,
  searchOrigin,
} from '../assisted-search-result-row';
import type { AssistedSearchResult } from '@/types/ai-search.types';

function result(overrides: Partial<AssistedSearchResult> = {}): AssistedSearchResult {
  return {
    productId: 'prod-1',
    sku: 'SKU-001',
    name: 'Anillo de plata',
    price: 39.9,
    quantityAtPointOfSale: 3,
    hasStock: true,
    primaryPhotoUrl: null,
    collectionName: null,
    score: 0.8,
    matchReasons: ['vector'],
    materials: ['plata'],
    familyId: null,
    variantLabel: null,
    ...overrides,
  };
}

function renderRow(overrides: Partial<AssistedSearchResult> = {}) {
  render(<AssistedSearchResultRow result={result(overrides)} onSelect={vi.fn()} />);
  return screen.getByTestId('assisted-search-result');
}

describe('AssistedSearchResultRow origin badge', () => {
  it('should show the lexical origin badge when a result has no vector provenance', () => {
    const row = renderRow({ matchReasons: ['lexical'] });

    expect(within(row).getByText('Búsqueda por texto')).toBeInTheDocument();
    expect(within(row).queryByText('Coincidencia semántica')).not.toBeInTheDocument();
  });

  it('should show the assisted badge when the result came from both branches', () => {
    const row = renderRow({ matchReasons: ['vector', 'lexical'] });

    expect(within(row).getByText('Coincidencia semántica')).toBeInTheDocument();
  });

  it('should decide per result, so one list can carry both origins', () => {
    render(
      <>
        <AssistedSearchResultRow
          result={result({ productId: 'a', sku: 'SKU-A', matchReasons: ['vector'] })}
          onSelect={vi.fn()}
        />
        <AssistedSearchResultRow
          result={result({ productId: 'b', sku: 'SKU-B', matchReasons: ['lexical'] })}
          onSelect={vi.fn()}
        />
      </>,
    );

    const [first, second] = screen.getAllByTestId('assisted-search-result');
    expect(within(first).getByText('Coincidencia semántica')).toBeInTheDocument();
    expect(within(second).getByText('Búsqueda por texto')).toBeInTheDocument();
  });

  it('should fall back to a neutral label for an origin it does not know', () => {
    const row = renderRow({ matchReasons: ['business_signal'] });

    expect(within(row).getByText('Resultado')).toBeInTheDocument();
    expect(within(row).getByText('SKU-001')).toBeInTheDocument();
  });

  it('should call the degraded path a text search when no retriever reported itself', () => {
    const row = renderRow({ matchReasons: [] });

    expect(within(row).getByText('Búsqueda por texto')).toBeInTheDocument();
  });

  it('should not render the raw match reasons', () => {
    const row = renderRow({ matchReasons: ['vector', 'lexical'] });

    expect(within(row).queryByText(/vector/i)).not.toBeInTheDocument();
    expect(within(row).queryByText(/^lexical$/i)).not.toBeInTheDocument();
  });

  it('should display the materials the retriever recognised', () => {
    const row = renderRow({ materials: ['plata', 'nacar'] });

    expect(within(row).getByText('plata')).toBeInTheDocument();
    expect(within(row).getByText('nacar')).toBeInTheDocument();
  });

  it('should leave no gap when the variant label is absent', () => {
    const row = renderRow({ variantLabel: null });

    expect(within(row).queryByText(/^Talla/)).not.toBeInTheDocument();
  });

  it('should show the size when the variant label is present', () => {
    const row = renderRow({ variantLabel: '16' });

    expect(within(row).getByText('Talla 16')).toBeInTheDocument();
  });
});

describe('resultOrigin', () => {
  it('should map provenance to the origin the operator reads', () => {
    expect(resultOrigin(['vector'])).toBe('assisted');
    expect(resultOrigin(['lexical', 'vector'])).toBe('assisted');
    expect(resultOrigin(['lexical'])).toBe('lexical');
    expect(resultOrigin([])).toBe('lexical');
    expect(originLabel(resultOrigin(['whatever']))).toBe('Resultado');
  });
});

describe('searchOrigin', () => {
  const withReasons = (...reasons: string[][]) =>
    reasons.map((matchReasons) => ({ matchReasons }));

  it('should report the assisted mode when any result came from the semantic branch', () => {
    expect(searchOrigin(withReasons(['lexical'], ['vector', 'lexical']), true)).toBe('assisted');
  });

  it('should report the service text search when nothing came from the semantic branch', () => {
    expect(searchOrigin(withReasons(['lexical'], ['lexical']), true)).toBe('service-lexical');
  });

  it('should report the legacy text search when the assisted path did not serve', () => {
    expect(searchOrigin(withReasons(['vector']), false)).toBe('legacy-lexical');
    expect(searchOrigin([], false)).toBe('legacy-lexical');
  });

  it('should claim nothing about the mode when there are no results to read', () => {
    expect(searchOrigin([], true)).toBe('unknown');
  });
});

/**
 * C40 · the stock label with and without a shop.
 *
 * `hasStock` gained a third value when the panel learnt to search every shop at once, and three
 * values do not fit two branches: falling through to "Sin existencias" would tell the operator a
 * piece has run out everywhere, which is a claim nobody made.
 */
describe('AssistedSearchResultRow stock label', () => {
  function renderWithShop(
    shop: string | null | undefined,
    overrides: Partial<AssistedSearchResult> = {},
  ) {
    render(
      <AssistedSearchResultRow
        result={result(overrides)}
        onSelect={vi.fn()}
        onOpenCard={vi.fn()}
        pointOfSaleName={shop}
      />,
    );
    return screen.getByTestId('assisted-search-result');
  }

  it('should name the shop in the stock label', () => {
    const row = renderWithShop('MAO-TALLER', { quantityAtPointOfSale: 3, hasStock: true });

    // «3 en tienda» is true of some shop and says which one only if the operator remembers what
    // they picked. With the panel able to span every shop, naming it is what makes the figure
    // readable at all.
    expect(within(row).getByTestId('stock-label')).toHaveTextContent('3 en MAO-TALLER');
  });

  it('should not show a zero when no shop is selected', () => {
    const row = renderWithShop(null, { quantityAtPointOfSale: null, hasStock: null });

    expect(within(row).getByTestId('stock-needs-a-shop')).toHaveTextContent(
      /selecciona una tienda/i,
    );
    expect(within(row).queryByText('0')).not.toBeInTheDocument();
    expect(within(row).queryByText(/sin existencias/i)).not.toBeInTheDocument();
  });

  it('should still say a piece has run out when the shop is known and carries none', () => {
    // The third state must not swallow the second: "we carry it, we are out of it" is an answer
    // that can still save a sale.
    const row = renderWithShop('MAO-TALLER', { quantityAtPointOfSale: 0, hasStock: false });

    expect(within(row).getByText(/sin existencias/i)).toBeInTheDocument();
  });

  it('should disable the sale card action when no shop is selected', () => {
    // The card reports one shop's stock and offers substitutes from its assortment. With no shop
    // it has nothing to answer, so the action is disabled rather than opened onto a degraded card.
    const row = renderWithShop(null, { quantityAtPointOfSale: null, hasStock: null });

    expect(within(row).getByTestId('assisted-search-open-card')).toBeDisabled();
  });

  it('should enable the sale card action when a shop is selected', () => {
    const row = renderWithShop('MAO-TALLER');

    expect(within(row).getByTestId('assisted-search-open-card')).toBeEnabled();
  });
});

/**
 * C40 · the row states what its family carries.
 *
 * The composition is tested in `lib/family-note.test.ts`, where the SKU fallback and the
 * single-member case belong. What these add is that the row *says* it, and — the part a reader
 * would not guess from the markup — that it says it **without offering to sell any of them**.
 */
describe('AssistedSearchResultRow family note', () => {
  function renderWithNote(note: string | null) {
    render(
      <AssistedSearchResultRow
        result={result()}
        onSelect={vi.fn()}
        onOpenCard={vi.fn()}
        pointOfSaleName="MAO-TALLER"
        familyNote={note}
      />,
    );
    return screen.getByTestId('assisted-search-result');
  }

  it('should state what else the family carries', () => {
    const row = renderWithNote('Aro Menorca también en: 20 mm, 22 mm');

    expect(within(row).getByTestId('family-note')).toHaveTextContent(
      'Aro Menorca también en: 20 mm, 22 mm',
    );
  });

  it('should name a member by its SKU when the variant label is missing', () => {
    const row = renderWithNote('Aro Menorca también en: JBG-0009');

    expect(within(row).getByTestId('family-note')).toHaveTextContent('JBG-0009');
  });

  it('should state nothing for a single-member group', () => {
    // Not an empty element: a row padded with a blank line reads as a rendering fault, and on a
    // shop floor a rendering fault reads as a system nobody should trust.
    const row = renderWithNote(null);

    expect(within(row).queryByTestId('family-note')).not.toBeInTheDocument();
  });

  it('should not offer a sale action for any member other than the one the row is about', () => {
    // **The row announces; the sale card unfolds.** An action per sibling would turn a result
    // list into a variant picker and would let an operator sell a piece they never looked at.
    const row = renderWithNote('Aro Menorca también en: 20 mm, 22 mm');

    const actions = within(row).getAllByRole('button').map((button) => button.textContent);

    expect(actions).toHaveLength(2);
    expect(actions.filter((text) => text?.includes('Seleccionar para venta'))).toHaveLength(1);
    expect(within(row).getByTestId('family-note').querySelectorAll('button')).toHaveLength(0);
  });
});
