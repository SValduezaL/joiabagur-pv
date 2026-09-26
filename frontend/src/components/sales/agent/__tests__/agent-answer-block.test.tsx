/**
 * One turn's answer block (EP15 / C42)
 *
 * **Ordered by measured frequency, and the tests follow that order.** One answer in five carries no
 * piece at all (19.6 %, identical on both arms), and of those, fourteen of twenty are a clarification
 * or a polite refusal — normal outcomes of a conversation rather than a search that found nothing.
 * Only six of 102 requests are «I looked and found nothing». Citations appear in 7.8 % of answers,
 * warnings in 3.9 %, and the incompleteness ribbon serves 2.0 %.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

import type { AgentAssistGroup, AgentAssistResponse } from '@/types/ai-agent.types';
import type { AssistedSearchResult } from '@/types/ai-search.types';
import { AgentAnswerBlock, searchedAndFoundNothing } from '../agent-answer-block';

function member(sku: string, overrides: Partial<AssistedSearchResult> = {}): AssistedSearchResult {
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
    ...overrides,
  } as AssistedSearchResult;
}

function group(
  origin: AgentAssistGroup['origin'],
  skus: string[],
  overrides: Partial<AgentAssistGroup> = {},
): AgentAssistGroup {
  return {
    familyId: null,
    familyLabel: null,
    origin,
    members: skus.map((sku) => member(sku)),
    ...overrides,
  };
}

function answer(overrides: Partial<AgentAssistResponse> = {}): AgentAssistResponse {
  return {
    groups: [],
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
    candidatesReturned: 0,
    survivedHydration: 0,
    ...overrides,
  };
}

function renderBlock(response: AgentAssistResponse, onSelect = vi.fn(), onOpenCard = vi.fn()) {
  render(
    <BrowserRouter>
      <AgentAnswerBlock
        answer={response}
        onSelect={onSelect}
        onOpenCard={onOpenCard}
        pointOfSaleName="Tienda Mahón"
      />
    </BrowserRouter>,
  );
  return { onSelect, onOpenCard };
}

/* ---------------------------------------------------------------- 19.6 %: no pieces at all */

describe('an answer with no pieces', () => {
  it('should render an answer with prose and no pieces', () => {
    // A knowledge answer: prose, citations, no rows. One in five answers looks like this, so none of
    // the empty-result phrases may appear.
    renderBlock(
      answer({
        groups: [],
        pitch: 'La plata de ley se limpia con un paño seco y se guarda aparte.',
        citations: [
          {
            citationId: 'material-plata#cuidados',
            documentTitle: 'Plata',
            sectionTitle: 'Cuidados',
            docType: 'material',
            claimScope: 'general',
            snippet: 'Evitar el agua.',
          },
        ],
      }),
    );

    expect(screen.getByText(/se limpia con un pa/i)).toBeInTheDocument();
    expect(screen.getByTestId('assist-citation')).toBeInTheDocument();
    expect(screen.queryByTestId('agent-searched-nothing')).not.toBeInTheDocument();
    expect(screen.queryByTestId('agent-answer-group')).not.toBeInTheDocument();
    expect(screen.queryByText(/sin resultados/i)).not.toBeInTheDocument();
  });

  it('should render only the question when the agent asked for a clarification', () => {
    renderBlock(
      answer({
        groups: [],
        pitch: '',
        pitchStatus: 'not_generated',
        clarificationQuestion: 'Para que ocasion es el regalo?',
        stopReason: 'aclaracion',
        toolCallsUsed: 1,
      }),
    );

    expect(screen.getByText(/para que ocasion/i)).toBeInTheDocument();
    // Not an empty search: the conversation is working, it needs one more thing.
    expect(screen.queryByTestId('agent-searched-nothing')).not.toBeInTheDocument();
  });

  it('should state having searched and found nothing, distinguishably from the other two', () => {
    const searched = answer({
      groups: [],
      pitch: '',
      pitchStatus: 'not_generated',
      abstained: true,
      toolCallsUsed: 2,
      stopReason: 'sin_mas_herramientas',
    });

    renderBlock(searched);

    expect(screen.getByTestId('agent-searched-nothing')).toHaveTextContent(/no encontr/i);
  });

  it('should tell the three no-piece states apart', () => {
    const knowledge = answer({ groups: [], pitch: 'La plata se limpia con un paño.', toolCallsUsed: 1 });
    const clarification = answer({
      groups: [],
      clarificationQuestion: 'Para quien es?',
      stopReason: 'aclaracion',
      toolCallsUsed: 1,
    });
    // Abstained and no prose: there was nothing to write an argument about.
    const nothing = answer({
      groups: [],
      pitch: '',
      pitchStatus: 'not_generated',
      abstained: true,
      toolCallsUsed: 2,
    });

    // Only the third is an empty search. The measurement is what forces the distinction: fourteen of
    // the twenty no-piece answers per arm are one of the first two.
    expect(searchedAndFoundNothing(knowledge)).toBe(false);
    expect(searchedAndFoundNothing(clarification)).toBe(false);
    expect(searchedAndFoundNothing(nothing)).toBe(true);
  });

  it('should not claim an empty search when no loop ran at all', () => {
    // A deployment with no agent credential: zero iterations, nothing was searched, so saying the
    // catalogue came back empty would blame the catalogue for a missing configuration.
    const noClient = answer({
      groups: [],
      pitch: '',
      pitchStatus: 'not_generated',
      stopReason: 'sin_cliente',
      iterations: 0,
      toolCallsUsed: 0,
      partial: true,
    });

    expect(searchedAndFoundNothing(noClient)).toBe(false);
  });

  it('should not claim an empty search on a refusal', () => {
    const refused = answer({
      groups: [],
      stopReason: 'rechazado',
      toolCallsUsed: 1,
      warnings: ['query_out_of_domain'],
    });

    expect(searchedAndFoundNothing(refused)).toBe(false);
  });
});

/* ---------------------------------------------------------- the majority: rows with two labels */

describe('the groups and their provenance', () => {
  it('should label a substitutes group as alternatives', () => {
    renderBlock(
      answer({ groups: [group('catalogo', ['ARO-M']), group('sustitutos', ['SUB-1'])] }),
    );

    const groups = screen.getAllByTestId('agent-answer-group');
    expect(groups).toHaveLength(2);
    expect(groups[0]).toHaveTextContent('Coincidencias');
    expect(groups[1]).toHaveTextContent('Alternativas');
  });

  it('should state the matches before the substitutes whatever order they arrive in', () => {
    // The label comes from the provenance and never from the position, so a service that returned
    // the substitutes first must still render the matches first.
    renderBlock(
      answer({ groups: [group('sustitutos', ['SUB-1']), group('catalogo', ['ARO-M'])] }),
    );

    const groups = screen.getAllByTestId('agent-answer-group');
    expect(groups[0]).toHaveAttribute('data-origin', 'catalogo');
    expect(groups[1]).toHaveAttribute('data-origin', 'sustitutos');
  });

  it('should never present a substitute as a match', () => {
    renderBlock(answer({ groups: [group('sustitutos', ['SUB-1'])] }));

    const only = screen.getByTestId('agent-answer-group');
    expect(only).toHaveTextContent('Alternativas');
    expect(only).not.toHaveTextContent('Coincidencias');
  });

  /**
   * **A refutation of the delta spec, recorded here rather than implemented differently in silence.**
   *
   * The scenario as written reads «the sale is disabled when stock is unknown». The row this panel
   * reuses — and which this change promises not to modify — does not do that, and C40's own test for
   * it pins the opposite: with `hasStock === null` it replaces the stock line with «Selecciona una
   * tienda para ver existencias» and disables **opening the sale card**, while selecting for sale
   * stays available. The sibling panel has behaved that way since C40.
   *
   * That behaviour is also the right one, which is why it is not worth a diff to the row: the
   * every-shop scope exists to find out *where* a piece is, and the manual sale flow it hands over to
   * requires a shop of its own and validates stock there. Disabling selection would make the scope
   * unable to lead anywhere. What must not happen — presenting unknown stock as «none left» — is what
   * the row's three-state rendering already prevents.
   *
   * The change's spec is amended to state what the reused row does; the live spec is untouched.
   */
  it('should say a shop is needed rather than asserting no stock when stock is unknown', () => {
    renderBlock(
      answer({
        groups: [
          {
            familyId: null,
            familyLabel: null,
            origin: 'catalogo',
            members: [member('ARO-M', { hasStock: null, quantityAtPointOfSale: null })],
          },
        ],
      }),
    );

    expect(screen.getByTestId('stock-needs-a-shop')).toBeInTheDocument();
    expect(screen.queryByText(/sin existencias/i)).not.toBeInTheDocument();
    // What the row actually disables: opening the card, which reports one shop's stock.
    expect(screen.getByTestId('assisted-search-open-card')).toBeDisabled();
  });

  it('should hydrate a substitute row with its price like any other', () => {
    renderBlock(answer({ groups: [group('sustitutos', ['SUB-1'])] }));

    // A substitute is a piece of this catalogue like any other: showing one without a price is what
    // treating it differently leads to.
    expect(screen.getByText(/39,90/)).toBeInTheDocument();
  });
});

/* ---------------------------------------------------------------- the status strip and the trace */

describe('the status strip', () => {
  const TEN = [
    'sin_mas_herramientas',
    'presupuesto_iteraciones',
    'presupuesto_tools',
    'presupuesto_tokens',
    'presupuesto_contexto',
    'presupuesto_reloj',
    'aclaracion',
    'rechazado',
    'sin_cliente',
    'fallo_proveedor',
  ];

  it('should state each of the ten stop reasons at block level', () => {
    for (const stopReason of TEN) {
      const { unmount } = render(
        <BrowserRouter>
          <AgentAnswerBlock answer={answer({ stopReason })} onSelect={vi.fn()} />
        </BrowserRouter>,
      );

      const strip = screen.getByTestId('agent-stop-reason');
      expect(strip.textContent).not.toBe('');
      expect(strip.textContent).not.toMatch(/no reconoce/i);

      unmount();
    }
  });

  it('should show a neutral statement at block level for a stop reason it does not know', () => {
    renderBlock(answer({ stopReason: 'un_valor_nuevo' }));

    expect(screen.getByTestId('agent-stop-reason')).toHaveTextContent(/no reconoce/i);
  });

  it('should show the turns and the consultations beside the reason', () => {
    renderBlock(answer({ iterations: 3, toolCallsUsed: 6 }));

    expect(screen.getByText(/3 vueltas/)).toBeInTheDocument();
    expect(screen.getByText(/6 consultas/)).toBeInTheDocument();
  });
});

describe('the trace', () => {
  it('should be reachable from the open block and list the iterations', async () => {
    const { default: userEvent } = await import('@testing-library/user-event');
    const user = userEvent.setup();

    renderBlock(
      answer({
        trace: [
          {
            iteration: 1,
            tools: [{ tool: 'buscar_catalogo', ok: true }],
            promptTokens: 3200,
            completionTokens: 60,
            totalTokens: 3260,
            elapsedMs: 1420.5,
          },
          {
            iteration: 2,
            tools: [
              { tool: 'consultar_disponibilidad', ok: true },
              { tool: 'buscar_sustitutos', ok: false, cause: 'presupuesto_agotado' },
            ],
            promptTokens: 4100,
            completionTokens: 80,
            totalTokens: 4180,
            elapsedMs: 1980,
          },
        ],
      }),
    );

    // Collapsed by default, with the number of turns visible: the operator's job is to sell, and the
    // ladder is what they open when the answer surprises them.
    const trigger = screen.getByText('Cómo lo ha averiguado');
    expect(screen.getByTestId('agent-trace')).toHaveTextContent('2 vueltas');

    await user.click(trigger);

    expect(screen.getAllByTestId('agent-trace-step')).toHaveLength(2);
    expect(screen.getByText('buscar_sustitutos')).toBeInTheDocument();
    expect(screen.getByText(/sin presupuesto/)).toBeInTheDocument();
    // The cost of each step: tokens and milliseconds, never euros. Matched over the element's whole
    // text because JSX interpolation splits it into several text nodes.
    // The thousands separator is left flexible on purpose: `toLocaleString('es-ES')` groups with a
    // dot in a browser and not under this runner's minimal ICU data, and pinning the separator would
    // make the test assert the runner's locale support instead of the component.
    const steps = screen.getAllByTestId('agent-trace-step');
    expect(steps[0].textContent).toMatch(/3\.?260 tokens/);
    expect(steps[0].textContent).toMatch(/1\.?421 ms/);
  });

  it('should show no tool argument and no observation content', () => {
    renderBlock(
      answer({
        trace: [
          {
            iteration: 1,
            tools: [{ tool: 'buscar_catalogo', ok: true }],
            promptTokens: 10,
            completionTokens: 1,
            totalTokens: 11,
            elapsedMs: 5,
          },
        ],
      }),
    );

    const trace = screen.getByTestId('agent-trace');

    // Excluded by the contract, so there is nothing to render even if somebody tried: the arguments
    // are the operator's question as the model reformulated it.
    expect(trace.textContent).not.toMatch(/consulta"|"sku"|\{/);
  });

  it('should render nothing when no loop ran', () => {
    renderBlock(answer({ trace: [], iterations: 0, stopReason: 'sin_cliente' }));

    expect(screen.queryByTestId('agent-trace')).not.toBeInTheDocument();
  });
});

/* ------------------------------------------------- when the service did not answer at all */

describe('an answer the AI service did not serve', () => {
  /**
   * **Found by the manual check of C42 and by nothing else.** With the every-shop scope against a
   * stale container the gateway degraded, and the block claimed «el agente terminó por un motivo que
   * esta pantalla no reconoce» over «0 vueltas · 0 consultas» — blaming the screen for a service that
   * simply did not answer, and describing a loop that never ran.
   */
  const degraded = () =>
    answer({
      groups: [],
      pitch: null,
      pitchStatus: 'ai_unavailable',
      aiAvailable: false,
      degradedReason: 'ai_unavailable',
      stopReason: '',
      iterations: 0,
      toolCallsUsed: 0,
      trace: [],
    });

  it('should state the degradation instead of claiming an unrecognised stop reason', () => {
    renderBlock(degraded());

    expect(screen.getByTestId('agent-degraded')).toHaveTextContent(/no está disponible/i);
    expect(screen.queryByTestId('agent-stop-reason')).not.toBeInTheDocument();
    expect(screen.queryByText(/no reconoce/i)).not.toBeInTheDocument();
  });

  it('should not report turns and consultations for a loop that never ran', () => {
    renderBlock(degraded());

    expect(screen.queryByText(/0 vueltas/)).not.toBeInTheDocument();
    expect(screen.queryByText(/0 consultas/)).not.toBeInTheDocument();
  });

  it('should not claim the rows come from the catalogue when there are no rows', () => {
    renderBlock(degraded());

    // C36's block words `ai_unavailable` for the sale card it was written for — «Lo que ves viene del
    // catálogo: el precio, las unidades y las variantes son reales» — which is false of a degraded
    // agent turn, because there is nothing to see.
    expect(screen.queryByText(/viene del cat/i)).not.toBeInTheDocument();
    expect(screen.queryByTestId('agent-answer-group')).not.toBeInTheDocument();
  });

  it('should not word it as an empty search either', () => {
    // Nothing was searched: the loop never started. Saying the catalogue came back empty would blame
    // the catalogue for a service that did not answer.
    expect(searchedAndFoundNothing(degraded())).toBe(false);
    renderBlock(degraded());
    expect(screen.queryByTestId('agent-searched-nothing')).not.toBeInTheDocument();
  });

  it('should name each degradation the backend can report', () => {
    for (const reason of ['switched_off', 'credential_rejected', 'not_implemented', 'ai_unavailable']) {
      const { unmount } = render(
        <BrowserRouter>
          <AgentAnswerBlock
            answer={{ ...degraded(), degradedReason: reason }}
            onSelect={vi.fn()}
          />
        </BrowserRouter>,
      );

      expect(screen.getByTestId('agent-degraded').textContent).not.toMatch(/no reconoce/i);
      unmount();
    }
  });

  it('should still show the strip when the service answered with a degradation of its own', () => {
    // The other kind: the service DID answer and reported that its provider fell. That is a stop
    // reason, it has copy of its own, and the counters mean something.
    renderBlock(
      answer({
        groups: [],
        pitch: '',
        pitchStatus: 'not_generated',
        aiAvailable: true,
        stopReason: 'fallo_proveedor',
        partial: true,
        iterations: 1,
        toolCallsUsed: 0,
      }),
    );

    expect(screen.getByTestId('agent-stop-reason')).toHaveTextContent(/proveedor/i);
    expect(screen.queryByTestId('agent-degraded')).not.toBeInTheDocument();
  });
});

/* ---------------------------------------------------------------- 2.0 %: the cut answer, last */

describe('an incomplete answer', () => {
  it('should tell a budget-cut answer from a complete one', () => {
    renderBlock(answer({ partial: true, stopReason: 'presupuesto_tools' }));

    const ribbon = screen.getByTestId('agent-partial-ribbon');
    expect(ribbon).toHaveTextContent(/incompleta/i);
    // And it names which budget ran out, because «incompleta» alone explains nothing.
    expect(ribbon).toHaveTextContent(/consultas al cat/i);
    // No alarm colour: the evidence gathered before the cut is still useful.
    expect(ribbon.className).not.toMatch(/destructive/);
  });

  it('should carry no such statement when the answer was not cut short', () => {
    renderBlock(answer({ partial: false, stopReason: 'sin_mas_herramientas' }));

    expect(screen.queryByTestId('agent-partial-ribbon')).not.toBeInTheDocument();
  });

  it('should carry no budget ribbon when partial came from a provider failure', () => {
    // `partial` is true here too, but no budget ran out: the ribbon would name a cause that is not
    // this one, and the argument's own block already states the degradation.
    renderBlock(answer({ partial: true, stopReason: 'fallo_proveedor' }));

    expect(screen.queryByTestId('agent-partial-ribbon')).not.toBeInTheDocument();
  });
});

/* ---------------------------------------------------------------- 3.9 %: the warnings */

describe('the warnings', () => {
  it('should state a warning about the conversation when one arrives', () => {
    renderBlock(answer({ warnings: ['query_out_of_domain'] }));

    expect(screen.getByTestId('agent-warnings')).toHaveTextContent(/no es de este negocio/i);
  });

  it('should render nothing at all when there is no warning', () => {
    renderBlock(answer({ warnings: [] }));

    expect(screen.queryByTestId('agent-warnings')).not.toBeInTheDocument();
  });
});

/* ---------------------------------------------------------------- selling from the block */

describe('selling from the block', () => {
  it('should hand the picked piece to the existing sale path', async () => {
    const onSelect = vi.fn();
    const { default: userEvent } = await import('@testing-library/user-event');
    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <AgentAnswerBlock
          answer={answer({ groups: [group('catalogo', ['ARO-M'])] })}
          onSelect={onSelect}
          pointOfSaleName="Tienda Mahón"
        />
      </BrowserRouter>,
    );

    await user.click(screen.getByRole('button', { name: /seleccionar para venta/i }));

    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect.mock.calls[0][0].sku).toBe('ARO-M');
  });
});
