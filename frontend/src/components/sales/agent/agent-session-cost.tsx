/**
 * What the session has spent, shown before the next request is sent. C42.
 *
 * **Before and not after, and that is the whole reason it exists.** This route is measured as costing
 * several times the deterministic one and withholding its argument six times more often, so the
 * figure is what makes the trade-off legible at the counter rather than a surprise on an invoice.
 *
 * **It accumulates rather than replacing.** Each answer reports what that turn cost; the totals are
 * the running sum across the conversation, because one turn's cost says nothing about what a
 * conversation costs — and it is the conversation that the quota is spent on.
 *
 * The quota that actually binds is **tokens per minute and not money**: ~13 000 prompt tokens per
 * request against 25 000 per minute admits about one request a minute. So the tokens are shown beside
 * the euros rather than behind them.
 */

import { Coins } from 'lucide-react';

import type { AgentAssistUsage, AgentSessionCost } from '@/types/ai-agent.types';

/**
 * Euros per million tokens, prompt and completion pooled.
 *
 * **An order of magnitude and not an invoice**, which is stated here rather than implied: the tokens a
 * turn reports add up to as many as three stages that may run three different models, so `usage.model`
 * is not a pricing key and no per-model tariff would be honest. What the operator needs is whether
 * this conversation has cost cents or euros, and this delivers that.
 */
const EUR_PER_MILLION_TOKENS = 6;

/** Adds one answer's usage to the running totals. Never replaces them. */
export function accrue(
  current: AgentSessionCost,
  usage: AgentAssistUsage | null | undefined,
): AgentSessionCost {
  // A turn always counts as a request, even when the caller is an operator and the usage object is
  // absent: the request was issued and the quota was spent on it whether or not the figure travels.
  const totalTokens = current.totalTokens + (usage?.totalTokens ?? 0);

  return {
    requests: current.requests + 1,
    totalTokens,
    costEur: (totalTokens / 1_000_000) * EUR_PER_MILLION_TOKENS,
  };
}

export const EMPTY_SESSION_COST: AgentSessionCost = {
  requests: 0,
  totalTokens: 0,
  costEur: 0,
};

interface AgentSessionCostProps {
  cost: AgentSessionCost;
}

export function AgentSessionCostBar({ cost }: AgentSessionCostProps) {
  // Nothing spent yet, so nothing to state: a row of zeros reads as a rendering fault.
  if (cost.requests === 0) return null;

  return (
    <span
      data-testid="agent-session-cost"
      className="flex items-center gap-1.5 text-sm text-muted-foreground"
    >
      <Coins className="h-4 w-4 shrink-0" aria-hidden="true" />
      Sesión: {cost.requests} {cost.requests === 1 ? 'pregunta' : 'preguntas'} ·{' '}
      {Math.round(cost.totalTokens / 1000).toLocaleString('es-ES')}k tokens ·{' '}
      {cost.costEur.toLocaleString('es-ES', {
        style: 'currency',
        currency: 'EUR',
        maximumFractionDigits: 2,
      })}
    </span>
  );
}

export default AgentSessionCostBar;
