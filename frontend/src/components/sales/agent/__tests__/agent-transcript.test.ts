/**
 * The transcript the composer counts and the thread sends (EP15 / C42)
 *
 * **The assistant's turns are the substance here.** The contract's total sums every turn, and the
 * argument travels back verbatim at a median of 386 characters — so a counter that measured only the
 * typed text would read half its limit with the refusal already earned. That is the failure these
 * tests exist to keep closed.
 */

import { describe, it, expect } from 'vitest';

import { AGENT_TRANSCRIPT_CAPS } from '@/types/ai-agent.types';
import type { AgentAssistResponse, AgentExchange } from '@/types/ai-agent.types';
import type { AssistedSearchResult } from '@/types/ai-search.types';
import {
  assistantTurnFor,
  buildTranscript,
  capReasonText,
  countTranscript,
  syntheticAssistantLine,
} from '../agent-transcript';

function member(sku: string): AssistedSearchResult {
  return {
    productId: `p-${sku}`,
    sku,
    name: `Pieza ${sku}`,
    price: 39.9,
    quantityAtPointOfSale: 2,
    hasStock: true,
  } as AssistedSearchResult;
}

function answer(overrides: Partial<AgentAssistResponse> = {}): AgentAssistResponse {
  return {
    groups: [],
    pitchStatus: 'generated',
    citations: [],
    warnings: [],
    abstained: false,
    aiAvailable: true,
    partial: false,
    stopReason: 'sin_mas_herramientas',
    iterations: 2,
    toolCallsUsed: 3,
    trace: [],
    candidatesReturned: 0,
    survivedHydration: 0,
    ...overrides,
  };
}

function exchange(question: string, answered: AgentAssistResponse | null): AgentExchange {
  return { id: question, question, answer: answered };
}

describe('the assistant turn that travels', () => {
  it('should send the argument whole when one was served', () => {
    const pitch = 'De las dos, la de aro fino es la más sobria y la otra la más vistosa.';

    // The whole argument and not a summary: summarising would put words in the assistant's mouth it
    // never said, and it is what keeps a later deictic reference with an antecedent.
    expect(assistantTurnFor(exchange('busco un anillo', answer({ pitch })))).toEqual({
      role: 'asistente',
      text: pitch,
    });
  });

  it('should send a synthetic assistant turn when the pitch was withheld', () => {
    // 13.1 % of requests, measured. Without this the turn has no text, the validator refuses it, and
    // the thread breaks on one answer in eight.
    const withheld = answer({
      pitch: '',
      pitchStatus: 'withheld_by_ai',
      groups: [
        {
          familyId: 'fam-1',
          familyLabel: 'Aro fino',
          origin: 'catalogo',
          members: [member('ARO-M'), member('ARO-S')],
        },
      ],
    });

    const turn = assistantTurnFor(exchange('busco un anillo', withheld));

    expect(turn).not.toBeNull();
    expect(turn!.role).toBe('asistente');
    expect(turn!.text).toContain('ARO-M');
    expect(turn!.text).toContain('ARO-S');
    expect(turn!.text.length).toBeGreaterThan(0);
  });

  it('should send the clarification itself when the agent asked one back', () => {
    const question = 'Para que ocasion es el regalo?';

    // The question is the antecedent of what the operator types next, so it is what goes back.
    expect(
      assistantTurnFor(exchange('busco algo', answer({ clarificationQuestion: question }))),
    ).toEqual({ role: 'asistente', text: question });
  });

  it('should say so rather than sending an empty turn when there were no pieces either', () => {
    const turn = assistantTurnFor(exchange('busco algo', answer({ pitch: '', groups: [] })));

    expect(turn!.text.length).toBeGreaterThan(0);
  });

  it('should send nothing for a turn still in flight', () => {
    expect(assistantTurnFor(exchange('busco algo', null))).toBeNull();
  });

  it('should keep a synthetic line inside the per-turn cap however many pieces there were', () => {
    const many = Array.from({ length: 40 }, (_, index) => `SKU-MUY-LARGO-${index}`);

    expect(syntheticAssistantLine(many).length).toBeLessThanOrEqual(
      AGENT_TRANSCRIPT_CAPS.maxTurnChars,
    );
  });
});

describe('the counters of the composer', () => {
  it('should count the assistant turns towards the transcript caps', () => {
    const pitch = 'x'.repeat(386);
    const exchanges = [
      exchange('busco un anillo', answer({ pitch })),
      exchange('y en dorado?', answer({ pitch })),
    ];

    const count = countTranscript(buildTranscript(exchanges, 'y mas barato'), true);

    // Four turns of history plus the draft: the assistant's two are half of them.
    expect(count.turns).toBe(5);
    // And they are most of the characters. A counter over the typed text alone would read ~40.
    expect(count.chars).toBeGreaterThan(2 * 386);
  });

  it('should reach the turn cap at six exchanges rather than at twelve questions', () => {
    // The economy the measurement fixes: six operator turns plus six assistant turns is twelve, so
    // the turn cap bites first while the characters sit well under their own limit.
    const six = Array.from({ length: 6 }, (_, index) =>
      exchange(`pregunta ${index}`, answer({ pitch: 'x'.repeat(386) })),
    );

    const closed = countTranscript(buildTranscript(six, 'una septima'), true);

    expect(closed.turns).toBe(13);
    expect(closed.exceeded).toBe('turns');
    expect(closed.chars).toBeLessThan(AGENT_TRANSCRIPT_CAPS.maxTranscriptChars);
  });

  it('should close one turn early when the history alone fills the turn cap', () => {
    // **A turn is indivisible.** With twelve turns of history any question overflows, so the composer
    // has to close before the operator types rather than after they have written a paragraph.
    const six = Array.from({ length: 6 }, (_, index) =>
      exchange(`pregunta ${index}`, answer({ pitch: 'corta' })),
    );

    const count = countTranscript(buildTranscript(six, ''), false);

    expect(count.turns).toBe(AGENT_TRANSCRIPT_CAPS.maxTurns);
    expect(count.exceeded).toBe('turns');
  });

  it('should keep room for a short question when only the characters are nearly spent', () => {
    // Characters are divisible, so they get no such treatment: a history at 3 900 of 4 000 still has
    // room for a short question, and closing there would refuse a request the service would serve.
    const exchanges = [
      exchange('x'.repeat(400), answer({ pitch: 'y'.repeat(500) })),
      exchange('x'.repeat(400), answer({ pitch: 'y'.repeat(500) })),
    ];

    const count = countTranscript(buildTranscript(exchanges, ''), false);

    expect(count.chars).toBeGreaterThan(1500);
    expect(count.exceeded).toBeNull();
  });

  it('should report the total cap when the arguments are long even inside the turn cap', () => {
    // The cap the other two do not imply: five exchanges of a maximum-length argument exceed the
    // total while every turn is within its own limit and the turn count is under twelve.
    const long = Array.from({ length: 5 }, () =>
      exchange('x'.repeat(400), answer({ pitch: 'y'.repeat(500) })),
    );

    const count = countTranscript(buildTranscript(long, ''), false);

    expect(count.turns).toBeLessThanOrEqual(AGENT_TRANSCRIPT_CAPS.maxTurns);
    expect(count.exceeded).toBe('total-chars');
  });

  it('should report no cap reached when there is room for the turn', () => {
    const count = countTranscript(buildTranscript([], 'busco un anillo de plata'), true);

    expect(count.turns).toBe(1);
    expect(count.exceeded).toBeNull();
  });

  it('should count the history alone before anything is typed', () => {
    // What decides whether there is room for another exchange at all, which is what the composer
    // needs to know before the operator starts writing rather than after.
    const exchanges = [exchange('busco un anillo', answer({ pitch: 'x'.repeat(386) }))];

    const count = countTranscript(buildTranscript(exchanges, ''));

    expect(count.turns).toBe(2);
    expect(count.chars).toBeGreaterThan(386);
  });

  it('should name the cap that closed the composer for each of the three', () => {
    for (const cap of ['turns', 'turn-chars', 'total-chars'] as const) {
      expect(capReasonText(cap).length).toBeGreaterThan(20);
    }

    // The two that end a conversation say what to do; the per-turn one says to shorten.
    expect(capReasonText('turns')).toContain('nueva');
    expect(capReasonText('total-chars')).toContain('nueva');
    expect(capReasonText('turn-chars')).toContain('rtalo');
  });

  it('should mention the assistant answers in the total cap reason', () => {
    // The operator has typed maybe two hundred characters and the counter says four thousand: the
    // reason has to explain where the rest came from or it reads as a bug.
    expect(capReasonText('total-chars')).toContain('respuestas del agente');
  });
});

describe('the transcript that is built', () => {
  it('should put the turns in order oldest first with the draft last', () => {
    const turns = buildTranscript(
      [exchange('primera', answer({ pitch: 'respuesta uno' }))],
      'segunda',
    );

    expect(turns.map((turn) => [turn.role, turn.text])).toEqual([
      ['operario', 'primera'],
      ['asistente', 'respuesta uno'],
      ['operario', 'segunda'],
    ]);
  });

  it('should leave the draft out when it is blank', () => {
    expect(buildTranscript([], '   ')).toEqual([]);
  });

  it('should skip the assistant turn of an exchange still in flight', () => {
    const turns = buildTranscript([exchange('primera', null)], 'segunda');

    expect(turns.map((turn) => turn.role)).toEqual(['operario', 'operario']);
  });
});
