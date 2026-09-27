/**
 * The assisted answer on screen (C40).
 *
 * One component, driven by a **resolved state** rather than by a ladder of field checks. The
 * sixteen conditions an assisted answer can arrive in are combinations of fields, and a screen
 * that branched on each field separately would get every branch right and the combinations
 * wrong — which is how the panel of C16 came to have five branches of emptiness, three of which
 * would paint a correct answer as a failure.
 *
 * `resolveFreeQueryState` does the deciding; this does the saying. The table with the
 * measurements behind each state lives in
 * `Documentos/Proyecto Final AIEng/informes/c40-m1-panel-states.md`.
 */

import { useEffect } from 'react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Card, CardContent } from '@/components/ui/card';
import { Quote, Sparkles } from 'lucide-react';

import { CitationRow } from '@/components/sales/sales-assist-card/pitch-block';
import { AssistedSearchResultRow } from '@/components/sales/assisted-search-result-row';
import {
  NO_VERIFIABLE_SOURCE,
  noRouteMessage,
  freeQueryPitchMessage,
  queryWarnings,
  warningLabel,
} from '@/lib/assist-copy';
import { FreeQueryFunnel } from '@/components/sales/free-query/free-query-funnel';
import { familyNote } from '@/lib/family-note';
import {
  isEmptyResult,
  resolveFreeQueryState,
  showsCitationBlock,
  showsNoVerifiableSource,
} from '@/lib/free-query-states';
import type { AssistedSearchResult, FreeQuerySearchResponse } from '@/types/ai-search.types';

interface FreeQueryAnswerProps {
  response: FreeQuerySearchResponse;
  onSelect: (result: AssistedSearchResult) => void;
  onOpenCard: (result: AssistedSearchResult) => void;
  /**
   * Called when the service asked a question back, so the caller can return focus to the query
   * box — which is the action the question itself is asking for.
   */
  onClarificationAsked?: () => void;
  /** The shop the answer is about, so each row's stock label can name it. */
  pointOfSaleName?: string | null;
  /**
   * Whether the caller is an administrator, which is the only thing that shows the funnel.
   *
   * Read from the role and **not** from `usage` being present, even though the backend builds
   * `usage` only for an administrator. The counters are in every response, so keying the
   * whole panel on `usage` would show an operator a funnel with no times in it on a degraded
   * response — and the requirement is that an operator never sees the funnel at all.
   */
  isAdmin?: boolean;
}

export function FreeQueryAnswer({
  response,
  onSelect,
  onOpenCard,
  onClarificationAsked,
  pointOfSaleName,
  isAdmin = false,
}: FreeQueryAnswerProps) {
  const state = resolveFreeQueryState(response);

  return (
    <div className="space-y-4" data-testid="assisted-answer" data-state={state.kind}>
      {/* --- what the router decided, before anything was retrieved --------------------- */}

      {state.kind === 'refused-out-of-domain' || state.kind === 'refused-not-in-catalogue' ? (
        <Alert data-testid="assisted-refusal">
          <AlertTitle>
            {warningLabel(
              state.kind === 'refused-out-of-domain'
                ? 'query_out_of_domain'
                : 'query_not_in_catalogue',
            )}
          </AlertTitle>
          <AlertDescription>
            Prueba a preguntar por una pieza o por algo del oficio.
          </AlertDescription>
        </Alert>
      ) : null}

      {state.kind === 'clarification' ? (
        <ClarificationBlock question={state.question} onAsked={onClarificationAsked} />
      ) : null}

      {/* --- what retrieval decided ----------------------------------------------------- */}

      {state.kind === 'abstained' ? (
        <Alert data-testid="assisted-abstained">
          <AlertTitle>No tengo nada que encaje con lo que describes</AlertTitle>
          <AlertDescription>Prueba a describirlo de otra forma.</AlertDescription>
        </Alert>
      ) : null}

      {state.kind === 'filters-too-narrow' ? (
        <Alert variant="warning" data-testid="assisted-filters-too-narrow">
          <AlertTitle>{warningLabel('filters_too_narrow')}</AlertTitle>
          {/* A different ending from the abstention's, and that is the point of telling them
              apart: here the thing to do is remove a filter, there it is to describe it again. */}
          <AlertDescription>Prueba a quitar alguno de los filtros.</AlertDescription>
        </Alert>
      ) : null}

      {/* --- the two states with no route ----------------------------------------------- */}

      {state.kind === 'no-route-contradictory' || state.kind === 'no-route-classifier-down' ? (
        <NoRouteBlock intent={response.intent} />
      ) : null}

      {/* --- .NET never got an answer ---------------------------------------------------- */}

      {state.kind === 'degraded' ? (
        <Alert variant="warning" data-testid="assisted-degraded">
          <AlertTitle>La respuesta asistida no está disponible</AlertTitle>
          <AlertDescription>
            Puedes usar la búsqueda rápida, que no necesita el asistente.
          </AlertDescription>
        </Alert>
      ) : null}

      {/* --- the query's own warnings, which are the only ones this screen may show ------- */}

      {queryWarnings(response.warnings).length > 0 &&
      state.kind !== 'refused-out-of-domain' &&
      state.kind !== 'refused-not-in-catalogue' &&
      state.kind !== 'filters-too-narrow' ? (
        <Alert data-testid="assisted-query-warnings">
          <AlertDescription>
            {queryWarnings(response.warnings).map((code) => (
              <span key={code} className="block">
                {warningLabel(code)}
              </span>
            ))}
          </AlertDescription>
        </Alert>
      ) : null}

      {/* --- the argument ----------------------------------------------------------------- */}

      {state.kind === 'answered' && response.pitch ? (
        <Card>
          <CardContent className="space-y-3 p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Quote className="size-4" />
              Argumentario
            </div>

            <p className="whitespace-pre-line" data-testid="assisted-pitch">
              {response.pitch}
            </p>

            {/* A discreet line and never an alert: it fires on roughly a quarter of knowledge
                answers, and at that frequency an alert trains an operator to ignore it. */}
            {showsNoVerifiableSource(response) ? (
              <p
                className="text-xs text-muted-foreground"
                data-testid="assisted-no-verifiable-source"
              >
                {NO_VERIFIABLE_SOURCE}
              </p>
            ) : null}

            {/* No prose, no citations. The service keeps them on purpose when it withholds the
                argument — that serves the evaluation harness — but for an operator a citation
                with no claim attached attributes nothing. */}
            {showsCitationBlock(response) ? (
              <div className="space-y-2">
                {response.citations.map((citation) => (
                  <CitationRow key={citation.citationId} citation={citation} />
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>
      ) : null}

      {/* 12 · 14 · 15 — results are real, the text is not there. `pitchStatus` says which. */}
      {state.kind === 'answered-without-prose' ? (
        <WithoutProseBlock response={response} />
      ) : null}

      {/* --- the pieces -------------------------------------------------------------------- */}

      {response.groups.map((group) =>
        group.members.map((member) => (
          <AssistedSearchResultRow
            key={member.productId}
            result={member}
            onSelect={onSelect}
            onOpenCard={onOpenCard}
            pointOfSaleName={pointOfSaleName}
            familyNote={familyNote(group, member.productId)}
          />
        )),
      )}

      {/* **Emptiness is not `groups.length === 0`.** On the knowledge route the service answers
          from the corpus and returns zero pieces on purpose, and announcing that as "no results"
          would write a failure directly above a correct answer. */}
      {/* Last, and only for an administrator. A diagnostic panel above the pieces would put
          the cost of a search between the operator and the answer they asked for. */}
      {isAdmin ? (
        <FreeQueryFunnel
          response={response}
          displayed={response.groups.reduce((total, group) => total + group.members.length, 0)}
        />
      ) : null}

      {isEmptyResult(response) && state.kind === 'answered' ? (
        <Alert data-testid="assisted-empty">
          <AlertTitle>Sin resultados</AlertTitle>
          <AlertDescription>No he encontrado nada que enseñarte para esto.</AlertDescription>
        </Alert>
      ) : null}
    </div>
  );
}

/**
 * The service's own question, rendered exactly as it arrives.
 *
 * Never rewritten and never paraphrased: the catalogue of questions is closed and written in
 * code on the service side, precisely so that no model composes a sentence an operator reads out
 * loud to a customer.
 */
function ClarificationBlock({
  question,
  onAsked,
}: {
  question: string;
  onAsked?: () => void;
}) {
  // Focus goes back to the query box, which is the action the question is asking for. In an
  // effect and keyed on the question: doing it during render would be a side effect in a render,
  // and re-running it on every render would fight the operator for the caret while they type.
  useEffect(() => {
    onAsked?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [question]);

  return (
    <Alert data-testid="assisted-clarification">
      <AlertTitle>{question}</AlertTitle>
    </Alert>
  );
}

/**
 * The two states with no route, which need opposite copy.
 *
 * With `in_domain` the classifier ran and contradicted itself, so asking for another wording is
 * fair. With `unclassified` it never ran — no credential, a two-second timeout, an unparseable
 * reply — and asking the operator to rephrase would be blaming them for a configuration. It is
 * not a theoretical path: with the router's credential missing, every query lands there.
 */
function NoRouteBlock({ intent }: { intent?: string | null }) {
  const message = noRouteMessage(intent);

  return (
    <Alert data-testid="assisted-no-route" data-intent={intent ?? 'unknown'}>
      <AlertTitle>{message.title}</AlertTitle>
      <AlertDescription>
        {message.body}
        {message.action ? (
          <span className="mt-1 block" data-testid="assisted-rephrase-invitation">
            {message.action}
          </span>
        ) : null}
      </AlertDescription>
    </Alert>
  );
}

/**
 * Results with no argument over them.
 *
 * The message comes from the shared table, which already distinguishes an argument the gate
 * withheld from one that was never generated — `withheld_by_ai` against `not_generated`, told
 * apart by whether a prompt version travelled. C36 built that distinction; it is reused rather
 * than restated.
 */
function WithoutProseBlock({ response }: { response: FreeQuerySearchResponse }) {
  // The panels do not share this copy: the card says «la ficha» and «esta pieza», and this
  // screen has neither. Found by the real-data check of C40 rather than by a test.
  const message = freeQueryPitchMessage(response.pitchStatus, response.degradedReason);

  if (!message) {
    return null;
  }

  return (
    <Alert data-testid="assisted-without-prose" data-pitch-status={response.pitchStatus}>
      <AlertTitle>{message.title}</AlertTitle>
      <AlertDescription>
        {message.body}
        {/* Empty for `not_generated`, and that is the prescription rather than an oversight:
            the classifier timed out or was never configured, and asking the operator to act
            on that would blame them for an outage. */}
        {message.action ? <span className="mt-1 block">{message.action}</span> : null}
      </AlertDescription>
    </Alert>
  );
}

/**
 * What the panel shows while an assisted answer is in flight.
 *
 * **A line of expectation from the first instant, never a blank pane.** The measured budget is
 * ten seconds and C34 saw a p95 of 7,1 s without the router; seven seconds of undifferentiated
 * waiting with a customer at the counter is where this feature gets abandoned. Saying it may
 * take a few seconds costs nothing and changes what the wait means.
 */
export function FreeQueryLoading() {
  return (
    <div className="space-y-2" data-testid="assisted-loading">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Sparkles className="size-4 animate-pulse" aria-hidden />
        Preparando la respuesta asistida; puede tardar unos segundos.
      </div>
    </div>
  );
}

export default FreeQueryAnswer;
