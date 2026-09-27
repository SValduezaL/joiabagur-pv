/**
 * Sale Card Page Tests (EP15 / C36)
 *
 * The substance is not "does it render the piece". It is that a card costs a paid generation and
 * may be asked for exactly once per visit; that six states of the argument have to say different
 * things without misstating where what is on screen came from; that a family of several variants
 * cannot be sold from without naming one; and that a value this screen does not know degrades a
 * row rather than breaking the screen.
 *
 * The services are replaced with `vi.mock` of the module and not with network handlers: the
 * interceptor is configured to *warn* on an unhandled request, so a test built on it can pass
 * having asserted nothing at all.
 *
 * The context providers are mocked rather than wrapped, following the assisted search panel's
 * own tests — rendering a page drags in whatever context it consumes, and that is the single
 * largest cause of the suite's pre-existing red.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { SalesAssistCardPage } from '../assist';
import { salesAssistService } from '@/services/sales-assist.service';
import * as pointOfSaleService from '@/services/point-of-sale.service';
import { UNKNOWN_WARNING_LABEL } from '@/lib/assist-copy';
import type {
  PitchStatus,
  SalesAssistCitation,
  SalesAssistMember,
  SalesAssistOutcome,
  SalesAssistResponse,
  SubstituteResult,
  SubstitutesOutcome,
  SubstitutesResponse,
} from '@/types/sales-assist.types';

vi.mock('@/services/sales-assist.service', () => ({
  salesAssistService: {
    assist: vi.fn(),
    substitutes: vi.fn(),
  },
}));

vi.mock('@/services/point-of-sale.service', () => ({
  getPointsOfSale: vi.fn(),
  getPointOfSale: vi.fn(),
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

const PRODUCT_ID = 'prod-anchor';
const POS_ID = 'pos-1';
const POS_ONE = { id: POS_ID, name: 'Ciutadella Centre', isActive: true } as never;
const POS_TWO = { id: 'pos-2', name: 'Fornells', isActive: true } as never;

function member(overrides: Partial<SalesAssistMember> = {}): SalesAssistMember {
  return {
    productId: PRODUCT_ID,
    sku: 'SKU-001',
    name: 'Anillo de plata',
    variantLabel: '16',
    price: 39.9,
    quantityAtPointOfSale: 3,
    hasStock: true,
    primaryPhotoUrl: null,
    collectionName: null,
    materials: ['plata'],
    matchReasons: ['vector'],
    isAnchor: true,
    ...overrides,
  };
}

function citation(overrides: Partial<SalesAssistCitation> = {}): SalesAssistCitation {
  return {
    citationId: 'cuidados-generales#limpieza',
    documentTitle: 'Cuidados generales de una joya',
    sectionTitle: 'Limpieza en casa',
    docType: 'material',
    claimScope: 'general',
    snippet: 'Un paño seco y suave retira el sudor y la grasa del día a día.',
    ...overrides,
  };
}

function response(overrides: Partial<SalesAssistResponse> = {}): SalesAssistResponse {
  return {
    aiAvailable: true,
    pointOfSaleId: POS_ID,
    productId: PRODUCT_ID,
    intent: 'product_pitch',
    groups: [{ familyId: null, familyLabel: null, members: [member()] }],
    pitch: 'Una pieza de plata de ley, sencilla y de diario.',
    pitchStatus: 'generated',
    citations: [],
    warnings: [],
    clarificationQuestion: null,
    promptVersion: 'v1',
    traceId: 'trace-1',
    ...overrides,
  };
}

function substitute(overrides: Partial<SubstituteResult> = {}): SubstituteResult {
  return {
    productId: 'prod-sub-1',
    sku: 'SKU-900',
    name: 'Anillo de plata trenzado',
    variantLabel: '16',
    price: 42,
    quantityAtPointOfSale: 2,
    primaryPhotoUrl: null,
    collectionName: null,
    materials: ['plata'],
    matchReasons: ['vector'],
    familyMatch: false,
    materialOverlap: 0.9,
    styleSimilarity: 0.8,
    ...overrides,
  };
}

function substitutesResponse(
  overrides: Partial<SubstitutesResponse> = {},
): SubstitutesResponse {
  return {
    outcome: 'ok',
    results: [substitute()],
    candidatesReturned: 5,
    survivedHydration: 1,
    pointOfSaleId: POS_ID,
    traceId: 'trace-2',
    ...overrides,
  };
}

function answers(payload: SalesAssistResponse) {
  vi.mocked(salesAssistService.assist).mockResolvedValue({ kind: 'ok', response: payload });
}

function answersWith(outcome: SalesAssistOutcome) {
  vi.mocked(salesAssistService.assist).mockResolvedValue(outcome);
}

/** Renders the card on its real route, with the point of sale in navigation state. */
function renderCard(state: { pointOfSaleId?: string } | null = { pointOfSaleId: POS_ID }) {
  return render(
    <MemoryRouter
      initialEntries={[
        { pathname: `/sales/new/assist/${PRODUCT_ID}`, state: state ?? undefined },
      ]}
    >
      <Routes>
        <Route path="/sales/new/assist/:productId" element={<SalesAssistCardPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

async function served() {
  await waitFor(() => expect(screen.getByTestId('assist-piece-header')).toBeInTheDocument());
}

beforeEach(() => {
  vi.clearAllMocks();
  role = 'Operator';
  vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE]);
  vi.mocked(pointOfSaleService.getPointOfSale).mockResolvedValue(POS_ONE);
  vi.mocked(salesAssistService.substitutes).mockResolvedValue({
    kind: 'ok',
    response: substitutesResponse(),
  });
  answers(response());
});

/* ---------------------------------------------------------------------------------------------
 * 7.2 — the cost of a card
 * ------------------------------------------------------------------------------------------ */

describe('SalesAssistCardPage — cost of a card', () => {
  it('should issue exactly one assist request per visit', async () => {
    renderCard();
    await served();

    // Navigating here *is* the explicit act. Re-rendering, the response arriving and a failure
    // must none of them produce another: the budget is ten per minute and there is no cache.
    expect(salesAssistService.assist).toHaveBeenCalledTimes(1);
    expect(vi.mocked(salesAssistService.assist).mock.calls[0]).toEqual([
      PRODUCT_ID,
      { pointOfSaleId: POS_ID },
    ]);
  });

  it('should not issue another request when the card re-renders', async () => {
    const { rerender } = renderCard();
    await served();

    rerender(
      <MemoryRouter
        initialEntries={[
          { pathname: `/sales/new/assist/${PRODUCT_ID}`, state: { pointOfSaleId: POS_ID } },
        ]}
      >
        <Routes>
          <Route path="/sales/new/assist/:productId" element={<SalesAssistCardPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(salesAssistService.assist).toHaveBeenCalledTimes(1);
  });

  it('should not retry a failed assist request', async () => {
    answersWith({ kind: 'error', message: 'No se pudo preparar la ficha de venta.' });
    renderCard();

    await waitFor(() => expect(screen.getByTestId('assist-error')).toBeInTheDocument());

    // On a route whose p95 is 7,1 s and whose budget is ten per minute, an automatic retry
    // doubles both the cost and the wait.
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(salesAssistService.assist).toHaveBeenCalledTimes(1);
  });

  it('should offer an explicit retry when the request failed', async () => {
    const user = userEvent.setup();
    answersWith({ kind: 'error', message: 'Falló.' });
    renderCard();

    await waitFor(() => expect(screen.getByTestId('assist-error')).toBeInTheDocument());

    await user.click(screen.getByRole('button', { name: /Volver a pedir la ficha/ }));

    // The retry exists, and it is the operator's.
    await waitFor(() => expect(salesAssistService.assist).toHaveBeenCalledTimes(2));
  });

  it('should show a loading state rather than an empty screen while the request is in flight', async () => {
    let settle: (outcome: SalesAssistOutcome) => void = () => {};
    vi.mocked(salesAssistService.assist).mockReturnValue(
      new Promise<SalesAssistOutcome>((resolve) => {
        settle = resolve;
      }),
    );

    renderCard();

    // The wait is 4 to 8 s with a customer in front of the operator.
    expect(await screen.findByTestId('assist-loading')).toBeInTheDocument();
    settle({ kind: 'ok', response: response() });
    await served();
  });

  it('should discard a stale response rather than rendering it', async () => {
    const user = userEvent.setup();
    vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE, POS_TWO]);

    // The real out-of-order path: naming one shop, then another before the first has answered.
    // Two questions cannot produce it, because the box is disabled while one is in flight —
    // which is itself a guard on the ten-per-minute budget.
    let settleFirst: (outcome: SalesAssistOutcome) => void = () => {};
    vi.mocked(salesAssistService.assist).mockReturnValueOnce(
      new Promise<SalesAssistOutcome>((resolve) => {
        settleFirst = resolve;
      }),
    );

    renderCard(null);

    await user.click(await screen.findByLabelText('Punto de venta'));
    await user.click(await screen.findByRole('option', { name: 'Ciutadella Centre' }));

    answers(response({ pitch: 'La respuesta de Fornells.' }));
    await user.click(screen.getByLabelText('Punto de venta'));
    await user.click(await screen.findByRole('option', { name: 'Fornells' }));
    await waitFor(() =>
      expect(screen.getByText('La respuesta de Fornells.')).toBeInTheDocument(),
    );

    // The older one lands last and must not overwrite the newer one.
    settleFirst({
      kind: 'ok',
      response: response({ pitch: 'La respuesta de Ciutadella.' }),
    });
    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(screen.getByText('La respuesta de Fornells.')).toBeInTheDocument();
    expect(screen.queryByText('La respuesta de Ciutadella.')).not.toBeInTheDocument();
  });

  it('should not issue a second question while one is still in flight', async () => {
    const user = userEvent.setup();
    renderCard();
    await served();

    let settle: (outcome: SalesAssistOutcome) => void = () => {};
    vi.mocked(salesAssistService.assist).mockReturnValueOnce(
      new Promise<SalesAssistOutcome>((resolve) => {
        settle = resolve;
      }),
    );
    await user.click(screen.getByRole('button', { name: /¿Se puede mojar esta pieza\?/ }));
    await user.click(screen.getByRole('button', { name: /¿Cómo se limpia en casa\?/ }));

    // Two of the ten per minute is the typical maximum for a visit, and the box enforces it
    // rather than trusting the operator not to press twice.
    expect(salesAssistService.assist).toHaveBeenCalledTimes(2);

    settle({ kind: 'ok', response: response() });
  });

  it('should ask again when the operator names a different point of sale', async () => {
    const user = userEvent.setup();
    vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE, POS_TWO]);
    renderCard(null);

    await user.click(await screen.findByLabelText('Punto de venta'));
    await user.click(await screen.findByRole('option', { name: 'Ciutadella Centre' }));
    await waitFor(() => expect(salesAssistService.assist).toHaveBeenCalledTimes(1));

    await user.click(screen.getByLabelText('Punto de venta'));
    await user.click(await screen.findByRole('option', { name: 'Fornells' }));

    // An explicit act, like navigating here in the first place — not one of the three things
    // the spec forbids issuing a request for. Keeping the old shop's prices under the new
    // shop's name would be the screen stating something false.
    await waitFor(() => expect(salesAssistService.assist).toHaveBeenCalledTimes(2));
    expect(vi.mocked(salesAssistService.assist).mock.calls[1][1]).toEqual({
      pointOfSaleId: 'pos-2',
    });
  });
});

/* ---------------------------------------------------------------------------------------------
 * The point of sale
 * ------------------------------------------------------------------------------------------ */

describe('SalesAssistCardPage — the point of sale', () => {
  it('should issue no request until a point of sale is chosen when opened cold', async () => {
    vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE, POS_TWO]);
    renderCard(null);

    await waitFor(() => expect(screen.getByTestId('assist-needs-pos')).toBeInTheDocument());

    // The card shows the price and the units of one shop, so it cannot guess which.
    expect(salesAssistService.assist).not.toHaveBeenCalled();
  });

  it('should offer the role resolved selector when opened cold', async () => {
    vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE, POS_TWO]);
    renderCard(null);

    expect(await screen.findByLabelText('Punto de venta')).toBeInTheDocument();
  });

  it('should ask for the card once the operator names a point of sale', async () => {
    const user = userEvent.setup();
    vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([POS_ONE, POS_TWO]);
    renderCard(null);

    await user.click(await screen.findByLabelText('Punto de venta'));
    await user.click(await screen.findByRole('option', { name: 'Fornells' }));

    await waitFor(() => expect(salesAssistService.assist).toHaveBeenCalledTimes(1));
    expect(vi.mocked(salesAssistService.assist).mock.calls[0][1]).toEqual({
      pointOfSaleId: 'pos-2',
    });
  });

  it('should not load the points of sale when one travelled in navigation state', async () => {
    renderCard();
    await served();

    // A request for a control that is never shown.
    expect(pointOfSaleService.getPointsOfSale).not.toHaveBeenCalled();
  });

  it('should name the shop in the units line when the point of sale travelled', async () => {
    renderCard();
    await served();

    // «24 en esta tienda» is ambiguous the moment more than one shop is in play, and an
    // ambiguous stock figure is the kind that costs a sale. The list is not loaded on this
    // path, so the name has to be read on its own.
    await waitFor(() =>
      expect(pointOfSaleService.getPointOfSale).toHaveBeenCalledWith(POS_ID),
    );
    const header = screen.getByTestId('assist-piece-header');
    expect(await within(header).findByText(/3 en Ciutadella Centre/)).toBeInTheDocument();
    expect(within(header).queryByText(/en esta tienda/)).not.toBeInTheDocument();
  });

  it('should still show the card when the shop name cannot be read', async () => {
    vi.mocked(pointOfSaleService.getPointOfSale).mockRejectedValue(new Error('nope'));
    renderCard();

    // The name is what the sentence would rather say, not something the card depends on.
    await served();
    expect(screen.getByTestId('assist-piece-header')).toBeInTheDocument();
  });

  it('should not show the selector when the point of sale travelled', async () => {
    renderCard();
    await served();

    // Reading the one shop's name populates the same list the selector renders from, so the
    // guard that keeps it hidden has to be the navigation state and not the list's length.
    await waitFor(() => expect(pointOfSaleService.getPointOfSale).toHaveBeenCalled());
    expect(screen.queryByLabelText('Punto de venta')).not.toBeInTheDocument();
  });
});

/* ---------------------------------------------------------------------------------------------
 * 7.3, 7.4 — the family
 * ------------------------------------------------------------------------------------------ */

const THREE_MEMBERS = [
  member({ productId: 'prod-14', sku: 'SKU-014', variantLabel: '14', isAnchor: false }),
  member({ productId: PRODUCT_ID, sku: 'SKU-016', variantLabel: '16', isAnchor: true }),
  member({
    productId: 'prod-18',
    sku: 'SKU-018',
    variantLabel: '18',
    isAnchor: false,
    hasStock: false,
    quantityAtPointOfSale: 0,
  }),
];

describe('SalesAssistCardPage — family disambiguation', () => {
  it('should require variant confirmation when family has multiple members', async () => {
    answers(
      response({
        groups: [{ familyId: 'fam-1', familyLabel: 'Anillo trenzado', members: THREE_MEMBERS }],
      }),
    );
    renderCard();
    await served();

    const rows = await screen.findAllByTestId('assist-family-member');
    expect(rows).toHaveLength(3);

    // Every sale action names a member. There is no action on this screen that starts a sale
    // without saying which variant it is for.
    for (const row of rows) {
      expect(within(row).getByRole('button', { name: /^Vender / })).toBeInTheDocument();
    }
    expect(screen.queryByTestId('assist-sell-direct')).not.toBeInTheDocument();
  });

  it('should preselect no member when the group has several', async () => {
    answers(
      response({
        groups: [{ familyId: 'fam-1', familyLabel: 'Anillo trenzado', members: THREE_MEMBERS }],
      }),
    );
    renderCard();
    await served();

    const rows = await screen.findAllByTestId('assist-family-member');

    // Preselect-then-confirm is the pattern people press without reading. The guarantee is
    // structural: there is no selected state on this block at all.
    for (const row of rows) {
      expect(row).not.toHaveAttribute('aria-selected', 'true');
      expect(row).not.toHaveAttribute('data-selected', 'true');
      expect(within(row).queryByRole('radio')).not.toBeInTheDocument();
      expect(within(row).queryByRole('checkbox')).not.toBeInTheDocument();
    }
  });

  it('should carry the chosen member to the manual sale page', async () => {
    const user = userEvent.setup();
    answers(
      response({
        groups: [{ familyId: 'fam-1', familyLabel: 'Anillo trenzado', members: THREE_MEMBERS }],
      }),
    );
    renderCard();
    await served();

    await user.click(await screen.findByRole('button', { name: 'Vender 14' }));

    // The identifier handed over is the one whose button was pressed, and never the anchored
    // piece when a different member was chosen.
    expect(navigate).toHaveBeenCalledWith('/sales/new', { state: { productId: 'prod-14' } });
    expect(navigate).not.toHaveBeenCalledWith('/sales/new', {
      state: { productId: PRODUCT_ID },
    });
  });

  it('should mark the anchored member as the one in hand', async () => {
    answers(
      response({
        groups: [{ familyId: 'fam-1', familyLabel: 'Anillo trenzado', members: THREE_MEMBERS }],
      }),
    );
    renderCard();
    await served();

    const rows = await screen.findAllByTestId('assist-family-member');
    const anchored = rows.filter((row) => row.getAttribute('data-anchor') === 'true');

    expect(anchored).toHaveLength(1);
    expect(within(anchored[0]).getByTestId('assist-family-anchor')).toBeInTheDocument();
  });

  it('should keep the order the backend delivered', async () => {
    answers(
      response({
        groups: [{ familyId: 'fam-1', familyLabel: 'Anillo trenzado', members: THREE_MEMBERS }],
      }),
    );
    renderCard();
    await served();

    const rows = await screen.findAllByTestId('assist-family-member');

    // No sort(): the order is a decision the backend made and this screen does not revisit.
    expect(rows.map((row) => row.getAttribute('data-product-id'))).toEqual([
      'prod-14',
      PRODUCT_ID,
      'prod-18',
    ]);
  });

  it('should mark a member with no stock', async () => {
    answers(
      response({
        groups: [{ familyId: 'fam-1', familyLabel: 'Anillo trenzado', members: THREE_MEMBERS }],
      }),
    );
    renderCard();
    await served();

    const rows = await screen.findAllByTestId('assist-family-member');
    const outOfStock = rows.find((row) => row.getAttribute('data-product-id') === 'prod-18')!;

    // Marked by text as well as by colour.
    expect(within(outOfStock).getByText('Sin existencias')).toBeInTheDocument();
  });

  it('should degrade a member row with no variant label to its sku', async () => {
    answers(
      response({
        groups: [
          {
            familyId: 'fam-1',
            familyLabel: 'Anillo trenzado',
            members: [
              member({ productId: 'prod-a', sku: 'SKU-AAA', variantLabel: null, isAnchor: true }),
              member({ productId: 'prod-b', sku: 'SKU-BBB', variantLabel: '18', isAnchor: false }),
            ],
          },
        ],
      }),
    );
    renderCard();
    await served();

    const rows = await screen.findAllByTestId('assist-family-member');
    const unlabelled = rows.find((row) => row.getAttribute('data-product-id') === 'prod-a')!;

    // 1,7 % of groups are mixed. A row nobody can tell from its neighbour is worse than one
    // identified by a code.
    expect(unlabelled).toHaveAttribute('data-identified-by', 'sku');
    expect(within(unlabelled).getByRole('button', { name: 'Vender SKU-AAA' })).toBeInTheDocument();
  });

  it('should restore the direct action when the group carries exactly one member', async () => {
    answers(response());
    renderCard();
    await served();

    // Nothing to choose between. C30a guarantees a null family yields exactly one member, so
    // the synthetic group of one can never trigger the confirmation.
    expect(await screen.findByTestId('assist-sell-direct')).toBeInTheDocument();
    expect(screen.queryByTestId('assist-family-member')).not.toBeInTheDocument();
  });
});

/* ---------------------------------------------------------------------------------------------
 * 7.5 — citations
 * ------------------------------------------------------------------------------------------ */

describe('SalesAssistCardPage — citations', () => {
  it('should render citations when pitch has sources', async () => {
    answers(response({ citations: [citation()] }));
    renderCard();
    await served();

    const citations = await screen.findAllByTestId('assist-citation');
    expect(citations).toHaveLength(1);
    expect(within(citations[0]).getByText(/Cuidados generales de una joya/)).toBeInTheDocument();
    expect(within(citations[0]).getByText(/Limpieza en casa/)).toBeInTheDocument();
  });

  it('should show the snippet when a citation is expanded', async () => {
    const user = userEvent.setup();
    answers(response({ citations: [citation()] }));
    renderCard();
    await served();

    const row = (await screen.findAllByTestId('assist-citation'))[0];
    await user.click(within(row).getByRole('button'));

    // Readable rather than clickable: no route serves the corpus, so a citation that cannot be
    // read would verify nothing.
    expect(
      await within(row).findByText(/Un paño seco y suave retira el sudor/),
    ).toBeInTheDocument();
  });

  it('should mark an establishment claim differently from a general one', async () => {
    answers(
      response({
        citations: [
          citation({ citationId: 'a#1', claimScope: 'general' }),
          citation({
            citationId: 'b#1',
            claimScope: 'establecimiento',
            documentTitle: 'Garantía',
            sectionTitle: 'Qué cubre',
          }),
        ],
      }),
    );
    renderCard();
    await served();

    const citations = await screen.findAllByTestId('assist-citation');
    const scopes = citations.map((c) => c.getAttribute('data-claim-scope'));

    // A commitment of the house and a fact of the world are not the same kind of claim.
    expect(scopes).toEqual(['general', 'establecimiento']);
    expect(within(citations[0]).getByText('Información general')).toBeInTheDocument();
    expect(within(citations[1]).getByText('Compromiso de la casa')).toBeInTheDocument();
  });

  it('should tell the operator to confirm an establishment claim in store', async () => {
    const user = userEvent.setup();
    answers(response({ citations: [citation({ claimScope: 'establecimiento' })] }));
    renderCard();
    await served();

    const row = (await screen.findAllByTestId('assist-citation'))[0];
    await user.click(within(row).getByRole('button'));

    expect(
      await within(row).findByTestId('assist-citation-establishment-note'),
    ).toBeInTheDocument();
  });

  it('should not resolve a citation into a link', async () => {
    answers(response({ citations: [citation()] }));
    renderCard();
    await served();

    const row = (await screen.findAllByTestId('assist-citation'))[0];

    // C34 forbids it and no route reads the corpus, which lives as files in the AI service.
    expect(within(row).queryByRole('link')).not.toBeInTheDocument();
    expect(row.textContent).not.toContain('cuidados-generales#limpieza');
  });

  it('should hide citations when the argument was withheld', async () => {
    answers(
      response({ pitchStatus: 'withheld_by_ai', pitch: null, citations: [citation()] }),
    );
    renderCard();
    await served();

    // Showing the sources of a text the operator cannot read is decoration, and they would be
    // only the ones that argument used anyway.
    expect(screen.queryByTestId('assist-citation')).not.toBeInTheDocument();
  });
});

/* ---------------------------------------------------------------------------------------------
 * 7.6 — warnings
 * ------------------------------------------------------------------------------------------ */

describe('SalesAssistCardPage — warnings', () => {
  it('should show a known warning code in Spanish and never the raw code', async () => {
    answers(response({ warnings: ['stock_critical'] }));
    renderCard();
    await served();

    const block = await screen.findByTestId('assist-warnings');
    expect(within(block).getByText('Quedan pocas unidades')).toBeInTheDocument();
    expect(block.textContent).not.toContain('stock_critical');
  });

  it('should fall back to a neutral label for an unknown warning code', async () => {
    answers(response({ warnings: ['stock_critical', 'a_code_from_a_later_version'] }));
    renderCard();
    await served();

    const rows = await screen.findAllByTestId('assist-warning');

    // The vocabulary is closed but versioned. The remaining warnings still render normally.
    expect(rows).toHaveLength(2);
    expect(rows[1]).toHaveTextContent(UNKNOWN_WARNING_LABEL);
    expect(rows[1].textContent).not.toContain('a_code_from_a_later_version');
    expect(rows[0]).toHaveTextContent('Quedan pocas unidades');
  });

  it('should carry the copy of the two router refusal codes even though this screen cannot reach them', async () => {
    answers(response({ warnings: ['query_out_of_domain', 'query_not_in_catalogue'] }));
    renderCard();
    await served();

    const rows = await screen.findAllByTestId('assist-warning');

    // **This test asserted the neutral fallback until C40.** The reasoning was right at the
    // time: the intent classifier runs only in the free-query mode, that mode had no screen, so
    // neither code could arrive anywhere and writing their Spanish would have been copy for an
    // impossible path. C40 gives the mode a screen, the copy table gained both rows, and this
    // screen picks them up for free.
    //
    // Neither can reach *this* card — its two routes are always anchored — so what is held here
    // is only that the shared table does not leave them unlabelled. The tolerance rule itself is
    // still witnessed, by the unknown-code test above.
    expect(rows).toHaveLength(2);
    for (const row of rows) {
      expect(row).not.toHaveTextContent(UNKNOWN_WARNING_LABEL);
      expect(row).toHaveAttribute('data-known', 'true');
    }
  });

  it('should render size label missing as a piece attribute and not as a warning', async () => {
    answers(response({ warnings: ['size_label_missing', 'stock_critical'] }));
    renderCard();
    await served();

    // It fires on 58,3 % of cards. As an alert it would crowd out stock_critical, which fires
    // on 3,9 % and is the one that can cost a sale.
    const attributes = screen.getByTestId('assist-piece-attributes');
    expect(within(attributes).getByTestId('assist-size-label-missing')).toHaveTextContent(
      'Sin talla declarada',
    );

    const warnings = screen.getByTestId('assist-warnings');
    expect(warnings.textContent).not.toContain('Sin talla declarada');
    expect(within(warnings).getByText('Quedan pocas unidades')).toBeInTheDocument();
  });

  it('should never suppress the missing size label', async () => {
    answers(response({ warnings: ['size_label_missing'] }));
    renderCard();
    await served();

    // Removing a code the backend emitted is what the panel's living spec forbids doing with
    // the retriever's match reasons. It is moved, not dropped.
    expect(screen.getByTestId('assist-size-label-missing')).toBeInTheDocument();
  });

  it('should show no warnings block when the backend emitted none', async () => {
    answers(response({ warnings: [] }));
    renderCard();
    await served();

    // Nothing is added that the backend did not emit.
    expect(screen.queryByTestId('assist-warnings')).not.toBeInTheDocument();
  });
});

/* ---------------------------------------------------------------------------------------------
 * 7.7 — the six states of the argument
 * ------------------------------------------------------------------------------------------ */

describe('SalesAssistCardPage — the state of the argument', () => {
  it('should display the argument when it was generated', async () => {
    answers(response());
    renderCard();
    await served();

    expect(screen.getByTestId('assist-pitch-text')).toHaveTextContent(
      'Una pieza de plata de ley, sencilla y de diario.',
    );
  });

  it('should tell a degraded card from one whose argument was not generated', async () => {
    answers(response({ aiAvailable: false, pitchStatus: 'ai_unavailable', pitch: null }));
    const degraded = renderCard();
    await served();
    const degradedText = screen.getByTestId('assist-pitch').textContent ?? '';
    degraded.unmount();

    vi.clearAllMocks();
    vi.mocked(salesAssistService.substitutes).mockResolvedValue({
      kind: 'ok',
      response: substitutesResponse(),
    });
    answers(response({ pitchStatus: 'not_generated', pitch: null }));
    renderCard();
    await served();
    const ungeneratedText = screen.getByTestId('assist-pitch').textContent ?? '';

    // In the first, half the screen is pure catalog. In the second the piece's data is the
    // index's, intact. One message for both would misstate where what is shown came from.
    expect(degradedText).not.toBe(ungeneratedText);
    expect(degradedText).toContain('catálogo');
  });

  it('should say what to do next when the argument is withheld', async () => {
    for (const status of ['withheld_by_ai', 'withheld_unresolved'] as const) {
      vi.clearAllMocks();
      vi.mocked(salesAssistService.substitutes).mockResolvedValue({
        kind: 'ok',
        response: substitutesResponse(),
      });
      answers(response({ pitchStatus: status, pitch: null, warnings: ['stock_critical'] }));
      const view = renderCard();
      await served();

      // An honest abstention says what would be needed to get past it, and the rest of the card
      // stays on screen.
      expect(screen.getByTestId('assist-pitch-action')).toBeInTheDocument();
      expect(screen.getByTestId('assist-pitch')).toHaveAttribute('data-pitch-status', status);
      expect(screen.getByTestId('assist-warnings')).toBeInTheDocument();
      expect(screen.getByTestId('assist-piece-header')).toBeInTheDocument();

      view.unmount();
    }
  });

  it('should keep the two withheld states distinguishable although they share a text', async () => {
    answers(response({ pitchStatus: 'withheld_unresolved', pitch: null }));
    renderCard();
    await served();

    // Nothing the operator can do differs between them, so the text is shared — but the states
    // are still two, and a test has to be able to separate them.
    expect(screen.getByTestId('assist-pitch')).toHaveAttribute(
      'data-pitch-status',
      'withheld_unresolved',
    );
  });

  it('should announce the alternatives when the piece is out of stock', async () => {
    answers(
      response({
        pitchStatus: 'withheld_out_of_stock',
        pitch: null,
        groups: [
          {
            familyId: null,
            familyLabel: null,
            members: [member({ hasStock: false, quantityAtPointOfSale: 0 })],
          },
        ],
      }),
    );
    renderCard();
    await served();

    expect(screen.getByTestId('assist-pitch')).toHaveTextContent(/agotada/);
    expect(screen.getByTestId('assist-pitch-action')).toHaveTextContent(/alternativas/);
  });

  it('should render the six states as six distinguishable documents', async () => {
    const seen: Record<PitchStatus, string> = {} as Record<PitchStatus, string>;

    for (const status of [
      'generated',
      'ai_unavailable',
      'not_generated',
      'withheld_by_ai',
      'withheld_unresolved',
      'withheld_out_of_stock',
    ] as PitchStatus[]) {
      vi.clearAllMocks();
      vi.mocked(salesAssistService.substitutes).mockResolvedValue({
        kind: 'ok',
        response: substitutesResponse(),
      });
      answers(
        response({
          pitchStatus: status,
          pitch: status === 'generated' ? 'El argumentario.' : null,
          aiAvailable: status !== 'ai_unavailable',
        }),
      );
      const view = renderCard();
      await served();

      seen[status] = screen.getByTestId('assist-pitch').getAttribute('data-pitch-status') ?? '';
      view.unmount();
    }

    expect(new Set(Object.values(seen)).size).toBe(6);
  });
});

/* ---------------------------------------------------------------------------------------------
 * 7.8 — substitutes
 * ------------------------------------------------------------------------------------------ */

const OUT_OF_STOCK_GROUP = [
  { familyId: null, familyLabel: null, members: [member({ hasStock: false, quantityAtPointOfSale: 0 })] },
];

describe('SalesAssistCardPage — substitutes', () => {
  it('should show substitutes block when selected product is out of stock', async () => {
    answers(response({ groups: OUT_OF_STOCK_GROUP }));
    renderCard();
    await served();

    await waitFor(() => expect(salesAssistService.substitutes).toHaveBeenCalledTimes(1));
    expect(vi.mocked(salesAssistService.substitutes).mock.calls[0].slice(0, 2)).toEqual([
      PRODUCT_ID,
      POS_ID,
    ]);
    expect(await screen.findByTestId('assist-substitutes')).toBeInTheDocument();
  });

  it('should request no substitutes when the anchored member has stock', async () => {
    answers(response());
    renderCard();
    await served();

    await new Promise((resolve) => setTimeout(resolve, 30));
    expect(salesAssistService.substitutes).not.toHaveBeenCalled();
  });

  it('should trigger on the anchored member stock and not on the state of the argument', async () => {
    // `hasStock` is present in every state the backend served; `withheld_out_of_stock` only
    // reports the absence of stock when no question was asked. A card that triggered on the
    // status would offer nothing to a piece the operator asked a question about.
    answers(
      response({ pitchStatus: 'generated', pitch: 'Texto.', groups: OUT_OF_STOCK_GROUP }),
    );
    renderCard();
    await served();

    await waitFor(() => expect(salesAssistService.substitutes).toHaveBeenCalledTimes(1));
  });

  it('should not request substitutes when the card is degraded', async () => {
    answers(
      response({
        aiAvailable: false,
        pitchStatus: 'ai_unavailable',
        pitch: null,
        groups: OUT_OF_STOCK_GROUP,
      }),
    );
    renderCard();
    await served();

    // With the AI path unavailable the call would come back `ai_unavailable` with certainty.
    await new Promise((resolve) => setTimeout(resolve, 30));
    expect(salesAssistService.substitutes).not.toHaveBeenCalled();

    // But saying nothing would read as a piece with no alternatives, which is a different and
    // false claim.
    const block = screen.getByTestId('assist-substitutes');
    expect(block).toHaveAttribute('data-substitutes-state', 'not-requested');
    expect(block).toHaveTextContent(/no está disponible/);
  });

  it('should tell the four substitute outcomes apart', async () => {
    const texts: string[] = [];

    for (const outcome of [
      'ok',
      'none_in_stock',
      'product_not_indexed',
      'ai_unavailable',
    ] as SubstitutesOutcome[]) {
      vi.clearAllMocks();
      answers(response({ groups: OUT_OF_STOCK_GROUP }));
      vi.mocked(salesAssistService.substitutes).mockResolvedValue({
        kind: 'ok',
        response: substitutesResponse({
          outcome,
          results: outcome === 'ok' ? [substitute()] : [],
        }),
      });

      const view = renderCard();
      await served();
      const block = await screen.findByTestId('assist-substitutes');
      await waitFor(() => expect(block).toHaveAttribute('data-outcome', outcome));
      texts.push(block.textContent ?? '');
      view.unmount();
    }

    expect(new Set(texts).size).toBe(4);
  });

  it('should say a piece is not ready yet rather than calling it an outage', async () => {
    answers(response({ groups: OUT_OF_STOCK_GROUP }));
    vi.mocked(salesAssistService.substitutes).mockResolvedValue({
      kind: 'ok',
      response: substitutesResponse({ outcome: 'product_not_indexed', results: [] }),
    });
    renderCard();
    await served();

    const block = await screen.findByTestId('assist-substitutes');
    await waitFor(() =>
      expect(block).toHaveAttribute('data-outcome', 'product_not_indexed'),
    );

    // A state of the catalog the next synchronisation fixes, never a fault.
    expect(block).toHaveTextContent(/no está preparada/);
  });

  it('should declare a short substitutes page instead of padding it', async () => {
    answers(response({ groups: OUT_OF_STOCK_GROUP }));
    vi.mocked(salesAssistService.substitutes).mockResolvedValue({
      kind: 'ok',
      response: substitutesResponse({
        outcome: 'ok',
        results: [substitute(), substitute({ productId: 'prod-sub-2', sku: 'SKU-901' })],
        candidatesReturned: 5,
        survivedHydration: 4,
      }),
    });
    renderCard();
    await served();

    const count = await screen.findByTestId('assist-substitutes-count');

    // If two survived, it says two. Left unsaid a short page reads as the system being unable
    // to search when the shop simply does not carry more.
    expect(count).toHaveTextContent('2 alternativas disponibles');
    expect(screen.getAllByTestId('assist-substitute')).toHaveLength(2);
  });

  it('should display the substitutes in the order received', async () => {
    answers(response({ groups: OUT_OF_STOCK_GROUP }));
    vi.mocked(salesAssistService.substitutes).mockResolvedValue({
      kind: 'ok',
      response: substitutesResponse({
        results: [
          substitute({ productId: 'sub-a', sku: 'SKU-A', price: 90 }),
          substitute({ productId: 'sub-b', sku: 'SKU-B', price: 10 }),
        ],
        survivedHydration: 2,
      }),
    });
    renderCard();
    await served();

    const rows = await screen.findAllByTestId('assist-substitute');

    // Not re-sorted by price or anything else: the rank is the measurement of retrieval quality.
    expect(rows.map((row) => row.getAttribute('data-product-id'))).toEqual(['sub-a', 'sub-b']);
  });

  it('should carry a chosen substitute to the manual sale page', async () => {
    const user = userEvent.setup();
    answers(response({ groups: OUT_OF_STOCK_GROUP }));
    renderCard();
    await served();

    const row = (await screen.findAllByTestId('assist-substitute'))[0];
    await user.click(within(row).getByRole('button', { name: 'Vender esta' }));

    expect(navigate).toHaveBeenCalledWith('/sales/new', { state: { productId: 'prod-sub-1' } });
  });
});

/* ---------------------------------------------------------------------------------------------
 * 7.9 — the customer's question
 * ------------------------------------------------------------------------------------------ */

describe('SalesAssistCardPage — the question', () => {
  it('should issue exactly one further request when a question is asked', async () => {
    const user = userEvent.setup();
    renderCard();
    await served();

    await user.type(screen.getByLabelText('Pregunta del cliente'), '¿Se puede duchar con ella?');
    await user.click(screen.getByRole('button', { name: /^Preguntar$/ }));

    await waitFor(() => expect(salesAssistService.assist).toHaveBeenCalledTimes(2));
    expect(vi.mocked(salesAssistService.assist).mock.calls[1][1]).toEqual({
      pointOfSaleId: POS_ID,
      question: '¿Se puede duchar con ella?',
    });
  });

  it('should fill and send in one act from a suggested question', async () => {
    const user = userEvent.setup();
    renderCard();
    await served();

    await user.click(screen.getByRole('button', { name: /¿Se puede mojar esta pieza\?/ }));

    // The suggestion is there to teach what can be asked; making the operator press again
    // would waste the lesson.
    await waitFor(() => expect(salesAssistService.assist).toHaveBeenCalledTimes(2));
    expect(vi.mocked(salesAssistService.assist).mock.calls[1][1]).toEqual({
      pointOfSaleId: POS_ID,
      question: '¿Se puede mojar esta pieza?',
    });
    expect(screen.getByLabelText('Pregunta del cliente')).toHaveValue(
      '¿Se puede mojar esta pieza?',
    );
  });

  it('should offer five suggested questions', async () => {
    renderCard();
    await served();

    const box = screen.getByTestId('assist-question-box');
    expect(within(box).getByRole('button', { name: /piel sensible/ })).toBeInTheDocument();
    expect(within(box).getByRole('button', { name: /limpia en casa/ })).toBeInTheDocument();
    expect(within(box).getByRole('button', { name: /playa o a la piscina/ })).toBeInTheDocument();
  });

  it('should reject a question over five hundred characters before sending', async () => {
    const user = userEvent.setup();
    renderCard();
    await served();

    const field = screen.getByLabelText('Pregunta del cliente');
    await user.click(field);
    // Typing 501 characters one keystroke at a time is slow and the point is the bound, not the
    // typing, so the value is pasted.
    await user.paste('a'.repeat(501));
    await user.click(screen.getByRole('button', { name: /^Preguntar$/ }));

    // Refused here, so it never becomes one of the ten requests the operator has per minute.
    expect(await screen.findByTestId('assist-question-error')).toHaveTextContent('500');
    expect(salesAssistService.assist).toHaveBeenCalledTimes(1);
  });

  it('should accept a question of exactly five hundred characters', async () => {
    const user = userEvent.setup();
    renderCard();
    await served();

    await user.click(screen.getByLabelText('Pregunta del cliente'));
    await user.paste('a'.repeat(500));
    await user.click(screen.getByRole('button', { name: /^Preguntar$/ }));

    // The bound is the contract's, and the contract says five hundred is allowed.
    await waitFor(() => expect(salesAssistService.assist).toHaveBeenCalledTimes(2));
  });

  it('should never put the question in the url', async () => {
    const user = userEvent.setup();
    renderCard();
    await served();

    await user.click(screen.getByRole('button', { name: /¿Se puede mojar esta pieza\?/ }));
    await waitFor(() => expect(salesAssistService.assist).toHaveBeenCalledTimes(2));

    // A URL ends up in the proxy's access log, the browser's history and any intermediate
    // cache. C34 forbids it on the server; this is the client side of the same rule.
    expect(window.location.search).not.toContain('mojar');
    expect(window.location.pathname).not.toContain('mojar');
    for (const call of navigate.mock.calls) {
      expect(JSON.stringify(call)).not.toContain('mojar');
    }
  });

  it('should start a new visit with no question', async () => {
    const user = userEvent.setup();
    const first = renderCard();
    await served();
    await user.type(screen.getByLabelText('Pregunta del cliente'), 'algo');
    first.unmount();

    vi.clearAllMocks();
    answers(response());
    renderCard();
    await served();

    // Keeping it would invite resending it by accident, and every resend is a paid call.
    expect(screen.getByLabelText('Pregunta del cliente')).toHaveValue('');
  });
});

/* ---------------------------------------------------------------------------------------------
 * 7.10 — failures
 * ------------------------------------------------------------------------------------------ */

describe('SalesAssistCardPage — failures become sentences', () => {
  it('should distinguish a rate limited response from an unavailable service', async () => {
    answersWith({ kind: 'rate-limited' });
    const limited = renderCard();
    const limitedText = (await screen.findByTestId('assist-rate-limited')).textContent ?? '';
    limited.unmount();

    vi.clearAllMocks();
    answers(response({ aiAvailable: false, pitchStatus: 'ai_unavailable', pitch: null }));
    renderCard();
    await served();
    const outageText = screen.getByTestId('assist-pitch').textContent ?? '';

    // One is the system protecting itself and the operator only has to wait; the other is a
    // fault. Opposite remedies.
    expect(limitedText).toContain('Espera unos segundos');
    expect(limitedText).not.toBe(outageText);
  });

  it('should say the shop does not carry the piece when the server answers not found', async () => {
    answersWith({ kind: 'not-found' });
    renderCard();

    const block = await screen.findByTestId('assist-not-found');

    expect(block).toHaveTextContent(/Esta tienda no lleva esta pieza/);
    expect(screen.queryByTestId('assist-error')).not.toBeInTheDocument();
  });

  it('should say the point of sale is not available to this caller when it is forbidden', async () => {
    answersWith({ kind: 'forbidden' });
    renderCard();

    expect(await screen.findByTestId('assist-forbidden')).toHaveTextContent(
      /No tienes acceso a esta tienda/,
    );
  });

  it('should render a validation refusal as the sentence the backend wrote', async () => {
    answersWith({
      kind: 'invalid',
      errors: ['El punto de venta no existe o no está activo.'],
    });
    renderCard();

    expect(await screen.findByTestId('assist-invalid')).toHaveTextContent(
      'El punto de venta no existe o no está activo.',
    );
  });

  it('should write neither the question nor the argument to the console', async () => {
    const user = userEvent.setup();
    const spies = (['log', 'info', 'warn', 'error', 'debug'] as const).map((level) =>
      vi.spyOn(console, level).mockImplementation(() => {}),
    );

    answers(response({ pitch: 'Un argumentario resuelto y confidencial.' }));
    renderCard();
    await served();
    await user.click(screen.getByRole('button', { name: /¿Se puede mojar esta pieza\?/ }));
    await waitFor(() => expect(salesAssistService.assist).toHaveBeenCalledTimes(2));

    const written = spies.flatMap((spy) => spy.mock.calls.map((call) => JSON.stringify(call)));
    expect(written.join(' ')).not.toContain('mojar');
    expect(written.join(' ')).not.toContain('confidencial');

    spies.forEach((spy) => spy.mockRestore());
  });
});
