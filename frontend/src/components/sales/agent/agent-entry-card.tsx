/**
 * The agent's entry card on the sales landing page. C42.
 *
 * **Three states, and the third is the one that matters.** The card is active when the probe says
 * the agent is available, disabled *with its reason* when it says it is not, and **active with a
 * warning** when the probe cannot answer at all. Failing the probe must not close a door that may
 * well work — the rule the availability badge of the assisted panel already follows, and the reason
 * a screen that presented a capability that was off as though it were on is the failure this whole
 * family of changes keeps being opened to remove.
 *
 * **The reason shown is the agent's own.** The agent has a credential chain of its own on the
 * service side, so a deployment can have the assisted answer configured and the agent not; showing
 * the assisted answer's reason here would explain the wrong switch.
 *
 * Reading the probe costs no request-rate quota and runs no model, which is why it happens **on
 * mount** rather than on press. That is its whole reason for existing.
 */

import { Link } from 'react-router-dom';
import { Bot, TriangleAlert } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ROUTES } from '@/routing/routes';
import type { AiSearchAvailability } from '@/types/ai-search.types';

/** Why the agent is off, in Spanish. Falls back to a neutral phrase for an unknown code. */
const UNAVAILABLE_REASONS: Record<string, string> = {
  switched_off: 'El agente está desactivado en esta tienda',
};

export function agentUnavailableText(reason?: string | null): string {
  if (!reason) return 'El agente no está disponible ahora mismo';
  return UNAVAILABLE_REASONS[reason] ?? 'El agente no está disponible ahora mismo';
}

/**
 * The three states of the gate, named so the card renders a value rather than a chain of
 * conditions — which is how the second and third state get confused.
 */
export type AgentGateState = 'available' | 'unavailable' | 'unknown';

/**
 * What the probe said about the agent.
 *
 * `agentAvailable` is optional on the wire so that a response from a backend predating C42 leaves it
 * undefined. **Undefined is «the probe did not say», which is the third state and not the second**:
 * treating a missing field as false would close the door on every deployment that had not been
 * updated yet, which is the opposite of what the third state is for.
 */
export function agentGateState(
  availability: AiSearchAvailability | null,
  settled: boolean,
): AgentGateState {
  if (!settled || availability === null) return 'unknown';
  if (availability.agentAvailable === undefined) return 'unknown';
  return availability.agentAvailable ? 'available' : 'unavailable';
}

interface AgentEntryCardProps {
  /** Null while the probe is still in flight, or when it could not be read at all. */
  availability: AiSearchAvailability | null;
  /** True once the read has settled, however it settled. */
  settled: boolean;
}

export function AgentEntryCard({ availability, settled }: AgentEntryCardProps) {
  const state = agentGateState(availability, settled);
  const disabled = state === 'unavailable';

  const body = (
    <>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          Preguntar al Agente
        </CardTitle>
        <CardDescription>
          Conversa con el agente: busca, consulta existencias y propone alternativas por su cuenta
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div className="space-y-1 text-sm text-muted-foreground">
            <p>• Varios turnos sobre la misma conversación</p>
            <p>• Enseña qué ha consultado y por qué ha parado</p>
            <p>• Más lento y más caro que buscar con ayuda</p>
          </div>
          <Bot className="h-12 w-12 text-muted-foreground/50" />
        </div>

        {/* The reason, stated on the card rather than discovered by pressing it. */}
        {disabled && (
          <p
            role="status"
            className="mt-4 flex items-start gap-2 text-sm text-muted-foreground"
          >
            <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            {agentUnavailableText(availability?.agentUnavailableReason)}
          </p>
        )}

        {/* Active, with the warning. A probe that cannot answer never closes the door. */}
        {state === 'unknown' && settled && (
          <p
            role="status"
            className="mt-4 flex items-start gap-2 text-sm text-muted-foreground"
          >
            <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            No se pudo confirmar si el agente está disponible
          </p>
        )}

        <Button className="mt-4 w-full" disabled={disabled}>
          Preguntar al Agente
        </Button>
      </CardContent>
    </>
  );

  if (disabled) {
    // No link at all rather than a disabled-looking link that still navigates: a card whose button
    // is greyed out and whose surface is still clickable is the shape of bug this card exists for.
    return (
      <Card aria-disabled="true" className="opacity-60">
        {body}
      </Card>
    );
  }

  return (
    <Card className="cursor-pointer transition-shadow hover:shadow-lg">
      <Link to={ROUTES.SALES.NEW_AGENT}>{body}</Link>
    </Card>
  );
}

export default AgentEntryCard;
