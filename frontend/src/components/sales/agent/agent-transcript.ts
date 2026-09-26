/**
 * Building the transcript that will be sent, and counting it. C42.
 *
 * **The counters count what is about to be sent, not what was typed.** The contract's total cap sums
 * every turn, the assistant's included, and the argument travels back verbatim at a median of 386
 * characters. A counter that measured only the operator's typing would read well under its limit
 * while the request was already over the total — which is precisely the refusal the counter exists
 * to prevent.
 *
 * That is also what fixes the depth of a conversation at **six exchanges**: six operator turns plus
 * six assistant turns is twelve, so the turn cap bites first while the character count sits around
 * 2 466 of 4 000 at the median and 3 780 at the maximum argument length measured.
 */

import { AGENT_TRANSCRIPT_CAPS } from '@/types/ai-agent.types';
import type { AgentExchange, AgentTurn } from '@/types/ai-agent.types';

/**
 * What an assistant turn carries when the argument was withheld or the answer was a question.
 *
 * **A short synthetic line naming the pieces.** The argument is withheld in 13.1 % of requests, which
 * would leave the turn with no text — and a turn with no text is refused by the validator, so the
 * thread would break on one answer in eight. Naming the SKUs keeps a later «ése» with an antecedent,
 * which is the whole reason the assistant's turn is sent at all.
 *
 * The contract authorises this explicitly: the assistant role is **attributed and never trusted**,
 * since the service stores no conversation and every turn arrives from the client.
 */
export function syntheticAssistantLine(skus: readonly string[]): string {
  if (skus.length === 0) return 'Sin piezas que ofrecer en ese turno.';
  // Bounded so one turn cannot eat the total cap on its own: the cap is per turn as well as overall.
  const named = skus.slice(0, 6).join(', ');
  return `Te enseñé: ${named}.`.slice(0, AGENT_TRANSCRIPT_CAPS.maxTurnChars);
}

/**
 * The assistant turn for one answered exchange.
 *
 * Three cases, and the first is the one that matters: **the argument goes back whole.** Summarising it
 * would put words in the assistant's mouth that it never said, and sending only the operator's turns
 * would leave «el segundo» and «ése» with nothing to refer to — measured against the three options,
 * the whole argument is the only one where the deictic reference of the next turn still works.
 */
export function assistantTurnFor(exchange: AgentExchange): AgentTurn | null {
  const answer = exchange.answer;
  if (!answer) return null;

  // A clarification: the question itself is what the operator answered, so it is the antecedent.
  if (answer.clarificationQuestion) {
    return {
      role: 'asistente',
      text: answer.clarificationQuestion.slice(0, AGENT_TRANSCRIPT_CAPS.maxTurnChars),
    };
  }

  const pitch = answer.pitch?.trim();
  if (pitch) {
    return { role: 'asistente', text: pitch.slice(0, AGENT_TRANSCRIPT_CAPS.maxTurnChars) };
  }

  // Withheld. The synthetic line, from the pieces that were actually shown.
  const skus = answer.groups.flatMap((group) => group.members.map((member) => member.sku));
  return { role: 'asistente', text: syntheticAssistantLine(skus) };
}

/**
 * The transcript for the next turn: every exchange so far, then what is being typed.
 *
 * `draft` may be empty, which is how the composer counts **before** anything is typed: the cost of
 * the history alone is what decides whether there is room for another exchange at all.
 */
export function buildTranscript(
  exchanges: readonly AgentExchange[],
  draft: string,
): AgentTurn[] {
  const turns: AgentTurn[] = [];

  for (const exchange of exchanges) {
    turns.push({
      role: 'operario',
      text: exchange.question.slice(0, AGENT_TRANSCRIPT_CAPS.maxTurnChars),
    });

    const assistant = assistantTurnFor(exchange);
    if (assistant) turns.push(assistant);
  }

  const trimmed = draft.trim();
  if (trimmed) {
    turns.push({ role: 'operario', text: trimmed });
  }

  return turns;
}

/** Which of the three caps a transcript has reached, if any. */
export type TranscriptCap = 'turns' | 'turn-chars' | 'total-chars';

export interface TranscriptCount {
  turns: number;
  chars: number;
  /** The cap that is blocking, or null when there is room for this turn. */
  exceeded: TranscriptCap | null;
}

/**
 * Counts a transcript against the three caps.
 *
 * **The three are checked independently because the total is not implied by the other two**: twelve
 * turns of 500 characters is 6 000, which the total refuses. Checking only the per-turn length would
 * pass a request the service rejects, which is the whole failure this counter removes.
 *
 * **`hasDraft` is what makes the turn cap close one turn early, and a turn is why.** A turn is
 * indivisible: with twelve turns of history already, *any* question overflows, so the composer has to
 * close before the operator types rather than after. Characters are divisible, so they get no such
 * treatment — a history at 3 900 of 4 000 still has room for a short question, and closing there
 * would refuse a request the service would have served.
 */
export function countTranscript(
  turns: readonly AgentTurn[],
  hasDraft = false,
): TranscriptCount {
  const chars = turns.reduce((total, turn) => total + turn.text.length, 0);
  // The slot the next question will occupy, when it is not occupied already.
  const wouldBe = turns.length + (hasDraft ? 0 : 1);

  let exceeded: TranscriptCap | null = null;
  if (wouldBe > AGENT_TRANSCRIPT_CAPS.maxTurns) {
    exceeded = 'turns';
  } else if (turns.some((turn) => turn.text.length > AGENT_TRANSCRIPT_CAPS.maxTurnChars)) {
    exceeded = 'turn-chars';
  } else if (chars > AGENT_TRANSCRIPT_CAPS.maxTranscriptChars) {
    exceeded = 'total-chars';
  }

  return { turns: turns.length, chars, exceeded };
}

/** Why the composer closed, in Spanish, naming the cap so the operator knows what to do. */
export const CAP_REASON_COPY: Record<TranscriptCap, string> = {
  turns:
    'La conversación ha llegado a su tope de turnos. Empieza una nueva para seguir preguntando.',
  'turn-chars': 'Ese turno es demasiado largo. Acórtalo para poder enviarlo.',
  'total-chars':
    'La conversación ha llegado a su tope de caracteres, contando las respuestas del agente. '
    + 'Empieza una nueva para seguir preguntando.',
};

export function capReasonText(cap: TranscriptCap): string {
  return CAP_REASON_COPY[cap];
}
