/**
 * The sixteen states of an assisted answer, resolved once (C40).
 *
 * **The unit is the state, not the field.** An assisted answer can come back in sixteen
 * distinguishable conditions, and every one of them is a *combination* of fields rather than a
 * value of any single one. A screen that branched on `groups.length`, then on `pitch`, then on
 * `intent`, would get each branch right and the combinations wrong — which is exactly how the
 * panel of C16 ended up with five branches of emptiness, three of which would paint a correct
 * assisted answer as a failure.
 *
 * So the resolution happens here, once, and the render consumes a tagged value. The full table
 * with its measurements lives in
 * `Documentos/Proyecto Final AIEng/informes/c40-m1-panel-states.md`; what follows is the mapping
 * that table implies, kept next to the code that implements it.
 *
 * ## The sixteen, and where each one lands
 *
 * | # | Condition on the wire | Resolved state |
 * |---|---|---|
 * | 1 | `intent=out_of_domain`, no groups, no pitch | `refused-out-of-domain` |
 * | 2 | `intent=not_in_catalogue` | `refused-not-in-catalogue` |
 * | 3 | `clarificationQuestion` present | `clarification` |
 * | 4 | `intent=in_domain`, results, **no prose** | `no-route-contradictory` |
 * | 5 | `intent=unclassified`, results, **no prose** | `no-route-classifier-down` |
 * | 6 | `abstained=true` | `abstained` |
 * | 7 | `filters_too_narrow` among the warnings | `filters-too-narrow` |
 * | 8 | route `catalog`, prose, zero citations **by design** | `answered` |
 * | 9 | route `knowledge`, prose, **zero groups** | `answered` — *never* an empty state |
 * | 10 | route `both`, prose, groups and citations | `answered` |
 * | 11 | prose, citations **reduced** by the gate | `answered` + `withoutVerifiableSource` |
 * | 12 | prose withheld by the gate (`promptVersion` present) | `answered-without-prose` |
 * | 13 | `knowledge`/`both` with no corpus coverage | `answered` + `knowledge_not_covered` warning |
 * | 14 | no generation ran (`promptVersion` absent) | `answered-without-prose` |
 * | 15 | a placeholder reached the gate in free-query mode | `answered-without-prose` — folds into 12 |
 * | 16 | `aiAvailable=false` | `degraded` |
 *
 * **States 12, 14 and 15 are three causes of one screen.** The operator's options are identical
 * in all three — the pieces are real, the text is not there — so they resolve to one state and
 * the *message* distinguishes them, which is the distinction C36 already renders through
 * `pitchStatus`. State 15 in particular must be invisible here: it is the failure `assist/v5`
 * and the integrity gate exist to remove, and measured after v5 it is zero.
 *
 * **The order of the checks is load-bearing** and is the order of the machine, not of
 * convenience: the router cuts before retrieval, so a refusal and a clarification are decided
 * before anything was searched and must win over any later condition. Abstention comes next
 * because it is decided before generation. Only then does the shape of what arrived matter.
 */

import type { FreeQuerySearchResponse } from '@/types/ai-search.types';

/** The state an assisted answer is in, once resolved. */
export type FreeQueryState =
  /** 16 · .NET never got an answer: switched off, circuit open, credential rejected, 501. */
  | { kind: 'degraded'; reason: string | null }
  /** 1 · Not a jewellery question at all. */
  | { kind: 'refused-out-of-domain' }
  /** 2 · A jewellery question about an object this shop does not stock. A different sentence. */
  | { kind: 'refused-not-in-catalogue' }
  /** 3 · The service asked a question back. Rendered verbatim. */
  | { kind: 'clarification'; question: string }
  /** 6 · Retrieval abstained: nothing in the catalogue is close to what was described. */
  | { kind: 'abstained' }
  /** 7 · The description is answerable; the filters are what left nothing. */
  | { kind: 'filters-too-narrow' }
  /** 4 · The classifier ran and contradicted itself. Rephrasing is a fair thing to ask. */
  | { kind: 'no-route-contradictory' }
  /** 5 · The classifier never ran. Asking for a rephrase would blame the operator. */
  | { kind: 'no-route-classifier-down' }
  /** 12 · 14 · 15 · Results are real, the argument is not there. `pitchStatus` says why. */
  | { kind: 'answered-without-prose' }
  /** 8 · 9 · 10 · 11 · 13 · An answer, with prose. */
  | { kind: 'answered' };

/**
 * Which of the sixteen this response is in.
 *
 * Exported and tested directly rather than inlined in the component, because the assertion worth
 * making is about the *classification* and not about the pixels: the three states the panel
 * would paint wrongly by default are wrong in the resolution, not in the markup.
 */
export function resolveFreeQueryState(response: FreeQuerySearchResponse): FreeQueryState {
  // 16 first: with no answer from the AI there is nothing else to read. Everything below
  // describes what the service said, and it said nothing.
  if (!response.aiAvailable) {
    return { kind: 'degraded', reason: response.degradedReason ?? null };
  }

  // 1 and 2 · The router cut before retrieving anything, so these win over any later shape.
  // Two codes and two sentences: what an operator says differs between a trade the shop does
  // not practise and a piece it does not carry.
  if (response.warnings.includes('query_out_of_domain')) {
    return { kind: 'refused-out-of-domain' };
  }
  if (response.warnings.includes('query_not_in_catalogue')) {
    return { kind: 'refused-not-in-catalogue' };
  }

  // 3 · Also decided before retrieval. The question is the service's own, from a closed
  // catalogue written in code, and is rendered exactly as it arrives.
  if (response.clarificationQuestion) {
    return { kind: 'clarification', question: response.clarificationQuestion };
  }

  // 6 · Decided before generation, and it means the catalogue has nothing close to the
  // description — which is a different fact from a filter having excluded everything.
  if (response.abstained) {
    return { kind: 'abstained' };
  }

  // 7 · The opposite reading of a thin result set: the description *is* answerable and the
  // filters are what left nothing. The service decides this with an unfiltered probe; the
  // screen must not try to infer it from a count.
  if (response.warnings.includes('filters_too_narrow')) {
    return { kind: 'filters-too-narrow' };
  }

  if (!response.pitch) {
    // 4 and 5 · Nothing was retrieved *and* nothing was written: the generation never ran
    // because no task was chosen, which happens exactly when the router decided no index.
    // **Only `intent` separates the two**, and they need opposite copy — one invites a
    // rephrase, the other must not.
    //
    // The fail-open consults both branches when there is no route, so a response here can
    // still carry pieces; what makes it states 4/5 rather than 12 is that nothing at all came
    // back. With content present, the distinction stops being about routing.
    if (!hasContent(response)) {
      return response.intent === 'unclassified'
        ? { kind: 'no-route-classifier-down' }
        : { kind: 'no-route-contradictory' };
    }

    // 12 · 14 · 15 · Something was retrieved and there is no text over it. One state, because
    // nothing the operator can do differs; `pitchStatus` carries which of the three it was.
    return { kind: 'answered-without-prose' };
  }

  // 8 · 9 · 10 · 11 · 13
  return { kind: 'answered' };
}

/**
 * Whether the response carries anything at all besides prose.
 *
 * Used to tell "nothing was retrieved" from "something was retrieved and not written up", which
 * is the difference between states 4/5 and state 12.
 */
function hasContent(response: FreeQuerySearchResponse): boolean {
  return response.groups.length > 0 || response.citations.length > 0;
}

/**
 * **Whether this is genuinely an empty result set.**
 *
 * The rule the panel of C16 gets wrong by default, and the one that costs the most: with
 * `route=knowledge` the service answers a question from the corpus and returns **zero pieces on
 * purpose**. Its five branches of emptiness would write «Sin resultados» directly above a
 * correct answer.
 *
 * So emptiness is not `groups.length === 0`. It is the absence of *everything the operator could
 * read*: no pieces, no prose, no citations. Anything else is an answer of some shape.
 */
export function isEmptyResult(response: FreeQuerySearchResponse): boolean {
  return (
    response.groups.length === 0 &&
    response.citations.length === 0 &&
    !response.pitch
  );
}

/**
 * Whether the citation block should be rendered at all.
 *
 * **No prose, no citations**, and the reason is not tidiness. When the integrity gate withholds
 * the argument it deliberately *keeps* the citations — a degraded response must never be poorer
 * than what the structured layer produces on its own, which is what keeps the ablation
 * comparable for the evaluation harness. That decision serves the harness. This one serves the
 * operator, and for them a citation with no claim attached attributes nothing: it is a reference
 * to a document in support of a sentence that is not on the screen.
 *
 * The two are both right and point in opposite directions because they serve different
 * consumers. Whoever reads one without the other will try to unify them.
 */
export function showsCitationBlock(response: FreeQuerySearchResponse): boolean {
  return Boolean(response.pitch) && response.citations.length > 0;
}

/**
 * Whether to say, discreetly, that the argument has no source anyone can check.
 *
 * There is prose and there are no citations. On the `catalog` route that is correct and expected
 * — the corpus is not consulted at all — so it is **not** said there; saying it would report a
 * gap where there is none. Elsewhere it means the gate withdrew what the model declared, which
 * happens on roughly a quarter of knowledge answers.
 */
export function showsNoVerifiableSource(response: FreeQuerySearchResponse): boolean {
  if (!response.pitch || response.citations.length > 0) {
    return false;
  }

  // The catalog route is answered from pieces and its own task tells the model to cite nothing,
  // so an empty citation list there is the correct state rather than a withdrawal.
  if (isCatalogOnly(response)) {
    return false;
  }

  // The corpus was consulted and covers nothing: the warning already says that, in more useful
  // words. Two lines about the same absence is one too many.
  return !response.warnings.includes('knowledge_not_covered');
}

/**
 * Whether this answer came from the catalogue alone.
 *
 * Inferred from the shape rather than read from a field, because the route does not travel on
 * the wire: pieces and no citations, with prose, is what the `catalog` task produces.
 */
function isCatalogOnly(response: FreeQuerySearchResponse): boolean {
  return response.groups.length > 0 && response.citations.length === 0;
}
