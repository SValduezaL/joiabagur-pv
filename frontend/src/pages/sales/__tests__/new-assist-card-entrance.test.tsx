/**
 * Manual Sales Page — the sale card entrance (EP15 / C36)
 *
 * A file of its own for the same reason `new-attribution.test.tsx` is one: `new.test.tsx` fails
 * wholesale in the baseline because it renders the page without a cart context, and building on
 * top of it would make these assertions unverifiable.
 *
 * Two things are held here. That the page offers the card for the product it has selected,
 * carrying its own point of sale so the card does not have to ask for one again. And that the
 * page accepts a product identifier different from the one it already had — which is what the
 * return leg from the card depends on, since the card's whole purpose is to hand back a
 * *different* member of the family than the one that was scanned.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';

import { ManualSalesPage } from '../new';
import * as productService from '@/services/product.service';
import * as posService from '@/services/point-of-sale.service';
import * as paymentService from '@/services/payment-method.service';
import * as inventoryService from '@/services/inventory.service';

vi.mock('@/services/sales.service');
vi.mock('@/services/product.service');
vi.mock('@/services/point-of-sale.service');
vi.mock('@/services/payment-method.service');
vi.mock('@/services/inventory.service');

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
}));

vi.mock('@/providers/auth-provider', () => ({
  useAuth: () => ({
    user: { userId: 'user-1', username: 'testuser', role: 'Operator' },
    isAuthenticated: true,
    isLoading: false,
  }),
}));

vi.mock('@/providers/cart-provider', () => ({
  useCart: () => ({ addLine: vi.fn().mockReturnValue(true), lineCount: 0 }),
}));

const navigate = vi.fn();
let locationState: Record<string, unknown> | null = null;
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigate,
    useLocation: () => ({ state: locationState, pathname: '/sales/new' }),
  };
});

const ANCHOR = {
  id: 'prod-16',
  sku: 'SKU-016',
  name: 'Anillo de plata talla 16',
  price: 39.9,
  isActive: true,
} as never;

const CHOSEN_MEMBER = {
  id: 'prod-18',
  sku: 'SKU-018',
  name: 'Anillo de plata talla 18',
  price: 41.5,
  isActive: true,
} as never;

function renderPage() {
  return render(
    <BrowserRouter>
      <ManualSalesPage />
    </BrowserRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  locationState = { productId: 'prod-16' };

  vi.mocked(posService.pointOfSaleService.getPointsOfSale).mockResolvedValue([
    { id: 'pos-1', name: 'Ciutadella Centre', code: 'POS1', allowManualPriceEdit: false },
  ] as never);
  vi.mocked(paymentService.paymentMethodService.getPointOfSalePaymentMethods).mockResolvedValue(
    [] as never,
  );
  vi.mocked(paymentService.paymentMethodService.getPaymentMethods).mockResolvedValue([
    { id: 'pm-1', name: 'Efectivo', isActive: true },
  ] as never);
  vi.mocked(inventoryService.inventoryService.getProductStockBreakdown).mockResolvedValue({
    breakdown: [{ pointOfSaleId: 'pos-1', quantity: 5 }],
  } as never);
  vi.mocked(productService.productService.getProduct).mockResolvedValue(ANCHOR);
  vi.mocked(productService.productService.searchProducts).mockResolvedValue([] as never);
});

describe('ManualSalesPage — the sale card entrance', () => {
  it('should offer the sale card for the selected product', async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Anillo de plata talla 16');

    await user.click(screen.getByTestId('sales-new-open-card'));

    // The point of sale of this form travels with it, so the card does not have to ask again.
    expect(navigate).toHaveBeenCalledWith('/sales/new/assist/prod-16', {
      state: { pointOfSaleId: 'pos-1' },
    });
  });

  it('should offer no card action before a product is selected', async () => {
    locationState = null;
    renderPage();

    await waitFor(() =>
      expect(posService.pointOfSaleService.getPointsOfSale).toHaveBeenCalled(),
    );

    // There is no piece to show a card for yet.
    expect(screen.queryByTestId('sales-new-open-card')).not.toBeInTheDocument();
  });

  it('should accept a product identifier different from the one it already had', async () => {
    const { unmount } = renderPage();
    await screen.findByText('Anillo de plata talla 16');
    unmount();

    // The return leg from the card: the operator chose a different member of the family, and
    // this page must preselect *that* one rather than the piece that was scanned.
    vi.mocked(productService.productService.getProduct).mockResolvedValue(CHOSEN_MEMBER);
    locationState = { productId: 'prod-18' };
    renderPage();

    expect(await screen.findByText('Anillo de plata talla 18')).toBeInTheDocument();
    expect(screen.queryByText('Anillo de plata talla 16')).not.toBeInTheDocument();
    expect(productService.productService.getProduct).toHaveBeenLastCalledWith('prod-18');
  });
});
