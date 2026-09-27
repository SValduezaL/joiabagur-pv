/**
 * Sale Card — the argument and its citations (EP15 / C36)
 *
 * Six states of the argument rendered as five things: the argument itself, and four messages
 * over the five states that carry none. The two that differ in **provenance** —
 * `ai_unavailable`, where the family, the materials and the match reasons come from the
 * transactional catalog and there are no citations, and `not_generated`, where they come from
 * the index — never share a message. All six stay distinguishable in the document through the
 * `data-pitch-status` attribute, so a test can separate the two that share a text.
 *
 * Citations are readable rather than clickable. No route serves the corpus — it lives as files
 * in the AI service's repository — so of the three properties a verifiable citation should have,
 * two are delivered: it resolves and it locates. The third is declared as a limitation.
 *
 * They are **hidden when the argument was not delivered**: showing the sources of a text the
 * operator cannot read attributes nothing, and they would be only the ones that argument used
 * anyway.
 */

import { ChevronDown, FileText, Quote } from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  ESTABLISHMENT_CLAIM_NOTE,
  claimScopeLabel,
  isEstablishmentClaim,
  pitchMessage,
  showsCitations,
} from '@/lib/assist-copy';
import type { PitchStatus, SalesAssistCitation } from '@/types/sales-assist.types';

interface CitationRowProps {
  citation: SalesAssistCitation;
}

/**
 * One citation, collapsible, with its claim scope stated in words as well as by colour.
 *
 * Exported since C40 so the free-query panel reuses it instead of copying it. The thing worth
 * not duplicating is the establishment/general distinction: a commitment of the house passed on
 * as a fact of the world is how a shop ends up owing something it never promised, and a second
 * copy of that rule would drift the first time one of the two was corrected.
 */
export function CitationRow({ citation }: CitationRowProps) {
  const establishment = isEstablishmentClaim(citation.claimScope);

  return (
    <Collapsible
      data-testid="assist-citation"
      data-claim-scope={citation.claimScope}
      className="rounded-md border"
    >
      <CollapsibleTrigger className="flex w-full items-center gap-2 p-3 text-start text-sm hover:bg-muted/50">
        <FileText className="size-4 shrink-0 text-muted-foreground" />
        <span className="min-w-0 flex-1">
          <span className="font-medium">{citation.documentTitle}</span>
          <span className="text-muted-foreground"> · {citation.sectionTitle}</span>
        </span>
        {/* Distinguished both visually and in words: a commitment of the house is not a fact of
            the world, and passing the first on as the second is how a shop ends up owing
            something it never promised. */}
        <Badge
          variant={establishment ? 'warning' : 'secondary'}
          appearance={establishment ? 'light' : 'outline'}
        >
          {claimScopeLabel(citation.claimScope)}
        </Badge>
        <ChevronDown className="size-4 shrink-0 text-muted-foreground" />
      </CollapsibleTrigger>

      <CollapsibleContent>
        <div className="space-y-2 border-t p-3 text-sm">
          <p className="text-muted-foreground">{citation.snippet}</p>
          {establishment ? (
            <p className="text-xs font-medium" data-testid="assist-citation-establishment-note">
              {ESTABLISHMENT_CLAIM_NOTE}
            </p>
          ) : null}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

interface PitchBlockProps {
  pitchStatus: PitchStatus;
  pitch?: string | null;
  citations: readonly SalesAssistCitation[];
  /**
   * A question back to the operator, when the AI service asked one.
   *
   * Constant null on these two routes, and read from the contract rather than removed from it.
   * It gets no block and no copy of its own — it is a field of the transfer object, not a
   * feature — but it is painted if it ever arrives.
   */
  clarificationQuestion?: string | null;
  /**
   * Why the AI path degraded, when it did. Refines the unavailable message so that a piece the
   * index has not reached yet stops reading as a service that has fallen over.
   */
  degradedReason?: string | null;
}

export function PitchBlock({
  pitchStatus,
  pitch,
  citations,
  clarificationQuestion,
  degradedReason,
}: PitchBlockProps) {
  const message = pitchMessage(pitchStatus, degradedReason);

  return (
    <div className="space-y-3" data-testid="assist-pitch" data-pitch-status={pitchStatus}>
      {message === null ? (
        <Card>
          <CardContent className="space-y-2 p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Quote className="size-4" />
              Argumentario
            </div>
            <p className="whitespace-pre-line" data-testid="assist-pitch-text">
              {pitch}
            </p>
          </CardContent>
        </Card>
      ) : (
        <Alert variant={pitchStatus === 'ai_unavailable' ? 'warning' : 'info'}>
          <AlertTitle>{message.title}</AlertTitle>
          <AlertDescription>
            <p>{message.body}</p>
            {/* Never a full stop at the end of an absence: an honest abstention says what would
                be needed to get past it. */}
            <p className="mt-1 font-medium" data-testid="assist-pitch-action">
              {message.action}
            </p>
          </AlertDescription>
        </Alert>
      )}

      {clarificationQuestion ? (
        <Alert data-testid="assist-clarification">
          <AlertDescription>{clarificationQuestion}</AlertDescription>
        </Alert>
      ) : null}

      {/* Hidden when the argument was not delivered. Presenting sources for a text nobody can
          read is decoration. */}
      {showsCitations(pitchStatus) && citations.length > 0 ? (
        <div className="space-y-2" data-testid="assist-citations">
          <p className="text-sm font-medium text-muted-foreground">
            De dónde sale ({citations.length})
          </p>
          {citations.map((citation) => (
            <CitationRow key={citation.citationId} citation={citation} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

export default PitchBlock;
