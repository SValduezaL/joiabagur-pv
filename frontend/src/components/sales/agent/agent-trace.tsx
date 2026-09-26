/**
 * The loop's trace, as a ladder of steps. C42.
 *
 * **The only thing on screen that distinguishes an agent from a single prompt.** The same question
 * asked in the deterministic panel comes back in one pass; here it comes back with the steps that
 * produced it, so the trace is what makes the ablation visible instead of asserted.
 *
 * **It carries no tool argument and no observation content, by rule rather than by omission.** The
 * contract excludes both: the arguments are the operator's question as the model reformulated it,
 * which the service's no-persistence rule keeps out of durable storage, and the observations are the
 * evidence that already travels as groups and citations. There is nothing here to render that
 * should not be rendered — which is why this component cannot leak either even if somebody tried.
 *
 * Collapsed by default, with the number of iterations visible in the block's status strip: the
 * operator's job is to sell, and the ladder is what they open when the answer surprises them.
 */

import { ChevronDown, Check, X } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import type { AgentTraceIteration } from '@/types/ai-agent.types';

/**
 * Why an observation failed, in Spanish: the five values of `TOOL_FAILURE_CAUSES`.
 *
 * An unrecognised cause shows **raw** rather than blank — visible and ugly beats invisible, because
 * a code on screen is a bug report and a blank is a failure the operator never sees.
 */
const TOOL_CAUSE_COPY: Record<string, string> = {
  argumento_invalido: 'petición mal formada',
  referencia_desconocida: 'referencia desconocida',
  referencia_no_utilizable: 'referencia no utilizable',
  dependencia_no_disponible: 'dependencia caída',
  presupuesto_agotado: 'sin presupuesto',
};

export function toolCauseText(cause?: string | null): string {
  if (!cause) return 'falló';
  return TOOL_CAUSE_COPY[cause] ?? cause;
}

interface AgentTraceProps {
  trace: readonly AgentTraceIteration[];
}

export function AgentTrace({ trace }: AgentTraceProps) {
  // No loop ran, so there is no ladder. Rendering an empty section would read as a fault, and this
  // state is real: a deployment with no agent credential reports zero iterations.
  if (trace.length === 0) return null;

  return (
    <Collapsible data-testid="agent-trace" className="rounded-md border">
      <CollapsibleTrigger className="flex w-full items-center gap-2 p-3 text-start text-sm hover:bg-muted/50">
        <ChevronDown className="h-4 w-4 shrink-0" aria-hidden="true" />
        <span>Cómo lo ha averiguado</span>
        <Badge variant="secondary" className="ml-auto">
          {trace.length} {trace.length === 1 ? 'vuelta' : 'vueltas'}
        </Badge>
      </CollapsibleTrigger>

      <CollapsibleContent>
        <ol className="space-y-2 border-t p-3 text-sm">
          {trace.map((iteration) => (
            <li
              key={iteration.iteration}
              data-testid="agent-trace-step"
              className="flex flex-col gap-1"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium">Vuelta {iteration.iteration}</span>

                {/* A turn that asked for no tool is a real step: it is the one where the model
                    decided it had enough, which is what `sin_mas_herramientas` means. */}
                {iteration.tools.length === 0 ? (
                  <span className="text-muted-foreground">sin consultas</span>
                ) : (
                  iteration.tools.map((tool, index) => (
                    <Badge
                      key={`${iteration.iteration}-${tool.tool}-${index}`}
                      data-testid="agent-trace-tool"
                      variant={tool.ok ? 'secondary' : 'destructive'}
                      className="gap-1 font-mono text-xs"
                    >
                      {tool.ok ? (
                        <Check className="h-3 w-3" aria-hidden="true" />
                      ) : (
                        <X className="h-3 w-3" aria-hidden="true" />
                      )}
                      {tool.tool}
                      {!tool.ok && <span>· {toolCauseText(tool.cause)}</span>}
                    </Badge>
                  ))
                )}
              </div>

              {/* What the step cost. Tokens and milliseconds, never euros: a tariff written into a
                  screen is wrong the day the provider moves it. */}
              <span className="text-xs text-muted-foreground">
                {iteration.totalTokens.toLocaleString('es-ES')} tokens ·{' '}
                {Math.round(iteration.elapsedMs).toLocaleString('es-ES')} ms
              </span>
            </li>
          ))}
        </ol>
      </CollapsibleContent>
    </Collapsible>
  );
}

export default AgentTrace;
