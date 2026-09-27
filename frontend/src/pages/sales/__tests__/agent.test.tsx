/**
 * The agent panel (EP15 / C42)
 *
 * **The thread is what these tests are about.** Each turn owning its answer block is the decision the
 * whole panel is built around: a single results area refreshed on each turn leaves the operator
 * reading one turn's argument while the rows beneath already belong to the next, and when the loop
 * pivots to substitutes the piece being looked at disappears with no explanation.
 *
 * Services are mocked with `vi.mock` rather than handled by MSW: an unhandled MSW request only warns,
 * so a test could pass having asserted nothing.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';

import { AgentSalesPage } from '../agent';
import { agentAssistService } from '@/services/agent-assist.service';
import { aiSearchService } from '@/services/ai-search.service';
import * as pointOfSaleService from '@/services/point-of-sale.service';
import type { AgentAssistResponse } from '@/types/ai-agent.types';
import type { AssistedSearchResult } from '@/types/ai-search.types';

vi.mock('@/services/agent-assist.service', () => ({
  agentAssistService: { answer: vi.fn() },
  default: { answer: vi.fn() },
}));

vi.mock('@/services/ai-search.service', () => ({
  aiSearchService: { getAvailability: vi.fn(), reportSelection: vi.fn() },
  default: { getAvailability: vi.fn(), reportSelection: vi.fn() },
}));

vi.mock('@/services/point-of-sale.service', () => ({
  getPointsOfSale: vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() },
}));

const mockAuth = { user: { role: 'Operator' } as { role: string } | null };

vi.mock('@/providers/auth-provider', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useAuth: () => mockAuth,
}));

const navigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigate };
});

const POS_ONE = '11111111-1111-1111-1111-111111111111';
const POS_TWO = '22222222-2222-2222-2222-222222222222';

function member(sku: string): AssistedSearchResult {
  return {
    productId: `p-${sku}`,
    sku,
    name: `Pieza ${sku}`,
    price: 39.9,
    quantityAtPointOfSale: 2,
    hasStock: true,
    primaryPhotoUrl: null,
    collectionName: null,
    score: 0.8,
    matchReasons: ['vector'],
    materials: ['plata'],
    familyId: null,
    variantLabel: null,
  } as AssistedSearchResult;
}

function answer(overrides: Partial<AgentAssistResponse> = {}): AgentAssistResponse {
  return {
    groups: [
      { familyId: null, familyLabel: null, origin: 'catalogo', members: [member('ARO-M')] },
    ],
    pitchStatus: 'generated',
    pitch: 'De las dos, la de aro fino es la más sobria.',
    citations: [],
    warnings: [],
    abstained: false,
    aiAvailable: true,
    partial: false,
    stopReason: 'sin_mas_herramientas',
    iterations: 2,
    toolCallsUsed: 3,
    trace: [],
    agentPromptVersion: 'assist/v6',
    searchEventId: 'ev-1',
    candidatesReturned: 1,
    survivedHydration: 1,
    usage: {
      model: 'openai/gpt-4o',
      promptTokens: 12876,
      completionTokens: 240,
      totalTokens: 13116,
      promptVersion: 'assist/v6',
      providerCalls: 4,
      aiMs: 5311,
      totalMs: 5500,
    },
    ...overrides,
  };
}

function renderPage() {
  return render(
    <BrowserRouter>
      <AgentSalesPage />
    </BrowserRouter>,
  );
}

/** Waits for the shop list to settle, which is what enables the composer. */
async function ready() {
  await waitFor(() =>
    expect(screen.getByLabelText('Escribe tu pregunta al agente')).toBeEnabled(),
  );
}

async function ask(user: ReturnType<typeof userEvent.setup>, text: string) {
  await user.type(screen.getByLabelText('Escribe tu pregunta al agente'), text);
  await user.click(screen.getByRole('button', { name: /^preguntar$/i }));
}

beforeEach(() => {
  vi.clearAllMocks();
  mockAuth.user = { role: 'Operator' };

  vi.mocked(pointOfSaleService.getPointsOfSale).mockResolvedValue([
    { id: POS_ONE, name: 'Tienda Mahón', code: 'MAO', isActive: true },
    { id: POS_TWO, name: 'Tienda Ciutadella', code: 'CIU', isActive: true },
  ] as never);

  vi.mocked(aiSearchService.getAvailability).mockResolvedValue({
    kind: 'ok',
    availability: {
      pointOfSaleId: POS_ONE,
      semanticSearchAvailable: true,
      assistedAnswerAvailable: true,
      agentAvailable: true,
    },
  });

  vi.mocked(agentAssistService.answer).mockResolvedValue({ kind: 'ok', response: answer() });
});

describe('the thread', () => {
  it("should keep each turn's answer anchored to its own turn", async () => {
    const user = userEvent.setup();
    renderPage();
    await ready();

    await ask(user, 'busco un anillo');
    await waitFor(() => expect(screen.getAllByTestId('agent-exchange')).toHaveLength(1));

    vi.mocked(agentAssistService.answer).mockResolvedValue({
      kind: 'ok',
      response: answer({
        pitch: 'En dorado te queda esta otra.',
        groups: [
          { familyId: null, familyLabel: null, origin: 'catalogo', members: [member('ARO-D')] },
        ],
      }),
    });

    await ask(user, 'y en dorado');

    await waitFor(() => expect(screen.getAllByTestId('agent-exchange')).toHaveLength(2));

    // Both questions stay in the thread: it is the audit trail of the conversation.
    expect(screen.getByText(/busco un anillo/)).toBeInTheDocument();
    expect(screen.getByText(/y en dorado/)).toBeInTheDocument();
  });

  it('should collapse the previous block to one line and reopen it when activated', async () => {
    const user = userEvent.setup();
    renderPage();
    await ready();

    await ask(user, 'busco un anillo');
    await waitFor(() => expect(screen.getByTestId('agent-answer-block')).toBeInTheDocument());

    await ask(user, 'y en dorado');
    await waitFor(() => expect(screen.getAllByTestId('agent-exchange')).toHaveLength(2));

    // Only the last one is open, so the act of selling always belongs to what is open.
    const blocks = screen.getAllByTestId('agent-answer-block');
    expect(blocks).toHaveLength(1);

    const summary = screen.getByTestId('agent-exchange-summary');
    expect(summary).toHaveTextContent(/1 piezas/);
    expect(summary).toHaveTextContent(/2 vueltas/);

    await user.click(summary);

    // Reopening the earlier one closes the later: one block open at a time, always.
    await waitFor(() => expect(screen.getAllByTestId('agent-answer-block')).toHaveLength(1));
  });

  it('should not de-duplicate a piece repeated across turns', async () => {
    const user = userEvent.setup();
    renderPage();
    await ready();

    await ask(user, 'busco un anillo');
    await waitFor(() => expect(screen.getAllByTestId('agent-exchange')).toHaveLength(1));

    // The same piece, again. Each turn's evidence is its own: a piece that survived a second search
    // is a stronger recommendation, not a duplicate row.
    await ask(user, 'y algo parecido');
    await waitFor(() => expect(screen.getAllByTestId('agent-exchange')).toHaveLength(2));

    await user.click(screen.getByTestId('agent-exchange-summary'));

    // The first block reopened still shows it, and the summary of the second reports it too.
    await waitFor(() => expect(screen.getByTestId('agent-answer-block')).toBeInTheDocument());
    expect(screen.getByText('ARO-M')).toBeInTheDocument();
  });

  it('should send the whole transcript including the assistant turn on the second turn', async () => {
    const user = userEvent.setup();
    renderPage();
    await ready();

    await ask(user, 'busco un anillo');
    await waitFor(() => expect(screen.getByTestId('agent-answer-block')).toBeInTheDocument());

    await ask(user, 'y en dorado');

    await waitFor(() => expect(agentAssistService.answer).toHaveBeenCalledTimes(2));

    const second = vi.mocked(agentAssistService.answer).mock.calls[1][0];
    expect(second.turns.map((turn) => turn.role)).toEqual(['operario', 'asistente', 'operario']);
    expect(second.turns[1].text).toBe('De las dos, la de aro fino es la más sobria.');
  });
});

describe('the composer', () => {
  it('should count the assistant turns towards the transcript caps', async () => {
    const user = userEvent.setup();
    renderPage();
    await ready();

    const before = screen.getByTestId('agent-composer-counters').textContent;
    expect(before).toMatch(/turnos 0\/12/);

    await ask(user, 'busco un anillo');
    await waitFor(() => expect(screen.getByTestId('agent-answer-block')).toBeInTheDocument());

    // Two turns after one exchange, not one: the argument travels back, and it is most of the cost.
    const after = screen.getByTestId('agent-composer-counters').textContent!;
    expect(after).toMatch(/turnos 2\/12/);
    expect(after).toMatch(/4\.?000 car\./);
  });

  it('should stop the composer with a reason when a cap is reached', async () => {
    const user = userEvent.setup();
    renderPage();
    await ready();

    // Six exchanges is twelve turns, which is the cap: the turn cap bites before the character one.
    for (let turn = 0; turn < 6; turn += 1) {
      await ask(user, `pregunta ${turn}`);
      await waitFor(() =>
        expect(screen.getAllByTestId('agent-exchange')).toHaveLength(turn + 1),
      );
    }

    await waitFor(() => expect(screen.getByTestId('agent-composer-closed')).toBeInTheDocument());

    expect(screen.getByTestId('agent-composer-closed')).toHaveTextContent(/tope de turnos/i);
    // And the field goes with it: a field that still takes text while the button refuses is how an
    // operator writes a paragraph for nothing.
    expect(screen.getByLabelText('Escribe tu pregunta al agente')).toBeDisabled();

    const calls = vi.mocked(agentAssistService.answer).mock.calls.length;
    expect(calls).toBe(6);
  });

  it('should disable the composer while a turn is in flight', async () => {
    const user = userEvent.setup();
    let release: (value: unknown) => void = () => {};
    vi.mocked(agentAssistService.answer).mockReturnValue(
      new Promise((resolve) => {
        release = resolve;
      }) as never,
    );

    renderPage();
    await ready();

    await ask(user, 'busco un anillo');

    await waitFor(() =>
      expect(screen.getByLabelText('Escribe tu pregunta al agente')).toBeDisabled(),
    );
    // The wait, stated before it happens: p50 5.3 s and up to 11.9 s measured, long enough that a
    // bare spinner reads as a hang.
    expect(screen.getByTestId('agent-composer-pending')).toHaveTextContent(/5 segundos/);

    release({ kind: 'ok', response: answer() });
    await waitFor(() =>
      expect(screen.getByLabelText('Escribe tu pregunta al agente')).toBeEnabled(),
    );
  });
});

describe('the scope', () => {
  it('should default to the operator own shop and never to every shop', async () => {
    renderPage();
    await ready();

    expect(screen.getByLabelText('Punto de venta')).toHaveTextContent('Tienda Mahón');
    expect(screen.queryByTestId('agent-all-shops-warning')).not.toBeInTheDocument();
  });

  it('should not offer the every-shop scope to an operator', async () => {
    const user = userEvent.setup();
    renderPage();
    await ready();

    await user.click(screen.getByLabelText('Punto de venta'));

    // The sibling panel's rule, copied: offered to the administrator only, while the backend serves
    // it to both. The boundary actually protected is that nobody may name an unassigned shop.
    expect(screen.queryByText('Todas las tiendas')).not.toBeInTheDocument();
  });

  it('should warn that the every-shop scope stops the agent offering alternatives', async () => {
    mockAuth.user = { role: 'Administrator' };
    const user = userEvent.setup();
    renderPage();
    await ready();

    await user.click(screen.getByLabelText('Punto de venta'));
    await user.click(screen.getByText('Todas las tiendas'));

    // A capability lost, not a display preference: with no shop the availability label can never say
    // the shop is out of stock, so the loop never pivots.
    const warning = await screen.findByTestId('agent-all-shops-warning');
    expect(warning).toHaveTextContent(/no ofrecer. alternativas/i);
  });

  it('should warn and restart the thread when the scope changes', async () => {
    const user = userEvent.setup();
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true);

    renderPage();
    await ready();

    await ask(user, 'busco un anillo');
    await waitFor(() => expect(screen.getAllByTestId('agent-exchange')).toHaveLength(1));

    await user.click(screen.getByLabelText('Punto de venta'));
    await user.click(screen.getByText('Tienda Ciutadella'));

    // Warned before, and the evidence cleared: it was gathered in another shop, with its prices, its
    // stock and its assortment.
    expect(confirm).toHaveBeenCalled();
    await waitFor(() => expect(screen.queryAllByTestId('agent-exchange')).toHaveLength(0));

    confirm.mockRestore();
  });

  it('should keep the thread when the operator declines the restart', async () => {
    const user = userEvent.setup();
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);

    renderPage();
    await ready();

    await ask(user, 'busco un anillo');
    await waitFor(() => expect(screen.getAllByTestId('agent-exchange')).toHaveLength(1));

    await user.click(screen.getByLabelText('Punto de venta'));
    await user.click(screen.getByText('Tienda Ciutadella'));

    expect(screen.getAllByTestId('agent-exchange')).toHaveLength(1);
    expect(screen.getByLabelText('Punto de venta')).toHaveTextContent('Tienda Mahón');

    confirm.mockRestore();
  });
});

describe('the session cost', () => {
  it('should accumulate rather than replacing when a new answer arrives', async () => {
    const user = userEvent.setup();
    renderPage();
    await ready();

    await ask(user, 'busco un anillo');
    await waitFor(() => expect(screen.getByTestId('agent-session-cost')).toBeInTheDocument());

    const first = screen.getByTestId('agent-session-cost').textContent!;
    expect(first).toMatch(/1 pregunta/);
    expect(first).toMatch(/13k tokens/);

    await ask(user, 'y en dorado');

    await waitFor(() =>
      expect(screen.getByTestId('agent-session-cost')).toHaveTextContent(/2 preguntas/),
    );

    // One turn's cost says nothing about a conversation's, and it is the conversation the quota is
    // spent on.
    expect(screen.getByTestId('agent-session-cost')).toHaveTextContent(/26k tokens/);
  });

  it('should show nothing before the first question', async () => {
    renderPage();
    await ready();

    // A row of zeros reads as a rendering fault.
    expect(screen.queryByTestId('agent-session-cost')).not.toBeInTheDocument();
  });
});

describe('failures of a turn', () => {
  it('should state a throttle as a wait rather than as an outage', async () => {
    const user = userEvent.setup();
    vi.mocked(agentAssistService.answer).mockResolvedValue({ kind: 'rate-limited' });

    renderPage();
    await ready();

    await ask(user, 'busco un anillo');

    const failure = await screen.findByTestId('agent-exchange-failure');
    expect(failure).toHaveTextContent(/espera un momento/i);
    // The thread survives it: the question stays, and the next turn can still be asked.
    expect(screen.getByText(/busco un anillo/)).toBeInTheDocument();
  });

  it('should carry the cap message through when the backend refuses the transcript', async () => {
    const user = userEvent.setup();
    vi.mocked(agentAssistService.answer).mockResolvedValue({
      kind: 'invalid',
      errors: ['La conversación no puede pasar de 4000 caracteres en total, sumando todos los turnos.'],
    });

    renderPage();
    await ready();

    await ask(user, 'busco un anillo');

    expect(await screen.findByTestId('agent-exchange-failure')).toHaveTextContent(/4000/);
  });
});

describe('the gate on the panel itself', () => {
  it('should state the reason and close the composer when the agent is off', async () => {
    vi.mocked(aiSearchService.getAvailability).mockResolvedValue({
      kind: 'ok',
      availability: {
        pointOfSaleId: POS_ONE,
        semanticSearchAvailable: true,
        assistedAnswerAvailable: true,
        agentAvailable: false,
        agentUnavailableReason: 'switched_off',
      },
    });

    renderPage();

    const notice = await screen.findByTestId('agent-unavailable');
    expect(notice).toHaveTextContent(/desactivado/i);
    await waitFor(() =>
      expect(screen.getByLabelText('Escribe tu pregunta al agente')).toBeDisabled(),
    );
  });

  it('should stay usable when the probe cannot answer', async () => {
    vi.mocked(aiSearchService.getAvailability).mockResolvedValue({ kind: 'unknown' });

    renderPage();
    await ready();

    // Failing the probe must not close a door that may well work.
    expect(screen.queryByTestId('agent-unavailable')).not.toBeInTheDocument();
  });
});

describe('selling from the thread', () => {
  it('should report the selection and hand the piece to the existing sale path', async () => {
    const user = userEvent.setup();
    renderPage();
    await ready();

    await ask(user, 'busco un anillo');
    await waitFor(() => expect(screen.getByTestId('agent-answer-block')).toBeInTheDocument());

    await user.click(screen.getByRole('button', { name: /seleccionar para venta/i }));

    // Attributed to the block the row belongs to, which is the search the operator was looking at.
    expect(aiSearchService.reportSelection).toHaveBeenCalledWith('ev-1', 'p-ARO-M');
    expect(navigate).toHaveBeenCalledWith('/sales/new', {
      state: { productId: 'p-ARO-M', searchEventId: 'ev-1' },
    });
  });
});

describe('the way back to the deterministic panel', () => {
  it('should link to the assisted panel so the same question can be compared', async () => {
    renderPage();
    await ready();

    expect(screen.getByRole('link', { name: /panel directo/i })).toHaveAttribute(
      'href',
      '/sales/new/assisted',
    );
  });
});
