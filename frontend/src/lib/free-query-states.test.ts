/**
 * The resolution of the sixteen states (C40).
 *
 * These are the assertions that matter most in the whole change, and they are made here rather
 * than through the DOM on purpose: the three states the panel would paint wrongly by default are
 * wrong in the **classification**, not in the markup. A test that rendered the component and
 * looked for a string would pass the day somebody fixed the string and broke the branch.
 */

import { describe, it, expect } from 'vitest';

import {
  resolveFreeQueryState,
  isEmptyResult,
  showsCitationBlock,
  showsNoVerifiableSource,
} from './free-query-states';
import type { FreeQuerySearchResponse } from '@/types/ai-search.types';

function response(
  overrides: Partial<FreeQuerySearchResponse> = {},
): FreeQuerySearchResponse {
  return {
    groups: [],
    pitch: null,
    pitchStatus: 'generated',
    citations: [],
    warnings: [],
    clarificationQuestion: null,
    intent: 'in_domain',
    abstained: false,
    aiAvailable: true,
    degradedReason: null,
    usage: null,
    searchEventId: null,
    pointOfSaleId: 'pos-1',
    candidatesReturned: 0,
    survivedHydration: 0,
    traceId: 'trace-1',
    ...overrides,
  };
}

const group = { familyId: 'fam-1', familyLabel: 'Aro fino', members: [] as never[] };
const citation = {
  citationId: 'plata#cuidados',
  documentTitle: 'Plata',
  sectionTitle: 'Cuidados',
  docType: 'material',
  claimScope: 'general',
  snippet: 'Evitar el agua.',
  score: 0.7,
} as never;

describe('resolveFreeQueryState — the router cuts first', () => {
  it('should resolve an out-of-domain refusal', () => {
    const state = resolveFreeQueryState(
      response({ warnings: ['query_out_of_domain'], intent: 'out_of_domain' }),
    );

    expect(state.kind).toBe('refused-out-of-domain');
  });

  it('should resolve a not-in-catalogue refusal as a different state', () => {
    const state = resolveFreeQueryState(
      response({ warnings: ['query_not_in_catalogue'], intent: 'not_in_catalogue' }),
    );

    // Two codes, two states, two sentences. The service went to the trouble of emitting two;
    // collapsing them here would throw that away at the last step.
    expect(state.kind).toBe('refused-not-in-catalogue');
  });

  it('should resolve a clarification, verbatim', () => {
    const state = resolveFreeQueryState(
      response({ clarificationQuestion: '¿Para regalo o para ti?' }),
    );

    expect(state).toEqual({ kind: 'clarification', question: '¿Para regalo o para ti?' });
  });

  it('should let a refusal win over anything the shape would otherwise suggest', () => {
    // The router cuts BEFORE retrieval, so a refusal cannot be overtaken by a later condition.
    const state = resolveFreeQueryState(
      response({ warnings: ['query_out_of_domain'], abstained: true, groups: [group] }),
    );

    expect(state.kind).toBe('refused-out-of-domain');
  });
});

describe('resolveFreeQueryState — the two states with no route', () => {
  it('should tell a contradictory classifier from one that did not run', () => {
    const contradictory = resolveFreeQueryState(response({ intent: 'in_domain' }));
    const down = resolveFreeQueryState(response({ intent: 'unclassified' }));

    // **Only `intent` separates them**, and they need opposite copy: one invites a rephrase,
    // the other must not, because the operator did nothing wrong.
    expect(contradictory.kind).toBe('no-route-contradictory');
    expect(down.kind).toBe('no-route-classifier-down');
    expect(contradictory.kind).not.toBe(down.kind);
  });

  it('should not read a withheld argument as a routing failure', () => {
    // Pieces came back and the gate withheld the text. That is state 12, not 4: the router did
    // its job, and asking the operator to rephrase would be nonsense.
    const state = resolveFreeQueryState(
      response({ groups: [group], intent: 'in_domain', pitchStatus: 'withheld_by_ai' }),
    );

    expect(state.kind).toBe('answered-without-prose');
  });
});

describe('resolveFreeQueryState — what retrieval decided', () => {
  it('should resolve an abstention', () => {
    expect(resolveFreeQueryState(response({ abstained: true })).kind).toBe('abstained');
  });

  it('should tell a narrow filter from an unanswerable query', () => {
    const narrow = resolveFreeQueryState(
      response({ warnings: ['filters_too_narrow'], groups: [group], pitch: 'Estas encajan.' }),
    );
    const unanswerable = resolveFreeQueryState(response({ abstained: true }));

    // «Hay piezas que encajan pero ninguna pasa los filtros» presupposes the description is
    // answerable. Over an unanswerable query that sentence would simply be false.
    expect(narrow.kind).toBe('filters-too-narrow');
    expect(unanswerable.kind).toBe('abstained');
  });

  it('should let an abstention win over a narrow filter', () => {
    // The abstention is decided first, on the unfiltered profile: if nothing matches the
    // description at all, blaming the filter would be the false sentence.
    const state = resolveFreeQueryState(
      response({ abstained: true, warnings: ['filters_too_narrow'] }),
    );

    expect(state.kind).toBe('abstained');
  });
});

describe('resolveFreeQueryState — .NET decided', () => {
  it('should resolve a degraded answer with its reason', () => {
    const state = resolveFreeQueryState(
      response({ aiAvailable: false, degradedReason: 'switched_off' }),
    );

    expect(state).toEqual({ kind: 'degraded', reason: 'switched_off' });
  });

  it('should let degradation win over everything, because nothing else was said', () => {
    const state = resolveFreeQueryState(
      response({ aiAvailable: false, warnings: ['query_out_of_domain'], abstained: true }),
    );

    expect(state.kind).toBe('degraded');
  });
});

describe('isEmptyResult — the state the panel gets wrong by default', () => {
  it('should not announce an empty result set on the knowledge route', () => {
    // **State 9.** Zero pieces and a correct answer: the corpus was asked a question and
    // answered it. The five branches of emptiness of the C16 panel would write «Sin resultados»
    // directly above it.
    const knowledge = response({
      groups: [],
      citations: [citation],
      pitch: 'La plata se empaña con el aire y se limpia con un paño suave.',
    });

    expect(isEmptyResult(knowledge)).toBe(false);
    expect(resolveFreeQueryState(knowledge).kind).toBe('answered');
  });

  it('should treat prose with no pieces and no citations as an answer too', () => {
    expect(isEmptyResult(response({ pitch: 'Algo que sí se puede decir.' }))).toBe(false);
  });

  it('should call it empty only when there is nothing at all to read', () => {
    expect(isEmptyResult(response())).toBe(true);
  });
});

describe('the citation block', () => {
  it('should render no citation when there is no argument', () => {
    // The service KEEPS the citations when it withholds the argument, on purpose: a degraded
    // response must not be poorer than the structured layer's own, which is what keeps the
    // ablation comparable for the harness. That serves the harness. For an operator a citation
    // with no claim attached attributes nothing.
    const withheld = response({
      groups: [group],
      citations: [citation],
      pitch: null,
      pitchStatus: 'withheld_by_ai',
    });

    expect(showsCitationBlock(withheld)).toBe(false);
  });

  it('should render citations when there is an argument they support', () => {
    expect(
      showsCitationBlock(response({ pitch: 'Se puede mojar.', citations: [citation] })),
    ).toBe(true);
  });
});

describe('the discreet line about a source nobody can check', () => {
  it('should say it when the gate withdrew every citation', () => {
    const withdrawn = response({ pitch: 'Se puede mojar.', citations: [], groups: [] });

    expect(showsNoVerifiableSource(withdrawn)).toBe(true);
  });

  it('should not say it on the catalogue route, where citing nothing is correct', () => {
    // That route is answered from pieces and its own task tells the model to return no
    // citations, so reporting a gap there would invent one.
    const catalogue = response({ pitch: 'Estas tres son sobrias.', groups: [group], citations: [] });

    expect(showsNoVerifiableSource(catalogue)).toBe(false);
  });

  it('should not say it when the warning already says the corpus covers nothing', () => {
    const uncovered = response({
      pitch: 'Eso no está en la documentación de la casa.',
      warnings: ['knowledge_not_covered'],
    });

    // Two lines about the same absence is one too many, and the warning is the more useful of
    // the two.
    expect(showsNoVerifiableSource(uncovered)).toBe(false);
  });

  it('should not say it when there are citations', () => {
    expect(
      showsNoVerifiableSource(response({ pitch: 'Se puede mojar.', citations: [citation] })),
    ).toBe(false);
  });
});
