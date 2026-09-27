/**
 * The sale agent as the panel sees it. C42.
 *
 * **Everything the free-query answer carries, plus what the loop did.** The comparison this panel
 * exists to enable runs the same question through both routes, so the agent's answer is a
 * difference of fields rather than a shape of its own — mirroring the service, where the agent's
 * response model is a subclass of the deterministic one.
 *
 * No figure here was written by a model: price and stock come from the catalog and the inventory of
 * the point of sale, exactly as on the sale card.
 */

import type { AssistedSearchResult, SearchFailureOutcome } from './ai-search.types';
import type { PitchStatus, SalesAssistCitation } from './sales-assist.types';

/* -------------------------------------------------------------------------------------------
 * The transcript
 * ---------------------------------------------------------------------------------------- */

/**
 * Who a turn is attributed to.
 *
 * **`asistente` is attributed and never trusted** — the service stores no conversation, so every
 * turn arrives from here. That is what authorises the panel to put a short synthetic line in an
 * assistant turn whose argument was withheld, and what makes the total character cap a sum over
 * turns this client wrote.
 */
export type AgentTurnRole = 'operario' | 'asistente';

/** One turn of the conversation, as it travels in the request. */
export interface AgentTurn {
  role: AgentTurnRole;
  text: string;
}

/**
 * The three caps the frozen contract declares, mirrored so the composer can count before sending.
 *
 * **The three are independent, and the total is the one that is easy to miss.** It sums *every*
 * turn, the assistant's included, so twelve turns each within the per-turn cap can still exceed it
 * — and do, because the argument is sent back verbatim at a median of 386 characters. That is what
 * fixes the depth of a conversation at **six exchanges**: six operator turns plus six assistant
 * turns is twelve, so the turn cap bites first while the character count sits around 2 466 of 4 000.
 *
 * A counter measuring only what the operator typed would read half its limit with the refusal
 * already earned, which is precisely the refusal the counter exists to prevent.
 */
export const AGENT_TRANSCRIPT_CAPS = {
  maxTurns: 12,
  maxTurnChars: 500,
  maxTranscriptChars: 4000,
} as const;

/* -------------------------------------------------------------------------------------------
 * The answer
 * ---------------------------------------------------------------------------------------- */

/**
 * Where a group of the answer came from, from a closed vocabulary of two.
 *
 * **Never inferred from position.** The payload keeps the order the evidence arrived in, so
 * position says nothing about provenance — and offering a second-best alternative as though it
 * were what was asked for is what a customer notices and what makes them stop trusting the counter.
 */
export type AgentGroupOrigin = 'catalogo' | 'sustitutos';

/** One group of the answer, labelled by where its evidence came from. */
export interface AgentAssistGroup {
  familyId: string | null;
  familyLabel: string | null;
  origin: AgentGroupOrigin;
  /**
   * Members in the order the service ranked them. Never re-sorted on the client: re-sorting would
   * make the rank measure this code instead of retrieval quality.
   */
  members: AssistedSearchResult[];
}

/** One tool call of one iteration of the loop: what, and how it went. */
export interface AgentTraceTool {
  /** Name of the tool invoked, from the frozen set of six. */
  tool: string;
  ok: boolean;
  /** Closed-vocabulary failure cause when the observation failed, null otherwise. */
  cause?: string | null;
}

/**
 * One turn of the loop, as the trace shows it.
 *
 * **No tool argument and no observation content**, by rule rather than by omission: the arguments
 * are the operator's question as the model reformulated it, which the service's no-persistence rule
 * keeps out of durable storage. The contract does not carry them, so there is nothing to render.
 */
export interface AgentTraceIteration {
  iteration: number;
  tools: AgentTraceTool[];
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  elapsedMs: number;
}

/**
 * What one agent turn cost. Present only for an administrator.
 *
 * Inputs of a cost and never the cost: tokens and model, never euros. On this route `model` is not
 * even a pricing key — the counts add up to as many as three stages that may run different models.
 */
export interface AgentAssistUsage {
  model: string | null;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  promptVersion: string | null;
  /** Chat-provider calls the turn made, which is what makes the loop's ceiling observable. */
  providerCalls: number;
  aiMs: number | null;
  totalMs: number;
}

/** The answer to one turn of a conversation. */
export interface AgentAssistResponse {
  groups: AgentAssistGroup[];
  pitch?: string | null;
  pitchStatus: PitchStatus;
  citations: SalesAssistCitation[];
  /** Warning codes about **the conversation**, never about a piece. */
  warnings: string[];
  /** The question the service asked back, verbatim. Rendered as it arrives and never rewritten. */
  clarificationQuestion?: string | null;
  /** What the router decided about the last turn. */
  intent?: string | null;
  abstained: boolean;
  aiAvailable: boolean;
  /** Why the AI path degraded, from the closed vocabulary. Null when it did not. */
  degradedReason?: string | null;

  /**
   * The answer is not the one an unhurried request would have produced.
   *
   * Measured at **2.0 %** of requests on the model that is served, against 58.8 % on the cheap one
   * — which is why the screen states it without alarm, and states it last.
   */
  partial: boolean;
  /**
   * Why the loop stopped, from the service's closed vocabulary of ten.
   *
   * **Read from this value alone and never derived from the counters below.** A count of iterations
   * does not say whether the last was the last one needed or the one that ran out, and those are
   * opposite claims about the answer being read.
   */
  stopReason: string;
  iterations: number;
  toolCallsUsed: number;
  /** The only thing on screen that distinguishes an agent from a single prompt. */
  trace: AgentTraceIteration[];
  agentPromptVersion?: string | null;

  /** Null for anyone but an administrator. */
  usage?: AgentAssistUsage | null;
  searchEventId?: string | null;
  pointOfSaleId?: string | null;
  candidatesReturned: number;
  survivedHydration: number;
  traceId?: string | null;
}

/**
 * How an agent turn ended, from the panel's point of view.
 *
 * `rate-limited` is a member of its own for the reason the two sibling routes hold it apart, and
 * here it matters more: the quota that binds this route is tokens per minute, so exceeding the
 * allowance is both likelier and resolved by waiting — the opposite remedy to an outage.
 */
export type AgentAssistOutcome =
  | { kind: 'ok'; response: AgentAssistResponse }
  | SearchFailureOutcome;

/** What the browser sends to answer one turn. */
export interface AgentAssistRequest {
  /** The conversation so far, oldest turn first. */
  turns: AgentTurn[];
  /**
   * The shop to answer about, or **absent** for the scope covering every shop.
   *
   * Absent is not a blank identifier, exactly as on the free query. On this route the absence costs
   * one thing more, and the panel says so: with no shop the availability label can never report
   * that the shop is out of stock, so **the loop cannot pivot to substitutes**.
   */
  pointOfSaleId?: string;
  /** Groups wanted. The server falls back to its configured default. */
  pageSize?: number;
  /** The visit this conversation belongs to, for telemetry. */
  searchSessionId?: string;
}

/* -------------------------------------------------------------------------------------------
 * The thread
 * ---------------------------------------------------------------------------------------- */

/**
 * One exchange of the thread: what the operator asked, and the block that answered it.
 *
 * **Each turn owns its answer block**, which is the decision the whole panel is built around. A
 * single results area refreshed on each turn leaves the operator reading one turn's argument while
 * the rows beneath it already belong to the next — and when the loop pivots to substitutes, the
 * piece being looked at disappears with no explanation. The pivot is exactly the behaviour the
 * agent exists to demonstrate, and it happened 125 times in the measured pass.
 */
export interface AgentExchange {
  /** Stable key for the list, so a block does not remount when a later one arrives. */
  id: string;
  /** What the operator typed for this turn. */
  question: string;
  /** The answer, or null while the request is in flight. */
  answer: AgentAssistResponse | null;
  /** A failure that is not an answer: a refusal, a throttle, a transport error. */
  failure?: SearchFailureOutcome | null;
}

/** Running totals of what the session has spent, accumulated as answers arrive. */
export interface AgentSessionCost {
  requests: number;
  totalTokens: number;
  /**
   * Euros accrued. Computed from the tokens each answer reports at a rate this panel holds, and
   * shown **before the next request is sent** rather than after — this route is measured as
   * costing several times the deterministic one, so the figure is what makes the trade-off legible
   * at the counter.
   */
  costEur: number;
}
