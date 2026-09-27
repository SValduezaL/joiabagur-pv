/**
 * The assisted answer's funnel (C40, group 13.2).
 *
 * This closes the third of the three infractions the exploration found: `usage`, `aiMs`, `totalMs`
 * and `model` were computed, paid for and returned, and the screen dropped them.
 *
 * What the tests guard is mostly what the panel must **not** say. A cost panel is exactly where a
 * euro figure gets added by someone being helpful, and exactly where a query text gets added by
 * someone debugging — and both are prohibited for reasons that are not obvious from the markup.
 */

import { describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { FreeQueryFunnel } from '../free-query-funnel';
import { FreeQueryAnswer } from '../free-query-answer';
import type { FreeQuerySearchResponse } from '@/types/ai-search.types';

const QUERY_TEXT = 'algo para mi suegra que no sea cursi';
const PITCH_TEXT = 'La plata se empaña con el aire y se limpia con un paño suave.';

function response(overrides: Partial<FreeQuerySearchResponse> = {}): FreeQuerySearchResponse {
  return {
    groups: [],
    pitch: PITCH_TEXT,
    pitchStatus: 'generated',
    citations: [],
    warnings: [],
    clarificationQuestion: null,
    intent: 'in_domain',
    abstained: false,
    aiAvailable: true,
    degradedReason: null,
    usage: {
      model: 'openai/gpt-4o-mini',
      promptTokens: 3412,
      completionTokens: 128,
      totalTokens: 3540,
      promptVersion: 'assist/v5',
      aiMs: 3404,
      totalMs: 3421,
    },
    searchEventId: 'event-1',
    pointOfSaleId: 'pos-1',
    candidatesReturned: 15,
    survivedHydration: 7,
    traceId: 'trace-1',
    ...overrides,
  };
}

async function expand(overrides: Partial<FreeQuerySearchResponse> = {}, displayed = 3) {
  const user = userEvent.setup();
  render(<FreeQueryFunnel response={response(overrides)} displayed={displayed} />);
  await user.click(screen.getByRole('button', { name: /embudo/i }));
  return screen.getByTestId('assisted-answer-funnel-body');
}

describe('FreeQueryFunnel', () => {
  it('should be collapsed by default', async () => {
    render(<FreeQueryFunnel response={response()} displayed={3} />);

    // A diagnostic panel on a shop-floor screen. An administrator serving a customer is an
    // operator with an extra permission, not an auditor.
    expect(screen.queryByTestId('assisted-answer-funnel-body')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /embudo/i })).toBeInTheDocument();
  });

  it('should split the elapsed time in the assisted funnel', async () => {
    const body = await expand();

    // **Two figures and never one.** It is the only way to tell «the provider was slow» from «we
    // were slow», and those end in opposite work: a vendor conversation against a profiler.
    expect(within(body).getByTestId('funnel-ai-ms')).toHaveTextContent('3.4 s');
    expect(within(body).getByTestId('funnel-total-ms')).toHaveTextContent('3.4 s');
    expect(within(body).getByTestId('funnel-model')).toHaveTextContent('openai/gpt-4o-mini');
    expect(within(body).getByTestId('funnel-tokens')).toHaveTextContent('3412');
    expect(within(body).getByTestId('funnel-tokens')).toHaveTextContent('128');
  });

  it('should report the two times apart even when they differ by an order of magnitude', async () => {
    const body = await expand({
      usage: { ...response().usage!, aiMs: 120, totalMs: 4800 },
    });

    expect(within(body).getByTestId('funnel-ai-ms')).toHaveTextContent('120 ms');
    expect(within(body).getByTestId('funnel-total-ms')).toHaveTextContent('4.8 s');
  });

  it('should show no monetary amount in the funnel', async () => {
    const body = await expand();

    // Tokens and the model are the INPUTS of a cost, and they are shown. A tariff written into a
    // screen is wrong the day the provider moves it, and the model named here is only the last
    // stage of a multi-stage route — so multiplying it would be false, and inviting the
    // multiplication would spread the falsehood.
    expect(body.textContent).not.toMatch(/€|EUR|eur\b|\$|coste|precio/i);
  });

  it('should show neither the query nor the argument in the funnel', async () => {
    const body = await expand();

    // The funnel is a cost panel, not a transcript. Both are already excluded from the logs by
    // the same rule, and a diagnostic panel is not a loophole in it.
    expect(body.textContent).not.toContain(QUERY_TEXT);
    expect(body.textContent).not.toContain(PITCH_TEXT);
  });

  it('should name the cause when the path degraded', async () => {
    const body = await expand({
      aiAvailable: false,
      degradedReason: 'credential_rejected',
      usage: null,
    });

    // The operator's message collapses several causes because their next move is the same. The
    // administrator's does not: a credential is not an outage and not an unindexed piece.
    expect(within(body).getByTestId('funnel-degraded-reason')).toHaveTextContent(
      /credencial rechazada/i,
    );
  });

  it('should say a global search was not recorded rather than look like a telemetry failure', async () => {
    const body = await expand({ searchEventId: null, pointOfSaleId: null });

    expect(within(body).getByTestId('funnel-not-recorded')).toHaveTextContent(
      /todas las tiendas/i,
    );
  });

  it('should still show the counters when the response carries no usage', async () => {
    // `usage` is built only for an administrator, so its absence here is a degraded response and
    // not a permission problem. The counters are in every response and must survive it.
    const body = await expand({ usage: null });

    expect(body).toHaveTextContent('Candidatos: 15');
    expect(body).toHaveTextContent('Supervivientes: 7');
    expect(within(body).queryByTestId('funnel-ai-ms')).not.toBeInTheDocument();
  });
});

describe('FreeQueryAnswer — who sees the funnel', () => {
  it('should render no funnel for a non-administrator', async () => {
    render(
      <FreeQueryAnswer
        response={response()}
        onSelect={vi.fn()}
        onOpenCard={vi.fn()}
        isAdmin={false}
      />,
    );

    expect(screen.queryByTestId('assisted-answer-funnel')).not.toBeInTheDocument();
  });

  it('should render the funnel for an administrator', async () => {
    render(
      <FreeQueryAnswer
        response={response()}
        onSelect={vi.fn()}
        onOpenCard={vi.fn()}
        isAdmin
      />,
    );

    expect(screen.getByTestId('assisted-answer-funnel')).toBeInTheDocument();
    // Still collapsed: being an administrator opens the door, it does not walk through it.
    expect(screen.queryByTestId('assisted-answer-funnel-body')).not.toBeInTheDocument();
  });

  it('should default to hiding the funnel when the caller says nothing about the role', async () => {
    // A caller that forgets the prop must not leak a diagnostic panel to an operator.
    render(<FreeQueryAnswer response={response()} onSelect={vi.fn()} onOpenCard={vi.fn()} />);

    expect(screen.queryByTestId('assisted-answer-funnel')).not.toBeInTheDocument();
  });
});
