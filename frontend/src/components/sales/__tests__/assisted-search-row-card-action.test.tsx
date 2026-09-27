/**
 * The result row's secondary action (EP14 / C16 · EP15 / C36)
 *
 * A separate file from the row's own tests on purpose: those cover the origin badge, which is
 * what that component was built for, and this covers the one thing C36 adds to it. The
 * substance is that the addition is *secondary* in the strict sense — it neither replaces,
 * disables nor precedes selecting the result for sale — and that opening a card reports no
 * selection, because counting it as one would inflate the very rate the search event exists to
 * measure.
 */
import { describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { AssistedSearchResultRow } from '../assisted-search-result-row';
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

describe('AssistedSearchResultRow — the sale card action', () => {
  it('should offer both actions on a result', () => {
    render(
      <AssistedSearchResultRow result={result()} onSelect={vi.fn()} onOpenCard={vi.fn()} />,
    );
    const row = screen.getByTestId('assisted-search-result');

    expect(within(row).getByRole('button', { name: 'Seleccionar para venta' })).toBeInTheDocument();
    expect(within(row).getByRole('button', { name: /Ver ficha de venta/ })).toBeInTheDocument();
  });

  it('should neither replace nor disable the selection for sale', async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(
      <AssistedSearchResultRow result={result()} onSelect={onSelect} onOpenCard={vi.fn()} />,
    );
    const row = screen.getByTestId('assisted-search-result');
    const select = within(row).getByRole('button', { name: 'Seleccionar para venta' });

    expect(select).toBeEnabled();
    await user.click(select);

    // Exactly as it behaved before this capability gained the secondary action.
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ productId: 'prod-1' }));
  });

  it('should open the card for that product without touching the selection', async () => {
    const onSelect = vi.fn();
    const onOpenCard = vi.fn();
    const user = userEvent.setup();
    render(
      <AssistedSearchResultRow result={result()} onSelect={onSelect} onOpenCard={onOpenCard} />,
    );

    await user.click(screen.getByRole('button', { name: /Ver ficha de venta/ }));

    expect(onOpenCard).toHaveBeenCalledWith(expect.objectContaining({ productId: 'prod-1' }));
    // Opening a card is not choosing the piece to sell.
    expect(onSelect).not.toHaveBeenCalled();
  });

  it('should render no card action when no handler is given', () => {
    // Optional so every caller and every test that existed before C36 keeps working unchanged.
    render(<AssistedSearchResultRow result={result()} onSelect={vi.fn()} />);

    expect(screen.queryByTestId('assisted-search-open-card')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Seleccionar para venta' })).toBeInTheDocument();
  });
});
