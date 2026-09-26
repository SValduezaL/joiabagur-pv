/**
 * The composer, with the counters of the transcript it is about to send. C42.
 *
 * **It counts what will be sent, not what was typed**, and the difference is the whole point: the
 * contract's total sums every turn including the assistant's, and the argument goes back verbatim at
 * a median of 386 characters. A counter reading only the typed text would sit at half its limit with
 * the refusal already earned.
 *
 * **It closes with its reason at any of the three caps**, rather than letting a request leave that
 * will come back a 400. On this route that matters more than on its siblings: the quota is tokens per
 * minute at roughly one request a minute, so a wasted round trip is a wasted minute.
 */

import { Loader2, Send } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { AGENT_TRANSCRIPT_CAPS } from '@/types/ai-agent.types';
import { capReasonText } from './agent-transcript';
import type { TranscriptCount } from './agent-transcript';

interface AgentComposerProps {
  draft: string;
  onDraftChange: (value: string) => void;
  onSend: () => void;
  /** The count of the transcript that would be sent, draft included. */
  count: TranscriptCount;
  /** True while a turn is in flight. */
  pending: boolean;
  /** True when no shop is chosen yet, so nothing can be asked. */
  disabled?: boolean;
}

export function AgentComposer({
  draft,
  onDraftChange,
  onSend,
  count,
  pending,
  disabled = false,
}: AgentComposerProps) {
  const closed = count.exceeded !== null;
  const canSend = !closed && !pending && !disabled && draft.trim().length > 0;

  return (
    <div data-testid="agent-composer" className="space-y-2 border-t pt-4">
      <Textarea
        aria-label="Escribe tu pregunta al agente"
        placeholder="Pregunta al agente: «busco un anillo de plata para un regalo de 50 €»"
        value={draft}
        onChange={(event) => onDraftChange(event.target.value)}
        onKeyDown={(event) => {
          // Enter sends, Shift+Enter breaks the line: the counter shape of a counter, not a chat.
          if (event.key === 'Enter' && !event.shiftKey && canSend) {
            event.preventDefault();
            onSend();
          }
        }}
        // Closed **with its reason**, and the field goes with it: a field that still accepts text
        // while the button refuses to send is how an operator writes a paragraph for nothing.
        disabled={closed || pending || disabled}
        rows={3}
      />

      <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
        {/* The counters, of the transcript about to be sent. Both, because either can bite first:
            the turn cap at six exchanges, the character cap on unusually long arguments. */}
        <span data-testid="agent-composer-counters" className="text-muted-foreground">
          turnos {count.turns}/{AGENT_TRANSCRIPT_CAPS.maxTurns} ·{' '}
          {count.chars.toLocaleString('es-ES')}/
          {AGENT_TRANSCRIPT_CAPS.maxTranscriptChars.toLocaleString('es-ES')} car.
        </span>

        <Button onClick={onSend} disabled={!canSend} size="sm">
          {pending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Send className="mr-2 h-4 w-4" aria-hidden="true" />
          )}
          {pending ? 'Preguntando…' : 'Preguntar'}
        </Button>
      </div>

      {closed && (
        <p data-testid="agent-composer-closed" role="status" className="text-sm text-muted-foreground">
          {capReasonText(count.exceeded!)}
        </p>
      )}

      {/* The wait, stated before it happens. Measured p50 5.3 s, p95 9.0 s, maximum 11.9 s against
          a real provider: long enough that a spinner with no expectation reads as a hang. */}
      {pending && (
        <p data-testid="agent-composer-pending" role="status" className="text-sm text-muted-foreground">
          El agente está buscando. Suele tardar unos 5 segundos, y hasta 12 en el peor caso.
        </p>
      )}
    </div>
  );
}

export default AgentComposer;
