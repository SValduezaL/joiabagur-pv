/**
 * One turn's answer, as its own block. C42.
 *
 * **Each turn owns its block, and that is the decision the panel is built around.** A single results
 * area refreshed on each turn leaves the operator reading one turn's argument while the rows beneath
 * it already belong to the next — and when the loop pivots to substitutes, the piece being looked at
 * disappears with no explanation. The pivot is exactly what the agent exists to demonstrate: the
 * substitutes tool was invoked 125 times in the measured pass.
 *
 * **The order of what follows comes from measured frequencies and not from a mockup.** One answer in
 * five carries no piece at all (19.6 %, identical on both model arms), and of those, three quarters
 * are a clarification or a polite refusal — normal outcomes of a conversation, not empty results. So
 * the no-rows case is handled first and never with an empty-result phrase. Citations are present in
 * 7.8 % of answers and warnings in 3.9 %, so both render nothing at all when empty. The
 * incompleteness ribbon serves 2.0 % of requests on the model that is served, so it comes last.
 *
 * Reuses `PitchBlock` from C36 and `AssistedSearchResultRow` from C40 **unmodified**. The
 * substitutes block of C36 is not reusable and is not attempted: it feeds on similarity signals that
 * arrive through another endpoint and that the agent's member does not carry.
 */

import { AlertTriangle, Scissors } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { AssistedSearchResultRow } from '@/components/sales/assisted-search-result-row';
import { PitchBlock } from '@/components/sales/sales-assist-card/pitch-block';
import { AgentTrace } from './agent-trace';
import {
  agentWarningText,
  degradedReasonText,
  isBudgetStop,
  originText,
  stopReasonText,
} from './agent-copy';
import type { AgentAssistResponse } from '@/types/ai-agent.types';
import type { AssistedSearchResult } from '@/types/ai-search.types';

interface AgentAnswerBlockProps {
  answer: AgentAssistResponse;
  onSelect: (result: AssistedSearchResult) => void;
  onOpenCard?: (result: AssistedSearchResult) => void;
  /** The shop these figures are about, so the row can name it. Null means every shop. */
  pointOfSaleName?: string | null;
}

/**
 * Whether this answer searched the catalogue and came back with nothing.
 *
 * **The distinction the measurement forced.** Of the twenty no-piece answers per arm, fourteen are a
 * clarification or a refusal and only six — 5.9 % of requests — are «I looked and found nothing».
 * Those six are the only ones that may be worded as an empty search; wording the other fourteen that
 * way would tell the operator the catalogue failed when the conversation was working normally.
 *
 * Read from the reported state and not from the group count alone: a clarification has no groups
 * either, and so does a refusal.
 */
export function searchedAndFoundNothing(answer: AgentAssistResponse): boolean {
  if (answer.groups.length > 0) return false;
  if (answer.clarificationQuestion) return false;
  if (answer.stopReason === 'rechazado' || answer.stopReason === 'aclaracion') return false;
  // No loop, no search: the agent never got as far as the catalogue, so saying the catalogue came
  // back empty would blame it for a missing configuration.
  if (answer.stopReason === 'sin_cliente' || answer.iterations === 0) return false;
  // **Prose without pieces is a knowledge answer**, which is the largest of the three no-piece
  // states and the one that must never be worded as an empty search. The agent answered a question
  // about the trade from the corpus; the catalogue was not what was being asked about.
  if (answer.pitch?.trim()) return false;
  return answer.abstained || answer.toolCallsUsed > 0;
}

export function AgentAnswerBlock({
  answer,
  onSelect,
  onOpenCard,
  pointOfSaleName,
}: AgentAnswerBlockProps) {
  // Matches before substitutes, and never by list position: the payload keeps the order the
  // evidence arrived in, so position says nothing about provenance.
  const matches = answer.groups.filter((group) => group.origin === 'catalogo');
  const substitutes = answer.groups.filter((group) => group.origin === 'sustitutos');
  const others = answer.groups.filter(
    (group) => group.origin !== 'catalogo' && group.origin !== 'sustitutos',
  );
  const ordered = [...matches, ...substitutes, ...others];

  return (
    <div data-testid="agent-answer-block" data-stop-reason={answer.stopReason} className="space-y-4">
      {/* **The strip says one of two things, and which one depends on whether the service answered.**
          Found by the manual check of C42 and not by any test: when the gateway degrades, the response
          carries no stop reason and no counters, and claiming one told the operator «el agente terminó
          por un motivo que esta pantalla no reconoce» — which blames the screen for a service that
          simply did not answer, next to «0 vueltas · 0 consultas» about a loop that never ran. */}
      {answer.aiAvailable ? (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          {/* Translated from the reported stop reason and never derived from the counters beside it. */}
          <Badge data-testid="agent-stop-reason" variant="secondary">
            {stopReasonText(answer.stopReason)}
          </Badge>
          <span className="text-muted-foreground">
            {answer.iterations} {answer.iterations === 1 ? 'vuelta' : 'vueltas'} ·{' '}
            {answer.toolCallsUsed}{' '}
            {answer.toolCallsUsed === 1 ? 'consulta' : 'consultas'}
          </span>
        </div>
      ) : (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <Badge data-testid="agent-degraded" variant="secondary">
            {degradedReasonText(answer.degradedReason)}
          </Badge>
        </div>
      )}

      {/* The argument and its citations, from C36's block, untouched — **and deliberately not
          rendered when the service did not answer.** That block's copy for `ai_unavailable` reads
          «Lo que ves viene del catálogo: el precio, las unidades y las variantes son reales», which
          is true of the sale card it was written for and false here, where there is nothing to see:
          a degraded agent turn carries no rows at all. The strip above already says what happened. */}
      {answer.aiAvailable && (
        <PitchBlock
          pitchStatus={answer.pitchStatus}
          pitch={answer.pitch}
          citations={answer.citations}
          clarificationQuestion={answer.clarificationQuestion}
          degradedReason={answer.degradedReason}
        />
      )}

      {/* Warnings about the conversation. Present in 3.9 % of answers, so nothing renders when the
          list is empty rather than an empty section. */}
      {answer.warnings.length > 0 && (
        <ul data-testid="agent-warnings" className="space-y-1">
          {answer.warnings.map((code) => (
            <li
              key={code}
              className="flex items-start gap-2 text-sm text-muted-foreground"
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              {agentWarningText(code)}
            </li>
          ))}
        </ul>
      )}

      {/* Having searched and found nothing, told apart from the other two no-piece states. */}
      {searchedAndFoundNothing(answer) && (
        <p data-testid="agent-searched-nothing" className="text-sm text-muted-foreground">
          El agente buscó en el catálogo y no encontró ninguna pieza que encaje.
        </p>
      )}

      {/* The rows, under their provenance labels. Matches first. */}
      {ordered.map((group, index) => (
        <section
          key={`${group.origin}-${group.familyId ?? index}`}
          data-testid="agent-answer-group"
          data-origin={group.origin}
          className="space-y-2"
        >
          <h4 className="text-sm font-semibold">
            {originText(group.origin)}
            {group.familyLabel && (
              <span className="ml-2 font-normal text-muted-foreground">{group.familyLabel}</span>
            )}
          </h4>

          {group.members.map((member) => (
            <AssistedSearchResultRow
              key={member.productId}
              result={member}
              onSelect={onSelect}
              onOpenCard={onOpenCard}
              pointOfSaleName={pointOfSaleName}
            />
          ))}
        </section>
      ))}

      {/* The ladder of steps, collapsed. */}
      <AgentTrace trace={answer.trace} />

      {/* Last, and serving 2.0 % of requests on the model that is served. **No alarm colour**: the
          evidence gathered before the cut is still useful, and presenting it as an error would make
          the operator discard an answer they can sell from. */}
      {answer.partial && isBudgetStop(answer.stopReason) && (
        <Card data-testid="agent-partial-ribbon" className="border-muted bg-muted/40">
          <CardContent className="flex items-start gap-2 p-3 text-sm text-muted-foreground">
            <Scissors className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span>
              {stopReasonText(answer.stopReason)}. Lo que ves se buscó de verdad; puede que falte
              algo.
            </span>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default AgentAnswerBlock;
