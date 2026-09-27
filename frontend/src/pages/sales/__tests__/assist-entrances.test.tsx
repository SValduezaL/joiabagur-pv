/**
 * The three entrances to the sale card (EP15 / C36)
 *
 * The card is reached from the assisted search results, from the manual sale page and from a
 * scanned code. That is not a convenience: the situation the card is named after — the customer
 * with the piece in their hand, asking — arrives through the last two, and a card confined to
 * the search row would leave the knowledge corpus with no route to the counter at all.
 *
 * What is held here is the destination and what travels with it, plus the one guarantee that is
 * easy to break silently: opening a card from the panel reports **no selection**.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';

import { AssistedSalesSearchPage } from '../assisted';
import { ScanningPage } from '../scan';
import { aiSearchService } from '@/services/ai-search.service';
import * as pointOfSaleService from '@/services/point-of-sale.service';
import { productService } from '@/services/product.service';
import type { AssistedSearchResponse, AssistedSearchResult } from '@/types/ai-search.types';

vi.mock('@/services/ai-search.service', () => ({
  aiSearchService: { search: vi.fn(), getAvailability: vi.fn(), reportSelection: vi.fn() },
}));

vi.mock('@/services/point-of-sale.service', () => ({
  getPointsOfSale: vi.fn(),
}));

vi.mock('@/services/product.service', () => ({
  productService: { searchProducts: vi.fn(), getProduct: vi.fn() },
}));

vi.mock('@/services/barcode-scanning.service', () => ({
  BarcodeScanningService: class {
    startCamera = vi.fn().mockRejectedValue(new Error('no camera in jsdom'));
    stopCamera = vi.fn();
    continuousScan = vi.fn();
    stopContinuousScan = vi.fn();
    toggleFlash = vi.fn().mockResolvedValue(false);
  },
}));

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
}));

const navigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigate };
});

vi.mock('@/providers/auth-provider', () => ({
  useAuth: () => ({ user: { userId: 'u-1', role: 'Operator' } }),
}));

const POS_ONE = { id: 'pos-1', name: 'Ciutadella Centre', isActive: true } as never;

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

function response(overrides: Partial<AssistedSearchResponse> = {}): AssistedSearchResponse {
  return {
    results: [result()],
    searchEventId: 'event-1',
    aiAvailable: true,
    lowConfidence: false,
    pointOfSaleId: 'pos-1',
    candidatesReturned: 12,
    survivedHydration: 1,
    ...overrides,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE]);
  // The panel reads the switches before any search. Without this the effect rejects and the
  // page never settles, which looks like a routing failure and is not one.
  vi.mocked(aiSearchService.getAvailability).mockResolvedValue({
    kind: 'ok',
    availability: {
      pointOfSaleId: 'pos-1',
      semanticSearchAvailable: true,
      assistedAnswerAvailable: true,
      assistedAnswerUnavailableReason: null,
    },
  });
  vi.mocked(aiSearchService.reportSelection).mockResolvedValue(undefined);
  vi.mocked(aiSearchService.search).mockResolvedValue({ kind: 'ok', response: response() });
});

async function searchAndGetRow() {
  const user = userEvent.setup();
  render(
    <BrowserRouter>
      <AssistedSalesSearchPage />
    </BrowserRouter>,
  );
  await waitFor(() => expect(pointOfSaleService.getPointsOfSale).toHaveBeenCalled());
  await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
  await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
  await screen.findByTestId('assisted-search-result');
  return user;
}

describe('the card is reached from the assisted search results', () => {
  it('should reach the card from the result row scoped to the panel point of sale', async () => {
    const user = await searchAndGetRow();

    await user.click(screen.getByTestId('assisted-search-open-card'));

    expect(navigate).toHaveBeenCalledWith('/sales/new/assist/prod-1', {
      state: { pointOfSaleId: 'pos-1' },
    });
  });

  it('should report no selection when the card is opened from a result row', async () => {
    const user = await searchAndGetRow();

    await user.click(screen.getByTestId('assisted-search-open-card'));

    // Opening a card is not choosing the piece to sell, and counting it as one would inflate
    // the selection rate the search event exists to measure.
    expect(aiSearchService.reportSelection).not.toHaveBeenCalled();
  });

  it('should cost no search when the card is opened from a result row', async () => {
    const user = await searchAndGetRow();
    const searchesBefore = vi.mocked(aiSearchService.search).mock.calls.length;

    await user.click(screen.getByTestId('assisted-search-open-card'));

    expect(aiSearchService.search).toHaveBeenCalledTimes(searchesBefore);
    // The displayed results are unchanged.
    expect(screen.getByTestId('assisted-search-result')).toBeInTheDocument();
  });

  it('should keep selecting for sale behaving exactly as it did', async () => {
    const user = await searchAndGetRow();

    await user.click(screen.getByRole('button', { name: 'Seleccionar para venta' }));

    // Reported and handed to the till with its attribution, as before C36.
    expect(aiSearchService.reportSelection).toHaveBeenCalledWith('event-1', 'prod-1');
    expect(navigate).toHaveBeenCalledWith('/sales/new', {
      state: { productId: 'prod-1', searchEventId: 'event-1' },
    });
  });
});

describe('the card is reached from a scanned piece', () => {
  it('should reach the card for the resolved product', async () => {
    const user = userEvent.setup();
    vi.mocked(productService.searchProducts).mockResolvedValue([
      { id: 'prod-9', sku: 'SKU-009', name: 'Pulsera de plata' },
    ] as never);

    render(
      <BrowserRouter>
        <ScanningPage />
      </BrowserRouter>,
    );

    // The camera is unavailable in jsdom, so the manual SKU path is the one exercised — which
    // is also the one a counter uses when a code will not read.
    const field = await screen.findByPlaceholderText('Ingresa SKU manualmente...');
    await user.type(field, 'SKU-009');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    await user.click(await screen.findByTestId('scan-open-card'));

    // No point of sale travels: this page has never had one, so the card offers its
    // role-resolved selector instead.
    expect(navigate).toHaveBeenCalledWith('/sales/new/assist/prod-9');
  });

  it('should still carry on to the till exactly as it did before', async () => {
    const user = userEvent.setup();
    vi.mocked(productService.searchProducts).mockResolvedValue([
      { id: 'prod-9', sku: 'SKU-009', name: 'Pulsera de plata' },
    ] as never);

    render(
      <BrowserRouter>
        <ScanningPage />
      </BrowserRouter>,
    );

    const field = await screen.findByPlaceholderText('Ingresa SKU manualmente...');
    await user.type(field, 'SKU-009');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    await user.click(await screen.findByRole('button', { name: 'Continuar con la venta' }));

    // The destination and the state are the ones this page used before it offered the card.
    expect(navigate).toHaveBeenCalledWith('/sales/new', { state: { productId: 'prod-9' } });
  });
});
