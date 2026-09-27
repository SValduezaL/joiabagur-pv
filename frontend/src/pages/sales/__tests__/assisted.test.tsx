/**
 * Assisted Search Panel Tests (EP14 / C16)
 *
 * The panel's substance is not "does it render a list": it is that a search costs money, that
 * four different kinds of nothing must say four different things, and that the attribution has
 * to survive all the way to the till. Those are what these tests hold.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';

import { AssistedSalesSearchPage } from '../assisted';
import { aiSearchService } from '@/services/ai-search.service';
import * as pointOfSaleService from '@/services/point-of-sale.service';
import type {
  AiSearchAvailability,
  AssistedSearchOutcome,
  FreeQuerySearchResponse,
  AssistedSearchResponse,
  AssistedSearchResult,
} from '@/types/ai-search.types';
import type { PointOfSale } from '@/types/point-of-sale.types';

vi.mock('@/services/ai-search.service', () => ({
  aiSearchService: {
    search: vi.fn(),
    searchAssisted: vi.fn(),
    getAvailability: vi.fn(),
    reportSelection: vi.fn(),
  },
}));

vi.mock('@/services/point-of-sale.service', () => ({
  getPointsOfSale: vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
}));

const navigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigate };
});

let role = 'Operator';
vi.mock('@/providers/auth-provider', () => ({
  useAuth: () => ({ user: { userId: 'u-1', role } }),
}));

// **Typed, not `as never`.** The cast these carried silenced the mock's signature and took the
// fixtures' own shape down with it: reading `POS_TWO.id` off a `never` is an error `vitest` never
// sees and `npm run build` transpiles straight past. Filling the required fields costs four keys
// and makes both the mock and the reads check.
function pointOfSale(
  overrides: Partial<PointOfSale> & Pick<PointOfSale, 'id' | 'name'>,
): PointOfSale {
  return {
    code: overrides.id.toUpperCase(),
    isActive: true,
    allowManualPriceEdit: false,
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

const POS_ONE = pointOfSale({ id: 'pos-1', name: 'Ciutadella Centre' });
const POS_TWO = pointOfSale({ id: 'pos-2', name: 'Fornells' });
const POS_INACTIVE = pointOfSale({ id: 'pos-3', name: 'Cerrada', isActive: false });

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

function answers(payload: AssistedSearchResponse) {
  vi.mocked(aiSearchService.search).mockResolvedValue({ kind: 'ok', response: payload });
}

function answersWith(outcome: AssistedSearchOutcome) {
  vi.mocked(aiSearchService.search).mockResolvedValue(outcome);
}

function renderPanel() {
  return render(
    <BrowserRouter>
      <AssistedSalesSearchPage />
    </BrowserRouter>,
  );
}

async function ready() {
  await waitFor(() => expect(pointOfSaleService.getPointsOfSale).toHaveBeenCalled());
}

/** Both paths on, which is the state the pre-existing tests of this file assume. */
function availabilityIs(overrides: Partial<AiSearchAvailability> = {}) {
  vi.mocked(aiSearchService.getAvailability).mockResolvedValue({
    kind: 'ok',
    availability: {
      pointOfSaleId: 'pos-1',
      semanticSearchAvailable: true,
      assistedAnswerAvailable: true,
      assistedAnswerUnavailableReason: null,
      ...overrides,
    },
  });
}

/** An assisted answer with one family of one member, hydrated. */
function assistedResponse(
  overrides: Partial<FreeQuerySearchResponse> = {},
): FreeQuerySearchResponse {
  return {
    groups: [{ familyId: 'fam-1', familyLabel: 'Aro fino', members: [result()] }],
    pitch: 'Las tres son sobrias y van bien a diario.',
    pitchStatus: 'generated',
    citations: [],
    warnings: [],
    clarificationQuestion: null,
    intent: 'in_domain',
    abstained: false,
    aiAvailable: true,
    degradedReason: null,
    usage: null,
    searchEventId: 'event-fq',
    pointOfSaleId: 'pos-1',
    candidatesReturned: 1,
    survivedHydration: 1,
    traceId: 'trace-fq',
    ...overrides,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  role = 'Operator';
  vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE]);
  vi.mocked(aiSearchService.reportSelection).mockResolvedValue(undefined);
  availabilityIs();
  answers(response());
  vi.mocked(aiSearchService.searchAssisted).mockResolvedValue({
    kind: 'ok',
    response: assistedResponse(),
  });
});

describe('AssistedSalesSearchPage — cost of a search', () => {
  it('should not issue a search request when the operator types without submitting', async () => {
    const user = userEvent.setup();
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo de plata');

    // The candidate cache is keyed on the whole query string, so no prefix can ever hit it: a
    // debounced field would charge one embedding per pause and read at most one of them.
    expect(aiSearchService.search).not.toHaveBeenCalled();
  });

  it('should issue exactly one search request when the operator submits', async () => {
    const user = userEvent.setup();
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo de plata');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    await waitFor(() => expect(aiSearchService.search).toHaveBeenCalledTimes(1));
    expect(vi.mocked(aiSearchService.search).mock.calls[0][0]).toMatchObject({
      query: 'anillo de plata',
      pointOfSaleId: 'pos-1',
    });
  });

  it('should fill the field and search when an example query is activated', async () => {
    const user = userEvent.setup();
    renderPanel();
    await ready();

    await user.click(screen.getByRole('button', { name: /un anillo de plata para regalar/ }));

    await waitFor(() => expect(aiSearchService.search).toHaveBeenCalledTimes(1));
    expect(screen.getByLabelText('¿Qué busca el cliente?')).toHaveValue(
      'un anillo de plata para regalar',
    );
  });

  it('should not issue a search request when a quick filter is toggled', async () => {
    const user = userEvent.setup();
    renderPanel();
    await ready();

    await user.click(screen.getByRole('button', { name: 'Plata' }));
    await user.click(screen.getByRole('button', { name: 'Perla' }));

    expect(aiSearchService.search).not.toHaveBeenCalled();
  });

  it('should allow selecting multiple materials in quick filters', async () => {
    const user = userEvent.setup();
    renderPanel();
    await ready();

    await user.click(screen.getByRole('button', { name: 'Plata' }));
    await user.click(screen.getByRole('button', { name: 'Perla' }));

    expect(screen.getByRole('button', { name: 'Plata' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: 'Perla' })).toHaveAttribute('aria-pressed', 'true');

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'algo bonito');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    await waitFor(() => expect(aiSearchService.search).toHaveBeenCalled());
    // Canonical terms, not the displayed labels: a label would match nothing in the index.
    expect(vi.mocked(aiSearchService.search).mock.calls[0][0].materials).toEqual([
      'plata',
      'perla',
    ]);
  });

  it('should clear every active filter when the clear action is used', async () => {
    const user = userEvent.setup();
    renderPanel();
    await ready();

    await user.click(screen.getByRole('button', { name: 'Plata' }));
    await user.click(screen.getByRole('button', { name: 'Quitar filtros' }));

    expect(screen.getByRole('button', { name: 'Plata' })).toHaveAttribute('aria-pressed', 'false');
  });
});

describe('AssistedSalesSearchPage — results', () => {
  it('should render results with reason when search succeeds', async () => {
    const user = userEvent.setup();
    answers(response({ results: [result({ materials: ['plata', 'perla'] })] }));
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    const row = await screen.findByTestId('assisted-search-result');
    expect(within(row).getByText('Anillo de plata')).toBeInTheDocument();
    expect(within(row).getByText('SKU-001')).toBeInTheDocument();
    expect(within(row).getByText('Coincidencia semántica')).toBeInTheDocument();
    expect(within(row).getByText('plata')).toBeInTheDocument();
    expect(within(row).getByText('perla')).toBeInTheDocument();
    // The raw retriever signal is never shown: it is the constant "vector" for every result.
    expect(within(row).queryByText('vector')).not.toBeInTheDocument();
  });

  it('should render results in the order received', async () => {
    const user = userEvent.setup();
    // Deliberately a set whose order by price and by name both differ from the order of arrival,
    // so that a client-side sort could not pass this test by coincidence.
    answers(
      response({
        results: [
          result({ productId: 'p-1', sku: 'SKU-C', name: 'Zafiro', price: 90 }),
          result({ productId: 'p-2', sku: 'SKU-A', name: 'Alianza', price: 10 }),
          result({ productId: 'p-3', sku: 'SKU-B', name: 'Medalla', price: 50 }),
        ],
      }),
    );
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'algo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    const rows = await screen.findAllByTestId('assisted-search-result');
    expect(rows.map((r) => within(r).getByText(/Zafiro|Alianza|Medalla/).textContent)).toEqual([
      'Zafiro',
      'Alianza',
      'Medalla',
    ]);
  });

  it('should mark a result as out of stock when it has none', async () => {
    const user = userEvent.setup();
    answers(response({ results: [result({ hasStock: false, quantityAtPointOfSale: 0 })] }));
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    const row = await screen.findByTestId('assisted-search-result');
    // Kept and marked, never hidden: "we carry it, we are out of it" can still save a sale.
    expect(within(row).getByText('Sin existencias')).toBeInTheDocument();
  });

  it('should not render a size when the variant label is absent', async () => {
    const user = userEvent.setup();
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    await screen.findByTestId('assisted-search-result');
    expect(screen.queryByText(/^Talla /)).not.toBeInTheDocument();
  });

  it('should declare a short page when fewer results survive than requested', async () => {
    const user = userEvent.setup();
    answers(response({ results: [result()], candidatesReturned: 18, survivedHydration: 1 }));
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    const note = await screen.findByTestId('assisted-search-short-page');
    expect(note).toHaveTextContent('1 resultados');
    expect(note).toHaveTextContent('18 candidatos');
  });
});

describe('AssistedSalesSearchPage — the four ways of showing nothing', () => {
  async function searchWith(payload: AssistedSearchResponse) {
    const user = userEvent.setup();
    answers(payload);
    renderPanel();
    await ready();
    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'algo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
  }

  it('should distinguish abstention from empty assortment', async () => {
    await searchWith(
      response({ results: [], lowConfidence: true, candidatesReturned: 0, survivedHydration: 0 }),
    );

    expect(await screen.findByText('No he encontrado nada que encaje')).toBeInTheDocument();
    expect(screen.queryByText('Nada de esto está en tu tienda')).not.toBeInTheDocument();
  });

  it('should say the shop carries none of it when candidates did not survive hydration', async () => {
    await searchWith(
      response({ results: [], lowConfidence: false, candidatesReturned: 24, survivedHydration: 0 }),
    );

    expect(await screen.findByText('Nada de esto está en tu tienda')).toBeInTheDocument();
    expect(screen.getByText(/24 piezas parecidas/)).toBeInTheDocument();
  });

  it('should say the semantic branch did not run when only lexical results came back', async () => {
    // The failure that looks healthiest of all: the AI service answered 200 with results on
    // screen, having served its lexical branch because the embedding provider failed. Without
    // this banner the panel claims a capability that did not run.
    await searchWith(
      response({
        results: [result({ matchReasons: ['lexical'] })],
        aiAvailable: true,
        candidatesReturned: 8,
        survivedHydration: 1,
      }),
    );

    expect(await screen.findByText('Coincidencia semántica no disponible')).toBeInTheDocument();
    expect(screen.queryByText('Búsqueda asistida no disponible')).not.toBeInTheDocument();

    const row = screen.getByTestId('assisted-search-result');
    expect(within(row).getByText('Búsqueda por texto')).toBeInTheDocument();
  });

  it('should not warn about the semantic branch when it did run', async () => {
    await searchWith(response({ results: [result({ matchReasons: ['vector', 'lexical'] })] }));

    expect(await screen.findByTestId('assisted-search-result')).toBeInTheDocument();
    expect(
      screen.queryByText('Coincidencia semántica no disponible'),
    ).not.toBeInTheDocument();
  });

  it('should show legacy results banner when ai is unavailable', async () => {
    // Match reasons are empty on the degraded path: no retriever ran, so there is no
    // provenance to report. Since C21 the row derives its badge from that, per result.
    await searchWith(
      response({
        results: [result({ matchReasons: [] })],
        aiAvailable: false,
        candidatesReturned: 0,
        survivedHydration: 1,
      }),
    );

    expect(await screen.findByText('Búsqueda asistida no disponible')).toBeInTheDocument();
    expect(
      screen.getByText('Estos resultados vienen de la búsqueda por texto.'),
    ).toBeInTheDocument();

    // The row states the same origin, so the operator can tell a degraded result from an
    // assisted one without scrolling back to the banner.
    const row = screen.getByTestId('assisted-search-result');
    expect(within(row).getByText('Búsqueda por texto')).toBeInTheDocument();
  });

  it('should show a rate limit message when the server answers 429', async () => {
    const user = userEvent.setup();
    answersWith({ kind: 'rate-limited' });
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'algo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    expect(await screen.findByText('Demasiadas búsquedas seguidas')).toBeInTheDocument();
    // A quota is the system protecting itself, not an outage. Saying the opposite would send the
    // operator looking for a fault that does not exist.
    expect(screen.queryByText('Búsqueda asistida no disponible')).not.toBeInTheDocument();
  });

  it('should report a forbidden point of sale as an access problem', async () => {
    const user = userEvent.setup();
    answersWith({ kind: 'forbidden' });
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'algo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    expect(await screen.findByText('No tienes acceso a esta tienda')).toBeInTheDocument();
  });
});

describe('AssistedSalesSearchPage — episode, selection and attribution', () => {
  it('should keep the search session id across reformulations in one panel visit', async () => {
    const user = userEvent.setup();
    renderPanel();
    await ready();

    const field = screen.getByLabelText('¿Qué busca el cliente?');
    const button = screen.getByRole('button', { name: /^Buscar$/ });

    await user.type(field, 'anillo');
    await user.click(button);
    await waitFor(() => expect(aiSearchService.search).toHaveBeenCalledTimes(1));

    await user.clear(field);
    await user.type(field, 'anillo de plata');
    await user.click(button);
    await waitFor(() => expect(aiSearchService.search).toHaveBeenCalledTimes(2));

    const calls = vi.mocked(aiSearchService.search).mock.calls;
    expect(calls[0][0].searchSessionId).toBeTruthy();
    // One episode per visit: without this, every rephrasing counts as an abandoned query.
    expect(calls[1][0].searchSessionId).toBe(calls[0][0].searchSessionId);
  });

  it('should keep the search session id when the point of sale changes', async () => {
    const user = userEvent.setup();
    vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE, POS_TWO]);
    renderPanel();
    await ready();

    const field = screen.getByLabelText('¿Qué busca el cliente?');
    await user.type(field, 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
    await waitFor(() => expect(aiSearchService.search).toHaveBeenCalledTimes(1));

    await user.click(screen.getByLabelText('Punto de venta'));
    await user.click(await screen.findByRole('option', { name: 'Fornells' }));

    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
    await waitFor(() => expect(aiSearchService.search).toHaveBeenCalledTimes(2));

    const calls = vi.mocked(aiSearchService.search).mock.calls;
    // Changing shop is still the same visit. Resetting the episode here — a plausible place to
    // put the reset — would turn every shop switch into a false abandoned query.
    expect(calls[1][0].searchSessionId).toBe(calls[0][0].searchSessionId);
    expect(calls[1][0].pointOfSaleId).not.toBe(calls[0][0].pointOfSaleId);
  });

  it('should start a new search session id when the panel is opened again', async () => {
    const user = userEvent.setup();
    const first = renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
    await waitFor(() => expect(aiSearchService.search).toHaveBeenCalledTimes(1));

    first.unmount();

    renderPanel();
    await waitFor(() => expect(pointOfSaleService.getPointsOfSale).toHaveBeenCalledTimes(2));

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'pendientes');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
    await waitFor(() => expect(aiSearchService.search).toHaveBeenCalledTimes(2));

    const calls = vi.mocked(aiSearchService.search).mock.calls;
    // A new visit is a new episode: there is nothing to group between two visits that each
    // ended in a selection.
    expect(calls[1][0].searchSessionId).not.toBe(calls[0][0].searchSessionId);
  });

  it('should emit search event when a result is selected', async () => {
    const user = userEvent.setup();
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
    await user.click(await screen.findByRole('button', { name: 'Seleccionar para venta' }));

    expect(aiSearchService.reportSelection).toHaveBeenCalledWith('event-1', 'prod-1');
  });

  it('should carry the search event id into the sale flow when a result is selected', async () => {
    const user = userEvent.setup();
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
    await user.click(await screen.findByRole('button', { name: 'Seleccionar para venta' }));

    expect(navigate).toHaveBeenCalledWith('/sales/new', {
      state: { productId: 'prod-1', searchEventId: 'event-1' },
    });
  });

  it('should not block navigation when reporting the selection fails', async () => {
    const user = userEvent.setup();
    vi.mocked(aiSearchService.reportSelection).mockRejectedValue(new Error('telemetry down'));
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
    await user.click(await screen.findByRole('button', { name: 'Seleccionar para venta' }));

    // The server stamps the moment, so the call leaves at the click and its outcome is nobody's
    // business but telemetry's.
    expect(navigate).toHaveBeenCalled();
  });

  it('should skip the selection report when no search event id was returned', async () => {
    const user = userEvent.setup();
    answers(response({ searchEventId: null }));
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
    await user.click(await screen.findByRole('button', { name: 'Seleccionar para venta' }));

    expect(aiSearchService.reportSelection).not.toHaveBeenCalled();
    expect(navigate).toHaveBeenCalledWith('/sales/new', {
      state: { productId: 'prod-1', searchEventId: undefined },
    });
  });

  it('should report the selection when the piece came from a free query', async () => {
    const user = userEvent.setup();
    vi.mocked(aiSearchService.searchAssisted).mockResolvedValue({
      kind: 'ok',
      response: assistedResponse(),
    });
    renderPanel();
    await ready();

    await user.click(await screen.findByTestId('route-option-assisted'));
    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'algo sobrio para diario');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
    await user.click(await screen.findByRole('button', { name: 'Seleccionar para venta' }));

    // **The generative route attributes too.** It read only the semantic state, so a piece found
    // by a free query reached the till with no event behind it: `SelectedFromRank` stayed null for
    // the whole population and the toggle lost the half of its ablation that says whether the
    // prose helped anyone buy anything.
    expect(aiSearchService.reportSelection).toHaveBeenCalledWith('event-fq', 'prod-1');
    expect(navigate).toHaveBeenCalledWith('/sales/new', {
      state: { productId: 'prod-1', searchEventId: 'event-fq' },
    });
  });
});

describe('AssistedSalesSearchPage — point of sale and role', () => {
  it('should hide the point of sale selector when the operator has a single assignment', async () => {
    renderPanel();
    await ready();

    await waitFor(() =>
      expect(screen.queryByLabelText('Punto de venta')).not.toBeInTheDocument(),
    );
  });

  it('should offer only active points of sale when several are available', async () => {
    vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([
      POS_ONE,
      POS_TWO,
      POS_INACTIVE,
    ]);
    renderPanel();
    await ready();

    const selector = await screen.findByLabelText('Punto de venta');
    expect(selector).toBeInTheDocument();
    // An inactive shop is refused by the endpoint for every role, so offering it would be
    // offering a guaranteed error.
    expect(screen.queryByText('Cerrada')).not.toBeInTheDocument();
  });

  it('should show the funnel block to an administrator', async () => {
    const user = userEvent.setup();
    role = 'Administrator';
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    const funnel = await screen.findByTestId('assisted-search-funnel');

    // Collapsed by default: the counts are not on screen until the administrator asks.
    expect(within(funnel).queryByText('Candidatos: 12')).not.toBeInTheDocument();

    await user.click(within(funnel).getByRole('button'));
    expect(within(funnel).getByText('Candidatos: 12')).toBeInTheDocument();
    expect(within(funnel).getByText('Supervivientes: 1')).toBeInTheDocument();
    expect(within(funnel).getByText('Mostrados: 1')).toBeInTheDocument();

    // The search event identifier, not a correlation identifier: the response deliberately does
    // not carry one. This is the key that joins what is on screen to the persisted telemetry row.
    expect(within(funnel).getByText('Evento: event-1')).toBeInTheDocument();
  });

  it('should clear the results when the point of sale changes', async () => {
    const user = userEvent.setup();
    vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE, POS_TWO]);
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
    await screen.findByTestId('assisted-search-result');

    await user.click(screen.getByLabelText('Punto de venta'));
    await user.click(await screen.findByRole('option', { name: 'Fornells' }));

    // Another shop is another assortment. Re-running here would charge an embedding the operator
    // never asked for, so the list is cleared and the next search is theirs to trigger.
    await waitFor(() =>
      expect(screen.queryByTestId('assisted-search-result')).not.toBeInTheDocument(),
    );
    expect(aiSearchService.search).toHaveBeenCalledTimes(1);
  });

  it('should ignore a stale response when the point of sale changed', async () => {
    const user = userEvent.setup();
    vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE, POS_TWO]);

    // The first search resolves last, which is exactly the order that would let it overwrite the
    // second one's results if the panel did not guard against it.
    let releaseFirst: (value: AssistedSearchOutcome) => void = () => {};
    vi.mocked(aiSearchService.search)
      .mockImplementationOnce(
        () => new Promise<AssistedSearchOutcome>((resolve) => (releaseFirst = resolve)),
      )
      .mockResolvedValueOnce({
        kind: 'ok',
        response: response({
          results: [result({ productId: 'p-fornells', name: 'Collar de Fornells' })],
        }),
      });

    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    await user.click(screen.getByLabelText('Punto de venta'));
    await user.click(await screen.findByRole('option', { name: 'Fornells' }));

    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
    expect(await screen.findByText('Collar de Fornells')).toBeInTheDocument();

    releaseFirst({
      kind: 'ok',
      response: response({ results: [result({ productId: 'p-stale', name: 'Resultado viejo' })] }),
    });

    await waitFor(() => expect(screen.queryByText('Resultado viejo')).not.toBeInTheDocument());
    expect(screen.getByText('Collar de Fornells')).toBeInTheDocument();
  });

  it('should hide the funnel block from an operator', async () => {
    const user = userEvent.setup();
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    await screen.findByTestId('assisted-search-result');
    expect(screen.queryByTestId('assisted-search-funnel')).not.toBeInTheDocument();
  });
});

/**
 * Availability, stated before a search (C40).
 *
 * The defect these hold is the one that opened the change: for the whole project the panel served
 * from its degraded route and looked exactly as it does when the AI answers. `aiAvailable` only
 * arrives inside a response, so the operator could not learn that a path was off without first
 * using it.
 */
describe('AssistedSalesSearchPage — availability before searching', () => {
  it('should state availability of both paths before any search', async () => {
    renderPanel();
    await ready();

    const badge = await screen.findByTestId('ai-availability');

    expect(badge).toHaveTextContent(/Búsqueda inteligente y respuesta asistida disponibles/);
    // The whole point: this is known without having searched, and without spending a call.
    expect(aiSearchService.search).not.toHaveBeenCalled();
    expect(aiSearchService.getAvailability).toHaveBeenCalledWith('pos-1');
  });

  it('should state the assisted option as unavailable with its reason when the assisted path is off', async () => {
    availabilityIs({
      assistedAnswerAvailable: false,
      assistedAnswerUnavailableReason: 'switched_off',
    });

    renderPanel();
    await ready();

    const badge = await screen.findByTestId('ai-availability');

    expect(badge).toHaveTextContent(/desactivada en esta tienda/);
    // Not presented as a fault: a switch that is off is somebody's decision, and telling an
    // operator the system is broken would send them looking for a problem that is not there.
    expect(badge).not.toHaveTextContent(/error|caíd|fallo/i);
  });

  it('should tell the semantic path apart from the assisted one when only one is off', async () => {
    availabilityIs({ semanticSearchAvailable: false, assistedAnswerAvailable: true });

    renderPanel();
    await ready();

    const badge = await screen.findByTestId('ai-availability');

    // The odd quadrant, and reachable: two independent switches. Collapsing them into one "AI"
    // flag would render this state wrongly.
    expect(badge).toHaveTextContent(/Búsqueda por texto/);
    expect(badge).toHaveTextContent(/Respuesta asistida disponible/);
  });

  it('should say it could not tell when availability cannot be read', async () => {
    vi.mocked(aiSearchService.getAvailability).mockResolvedValue({ kind: 'unknown' });

    renderPanel();
    await ready();

    const badge = await screen.findByTestId('ai-availability');

    // Failing to read the switches is not an outage. The panel still searches, so the badge
    // admits ignorance instead of alarming about something the operator cannot act on.
    expect(badge).toHaveTextContent(/No he podido comprobar la disponibilidad/);
  });

  it('should re-read availability when the point of sale changes', async () => {
    vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE, POS_TWO]);
    const user = userEvent.setup();
    renderPanel();
    await ready();

    await waitFor(() => expect(aiSearchService.getAvailability).toHaveBeenCalledWith('pos-1'));

    await user.click(screen.getByLabelText('Punto de venta'));
    await user.click(await screen.findByRole('option', { name: 'Fornells' }));

    // The switches are per shop, so the answer has to be re-read. And it stays free: changing
    // shop must not cost a model call.
    await waitFor(() => expect(aiSearchService.getAvailability).toHaveBeenCalledWith('pos-2'));
    expect(aiSearchService.search).not.toHaveBeenCalled();
  });
});

/**
 * The route toggle (C40).
 *
 * Two ways to answer the same query. What these hold is the cost discipline the panel has had
 * since C16, applied to a route that costs four times the time budget and three times the quota.
 */
describe('AssistedSalesSearchPage — the route toggle', () => {
  it('should default to the fast route', async () => {
    const user = userEvent.setup();
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    // The cheap one, on every visit. The expensive face is not what an operator lands on.
    await waitFor(() => expect(aiSearchService.search).toHaveBeenCalled());
    expect(aiSearchService.searchAssisted).not.toHaveBeenCalled();
  });

  it('should state the cost difference before any search', async () => {
    renderPanel();
    await ready();

    const toggle = await screen.findByTestId('search-route-toggle');

    // Stated before pressing, not after: an operator who discovers the difference by waiting
    // seven seconds has already paid it.
    expect(toggle).toHaveTextContent(/30 búsquedas por minuto/);
    expect(toggle).toHaveTextContent(/10 búsquedas por minuto/);
    expect(toggle).toHaveTextContent(/puede tardar unos segundos/i);
    expect(aiSearchService.search).not.toHaveBeenCalled();
  });

  it('should issue no request when the route changes', async () => {
    const user = userEvent.setup();
    renderPanel();
    await ready();

    await user.click(await screen.findByTestId('route-option-assisted'));

    // Changing route picks what the NEXT search will do. The panel's first rule is that a
    // search happens only when the operator asks for one.
    expect(aiSearchService.search).not.toHaveBeenCalled();
    expect(aiSearchService.searchAssisted).not.toHaveBeenCalled();
  });

  it('should issue exactly one assisted request when that route is chosen', async () => {
    const user = userEvent.setup();
    renderPanel();
    await ready();

    await user.click(await screen.findByTestId('route-option-assisted'));
    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'se puede mojar la plata');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    await waitFor(() => expect(aiSearchService.searchAssisted).toHaveBeenCalledTimes(1));
    expect(aiSearchService.search).not.toHaveBeenCalled();
  });

  it('should not remember the route between visits', async () => {
    const user = userEvent.setup();
    const first = renderPanel();
    await ready();

    await user.click(await screen.findByTestId('route-option-assisted'));
    expect(await screen.findByTestId('route-option-assisted')).toHaveAttribute('aria-checked', 'true');

    // A second visit, as an operator gets by navigating away and back.
    first.unmount();
    vi.clearAllMocks();
    vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE]);
    availabilityIs();
    answers(response());

    renderPanel();
    await ready();

    // Remembering the expensive face is how it gets spent without anybody deciding to.
    expect(await screen.findByTestId('route-option-semantic')).toHaveAttribute('aria-checked', 'true');
    expect(screen.getByTestId('route-option-assisted')).toHaveAttribute('aria-checked', 'false');
  });

  it('should disable the assisted option with its reason when the assisted path is off', async () => {
    availabilityIs({
      assistedAnswerAvailable: false,
      assistedAnswerUnavailableReason: 'switched_off',
    });

    renderPanel();
    await ready();

    const option = await screen.findByTestId('route-option-assisted');

    // Disabled with its reason rather than failing when pressed: an option that throws on click
    // is the same lie this change exists to remove, moved one step later.
    expect(option).toBeDisabled();
    expect(screen.getByTestId('route-unavailable-assisted')).toHaveTextContent(
      /desactivada en esta tienda/,
    );
  });

  it('should render the assisted answer with its argument and its groups', async () => {
    const user = userEvent.setup();
    vi.mocked(aiSearchService.searchAssisted).mockResolvedValue({
      kind: 'ok',
      response: assistedResponse(),
    });

    renderPanel();
    await ready();

    await user.click(await screen.findByTestId('route-option-assisted'));
    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'algo de plata');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    expect(await screen.findByTestId('assisted-pitch')).toHaveTextContent(
      /sobrias y van bien a diario/,
    );
    expect(await screen.findByTestId('assisted-search-result')).toBeInTheDocument();
  });

  it('should not render a piece warning above the result list', async () => {
    const user = userEvent.setup();
    vi.mocked(aiSearchService.searchAssisted).mockResolvedValue({
      kind: 'ok',
      response: assistedResponse({
        warnings: ['family_has_variants', 'size_label_missing', 'knowledge_not_covered'],
      }),
    });

    renderPanel();
    await ready();

    await user.click(await screen.findByTestId('route-option-assisted'));
    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'algo de plata');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    const banner = await screen.findByTestId('assisted-query-warnings');

    // A warning about a piece describes the first member of the first group, so above a list it
    // would state something false about every other result.
    expect(banner).toHaveTextContent(/La documentación no cubre esta pregunta/);
    expect(banner).not.toHaveTextContent(/otras variantes/);
    expect(banner).not.toHaveTextContent(/Sin talla declarada/);
  });
});

/**
 * The sixteen states on screen (C40).
 *
 * The classification itself is held in `free-query-states.test.ts`; what these add is that the
 * screen says the right thing for each, and — for three of them — that it does **not** say the
 * thing it would say by default.
 */
describe('AssistedSalesSearchPage — the sixteen states', () => {
  async function assistedSearch(user: ReturnType<typeof userEvent.setup>) {
    await user.click(await screen.findByTestId('route-option-assisted'));
    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'una consulta');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
  }

  function assistedAnswers(overrides: Partial<FreeQuerySearchResponse>) {
    vi.mocked(aiSearchService.searchAssisted).mockResolvedValue({
      kind: 'ok',
      response: assistedResponse(overrides),
    });
  }

  const citation = {
    citationId: 'plata#cuidados',
    documentTitle: 'Plata',
    sectionTitle: 'Cuidados',
    docType: 'material',
    claimScope: 'general',
    snippet: 'Evitar el agua.',
    score: 0.7,
  } as never;

  it('should word an out-of-domain refusal differently from a not-in-catalogue one', async () => {
    const user = userEvent.setup();
    assistedAnswers({
      groups: [],
      pitch: null,
      intent: 'out_of_domain',
      warnings: ['query_out_of_domain'],
    });
    renderPanel();
    await ready();
    await assistedSearch(user);

    const outOfDomain = (await screen.findByTestId('assisted-refusal')).textContent;

    expect(outOfDomain).toMatch(/no es una pregunta de joyería/i);
    expect(outOfDomain).not.toMatch(/no trabajamos ese tipo/i);
  });

  it('should invite rephrasing when the classifier could not route', async () => {
    const user = userEvent.setup();
    assistedAnswers({ groups: [], pitch: null, intent: 'in_domain' });
    renderPanel();
    await ready();
    await assistedSearch(user);

    const block = await screen.findByTestId('assisted-no-route');

    expect(block).toHaveAttribute('data-intent', 'in_domain');
    expect(screen.getByTestId('assisted-rephrase-invitation')).toBeInTheDocument();
  });

  it('should not invite rephrasing when the classifier did not run', async () => {
    const user = userEvent.setup();
    assistedAnswers({ groups: [], pitch: null, intent: 'unclassified' });
    renderPanel();
    await ready();
    await assistedSearch(user);

    const block = await screen.findByTestId('assisted-no-route');

    // The classifier never ran — no credential, a timeout, an unparseable reply. Asking the
    // operator to rephrase would blame them for a configuration, and with the router credential
    // missing EVERY query lands here.
    expect(block).toHaveAttribute('data-intent', 'unclassified');
    expect(screen.queryByTestId('assisted-rephrase-invitation')).not.toBeInTheDocument();
  });

  it('should not announce an empty result set on the knowledge route', async () => {
    const user = userEvent.setup();
    assistedAnswers({
      groups: [],
      citations: [citation],
      pitch: 'La plata se empaña con el aire y se limpia con un paño suave.',
    });
    renderPanel();
    await ready();
    await assistedSearch(user);

    await screen.findByTestId('assisted-pitch');

    // Zero pieces and a correct answer. The five branches of emptiness of the C16 panel would
    // write «Sin resultados» directly above it.
    expect(screen.queryByTestId('assisted-empty')).not.toBeInTheDocument();
    expect(screen.queryByText(/sin resultados/i)).not.toBeInTheDocument();
  });

  it('should render the clarification question and return focus to the query box', async () => {
    const user = userEvent.setup();
    assistedAnswers({
      groups: [],
      pitch: null,
      clarificationQuestion: '¿Es para regalo o para ti?',
    });
    renderPanel();
    await ready();
    await assistedSearch(user);

    // Verbatim: the catalogue of questions is closed and written in code on the service side,
    // precisely so no model composes a sentence an operator reads out loud.
    expect(await screen.findByTestId('assisted-clarification')).toHaveTextContent(
      '¿Es para regalo o para ti?',
    );

    // Focus goes back to the box, which is the action the question is asking for.
    await waitFor(() => expect(screen.getByLabelText('¿Qué busca el cliente?')).toHaveFocus());
  });

  it('should render no citation when there is no argument', async () => {
    const user = userEvent.setup();
    assistedAnswers({ pitch: null, pitchStatus: 'withheld_by_ai', citations: [citation] });
    renderPanel();
    await ready();
    await assistedSearch(user);

    await screen.findByTestId('assisted-without-prose');

    // The service keeps them on purpose — a degraded response must not be poorer than the
    // structured layer produces on its own, which keeps the ablation comparable for the
    // harness. For an operator a citation with no claim attached attributes nothing.
    expect(screen.queryByTestId('assist-citation')).not.toBeInTheDocument();
  });

  it('should state a withdrawn citation without alarming', async () => {
    const user = userEvent.setup();
    assistedAnswers({
      groups: [],
      citations: [],
      pitch: 'La plata tolera bien el agua del grifo.',
    });
    renderPanel();
    await ready();
    await assistedSearch(user);

    const line = await screen.findByTestId('assisted-no-verifiable-source');

    // A discreet line, not an alert: it fires on roughly a quarter of knowledge answers, and at
    // that frequency an alert trains an operator to ignore it.
    expect(line).toHaveTextContent(/sin fuente verificable/i);
    expect(line.tagName.toLowerCase()).toBe('p');
  });

  it('should not describe a withdrawn citation as invented', async () => {
    const user = userEvent.setup();
    assistedAnswers({ groups: [], citations: [], pitch: 'La plata tolera bien el agua.' });
    renderPanel();
    await ready();
    await assistedSearch(user);

    const line = await screen.findByTestId('assisted-no-verifiable-source');

    // The citation existed; what could not be verified is the span that supported it.
    expect(line.textContent).not.toMatch(/invent|falso/i);
  });

  it('should state that the assisted answer may take seconds while in flight', async () => {
    const user = userEvent.setup();
    let settle: (value: never) => void = () => {};
    vi.mocked(aiSearchService.searchAssisted).mockReturnValue(
      new Promise((resolve) => {
        settle = resolve as never;
      }),
    );

    renderPanel();
    await ready();
    await assistedSearch(user);

    // From the first instant, never a blank pane: the budget is ten seconds, and seven of
    // undifferentiated waiting with a customer at the counter is where this gets abandoned.
    expect(await screen.findByTestId('assisted-loading')).toHaveTextContent(
      /puede tardar unos segundos/i,
    );

    settle({ kind: 'ok', response: assistedResponse() } as never);
  });

  it('should tell a narrow filter from an unanswerable query', async () => {
    const user = userEvent.setup();
    assistedAnswers({ warnings: ['filters_too_narrow'] });
    renderPanel();
    await ready();
    await assistedSearch(user);

    const narrow = await screen.findByTestId('assisted-filters-too-narrow');

    // The two end in different actions: remove a filter, or describe it another way.
    expect(narrow).toHaveTextContent(/ninguna pasa los filtros/i);
    expect(narrow).toHaveTextContent(/quitar alguno de los filtros/i);
    expect(screen.queryByTestId('assisted-abstained')).not.toBeInTheDocument();
  });
});

/**
 * C40 · changing shop is a cheap act, and it has to stay cheap.
 *
 * The panel reads availability on every shop change, which is what lets it say a path is off
 * *before* the operator uses it. That read must not be mistaken for a search: it calls no model,
 * spends no quota and, above all, must not re-run the last query against the new shop.
 */
describe('AssistedSalesSearchPage — changing the shop', () => {
  it('should issue no assisted request when the shop changes', async () => {
    const user = userEvent.setup();
    vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE, POS_TWO]);
    renderPanel();
    await ready();

    await user.click(await screen.findByTestId('route-option-assisted'));
    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo de plata');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
    await waitFor(() => expect(aiSearchService.searchAssisted).toHaveBeenCalledTimes(1));

    await user.click(screen.getByLabelText('Punto de venta'));
    await user.click(await screen.findByRole('option', { name: 'Fornells' }));

    // Availability is read again — that is the point of reading it per shop — and nothing else.
    await waitFor(() =>
      expect(aiSearchService.getAvailability).toHaveBeenCalledWith(POS_TWO.id),
    );
    expect(aiSearchService.searchAssisted).toHaveBeenCalledTimes(1);
    expect(aiSearchService.search).not.toHaveBeenCalled();
  });

  it('should keep reading availability without spending the assisted quota', async () => {
    const user = userEvent.setup();
    vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE, POS_TWO]);
    renderPanel();
    await ready();

    await user.click(screen.getByLabelText('Punto de venta'));
    await user.click(await screen.findByRole('option', { name: 'Fornells' }));
    await user.click(screen.getByLabelText('Punto de venta'));
    await user.click(await screen.findByRole('option', { name: POS_ONE.name }));

    expect(aiSearchService.searchAssisted).not.toHaveBeenCalled();
    expect(aiSearchService.search).not.toHaveBeenCalled();
  });
});

/**
 * The every-point-of-sale scope (C40_FIX)
 *
 * C40 built this scope in full and left no way into it, so none of it ever ran. The reason none of
 * its 136 scenarios caught that is the reason these tests are here and at page level: the row's own
 * tests pass the no-shop state **straight to the component**, so they exercised the state without
 * ever exercising the path to it. Auditing the state is not auditing the way in.
 */
describe('AssistedSalesSearchPage — the every-point-of-sale scope', () => {
  /** Administrator with two shops, which is when the selector is shown and the option is offered. */
  function asAdministrator() {
    role = 'Administrator';
    vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE, POS_TWO]);
  }

  async function chooseEveryShop(user: ReturnType<typeof userEvent.setup>) {
    await user.click(screen.getByLabelText('Punto de venta'));
    await user.click(await screen.findByRole('option', { name: 'Todas las tiendas' }));
  }

  /** The no-shop answer: grouped by product, with no quantity and no stock flag. */
  function assistedResponseWithoutShop() {
    vi.mocked(aiSearchService.searchAssisted).mockResolvedValue({
      kind: 'ok',
      response: assistedResponse({
        pointOfSaleId: null,
        groups: [
          {
            familyId: null,
            familyLabel: null,
            members: [result({ quantityAtPointOfSale: null, hasStock: null })],
          },
        ],
      }),
    });
  }

  it('should offer the every-shop scope when the caller is an administrator', async () => {
    const user = userEvent.setup();
    asAdministrator();
    renderPanel();
    await ready();

    await user.click(screen.getByLabelText('Punto de venta'));

    expect(await screen.findByRole('option', { name: 'Todas las tiendas' })).toBeInTheDocument();
  });

  it('should not offer the every-shop scope when the caller is an operator', async () => {
    const user = userEvent.setup();
    // Two shops, so the selector is shown and its absence cannot be blamed on the selector itself.
    vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE, POS_TWO]);
    renderPanel();
    await ready();

    await user.click(screen.getByLabelText('Punto de venta'));
    expect(await screen.findByRole('option', { name: 'Fornells' })).toBeInTheDocument();

    // The narrowing belongs to the screen, not to authorisation: the route keeps serving this scope
    // to operators. What the panel declines to offer is a tool that answers the wrong question at a
    // counter, since it reports no stock at all and so cannot close a sale.
    expect(screen.queryByRole('option', { name: 'Todas las tiendas' })).not.toBeInTheDocument();
  });

  it('should select a concrete shop on load rather than the every-shop scope', async () => {
    asAdministrator();
    renderPanel();
    await ready();

    await waitFor(() =>
      expect(screen.getByLabelText('Punto de venta')).toHaveTextContent(POS_ONE.name),
    );
    expect(screen.queryByTestId('assisted-scope-consequence')).not.toBeInTheDocument();
  });

  it('should issue no search request when the scope changes to every shop', async () => {
    const user = userEvent.setup();
    asAdministrator();
    renderPanel();
    await ready();

    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));
    await screen.findByTestId('assisted-search-result');

    await chooseEveryShop(user);

    // Picking a scope is not asking for a search, and the displayed results stop describing the
    // scope that is now selected, so they go.
    await waitFor(() =>
      expect(screen.queryByTestId('assisted-search-result')).not.toBeInTheDocument(),
    );
    expect(aiSearchService.search).toHaveBeenCalledTimes(1);
    expect(aiSearchService.searchAssisted).not.toHaveBeenCalled();
  });

  it('should state the consequence of the scope before any search is issued', async () => {
    const user = userEvent.setup();
    asAdministrator();
    renderPanel();
    await ready();

    await chooseEveryShop(user);

    const stated = await screen.findByTestId('assisted-scope-consequence');
    expect(stated).toHaveTextContent(/todo el catálogo/i);
    expect(stated).toHaveTextContent(/elige una tienda/i);
    expect(aiSearchService.search).not.toHaveBeenCalled();
    expect(aiSearchService.searchAssisted).not.toHaveBeenCalled();
  });

  it('should disable the fast route with a reason of scope when every shop is selected', async () => {
    const user = userEvent.setup();
    asAdministrator();
    renderPanel();
    await ready();

    await chooseEveryShop(user);

    const reason = await screen.findByTestId('route-unavailable-semantic');
    expect(reason).toHaveTextContent(/una tienda concreta/i);
  });

  it('should not state the semantic path as switched off when the fast route is disabled by scope', async () => {
    const user = userEvent.setup();
    asAdministrator();
    renderPanel();
    await ready();

    await chooseEveryShop(user);

    // Two different facts. The fast route does not accept this scope; its switch is untouched.
    // Reporting the first as the second is the class of false statement this panel exists to stop
    // making, and it is the one C40 was opened to remove.
    const reason = await screen.findByTestId('route-unavailable-semantic');
    expect(reason).not.toHaveTextContent(/desactivad/i);
  });

  it('should keep the assisted route enabled when every shop is selected', async () => {
    const user = userEvent.setup();
    asAdministrator();
    renderPanel();
    await ready();

    await chooseEveryShop(user);

    // **The test that closes this change.** Before it, selecting the scope left the availability
    // read unresolved, so the assisted option came out disabled with no reason to show: a path that
    // switches itself off and does not say so, which is the exact shape of failure C40 existed to
    // retire.
    await waitFor(() =>
      expect(screen.queryByTestId('route-unavailable-assisted')).not.toBeInTheDocument(),
    );
    expect(screen.getByTestId('ai-availability')).not.toHaveTextContent(
      /Comprobando disponibilidad/i,
    );
  });

  it('should state that the scope needs the assisted answer when it is switched off', async () => {
    const user = userEvent.setup();
    asAdministrator();
    availabilityIs({
      pointOfSaleId: null,
      assistedAnswerAvailable: false,
      assistedAnswerUnavailableReason: 'switched_off',
    });
    renderPanel();
    await ready();

    await chooseEveryShop(user);

    // Both options of the toggle are disabled here, one by scope and one by switch. Left unsaid
    // that is a scope you can pick and cannot search from.
    const deadEnd = await screen.findByTestId('assisted-scope-dead-end');
    expect(deadEnd).toHaveTextContent(/respuesta asistida/i);
    expect(deadEnd).toHaveTextContent(/desactivada/i);
  });

  it('should not claim the assisted answer is off at this shop when every shop is selected', async () => {
    const user = userEvent.setup();
    asAdministrator();
    availabilityIs({
      pointOfSaleId: null,
      assistedAnswerAvailable: false,
      assistedAnswerUnavailableReason: 'switched_off',
    });
    renderPanel();
    await ready();

    await chooseEveryShop(user);

    // There is no shop to speak of in this scope, so naming one is not a wording preference: it is
    // a false statement.
    await waitFor(() =>
      expect(screen.getByTestId('route-unavailable-assisted')).not.toHaveTextContent(
        /en esta tienda/i,
      ),
    );
    expect(screen.getByTestId('ai-availability')).not.toHaveTextContent(/en esta tienda/i);
  });

  it('should send no point of sale when searching every shop', async () => {
    const user = userEvent.setup();
    asAdministrator();
    renderPanel();
    await ready();

    await chooseEveryShop(user);
    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo de plata');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    await waitFor(() => expect(aiSearchService.searchAssisted).toHaveBeenCalledTimes(1));

    // **Absent, not blank.** The routes tell the two apart on purpose: an absent point of sale
    // leaves the availability prefilter unapplied, while a blank identifier names no shop and is
    // refused. Reading one as the other would turn a client bug into a wider search.
    const payload = vi.mocked(aiSearchService.searchAssisted).mock.calls[0][0];
    expect(payload).not.toHaveProperty('pointOfSaleId');
    expect(JSON.stringify(payload)).not.toContain('00000000-0000-0000-0000-000000000000');

    // The fast route refuses this scope with a 400, so it must not be the one that was asked.
    expect(aiSearchService.search).not.toHaveBeenCalled();
  });

  it('should read availability without a point of sale when every shop is selected', async () => {
    const user = userEvent.setup();
    asAdministrator();
    renderPanel();
    await ready();

    await chooseEveryShop(user);

    await waitFor(() =>
      expect(aiSearchService.getAvailability).toHaveBeenLastCalledWith(undefined),
    );
  });

  it('should state that a shop is needed to read stock when every shop is selected', async () => {
    const user = userEvent.setup();
    asAdministrator();
    assistedResponseWithoutShop();
    renderPanel();
    await ready();

    await chooseEveryShop(user);
    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo de plata');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    const row = await screen.findByTestId('assisted-search-result');
    // Not a zero, which would be a false statement about a piece that may be in the next shop along.
    expect(row).toHaveTextContent(/selecciona una tienda/i);
    expect(row).not.toHaveTextContent(POS_ONE.name);
  });

  it('should disable the sale card action when every shop is selected', async () => {
    const user = userEvent.setup();
    asAdministrator();
    assistedResponseWithoutShop();
    renderPanel();
    await ready();

    await chooseEveryShop(user);
    await user.type(screen.getByLabelText('¿Qué busca el cliente?'), 'anillo de plata');
    await user.click(screen.getByRole('button', { name: /^Buscar$/ }));

    const row = await screen.findByTestId('assisted-search-result');
    expect(within(row).getByRole('button', { name: /ficha/i })).toBeDisabled();
  });
});
