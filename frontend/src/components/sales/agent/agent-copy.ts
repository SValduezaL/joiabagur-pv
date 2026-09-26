/**
 * The Spanish the agent panel reads from. C42.
 *
 * **Every phrase comes from a reported value and none from a counter.** The service publishes ten
 * stop reasons in a closed vocabulary, and a count of iterations does not say whether the last one
 * was the last needed or the one that ran out — those are opposite claims about the answer on
 * screen. So the statement is looked up here and never computed there.
 *
 * A value this table does not recognise falls back to a **neutral** phrase rather than to a guess or
 * to a blank. A blank would leave the strip saying nothing about an answer that may be incomplete;
 * a guess would say something false about one that is not.
 */

/**
 * The ten values of `AGENT_STOP_REASONS`, each with what the operator reads.
 *
 * Kept as a flat table rather than as branches, so the test that walks all ten is a walk over this
 * object and a value added on the service side shows up here as a missing key rather than as a
 * silently wrong sentence.
 */
export const STOP_REASON_COPY: Record<string, string> = {
  /** The model stopped asking for tools. The ordinary, complete ending. */
  sin_mas_herramientas: 'Respuesta completa',
  /** The five budgets. Each names what ran out, because «incompleta» alone explains nothing. */
  presupuesto_iteraciones: 'Respuesta incompleta: se agotaron las vueltas de búsqueda',
  presupuesto_tools: 'Respuesta incompleta: se agotaron las consultas al catálogo',
  presupuesto_tokens: 'Respuesta incompleta: se agotó el presupuesto de texto',
  presupuesto_contexto: 'Respuesta incompleta: la conversación acumulada llegó a su tope',
  presupuesto_reloj: 'Respuesta incompleta: se agotó el tiempo de búsqueda',
  /** Not an incompleteness: the agent needs one more thing to search with. */
  aclaracion: 'Falta un dato para poder buscar',
  /** A complete answer to a request this shop will not serve. */
  rechazado: 'Consulta fuera de lo que esta tienda atiende',
  /** No agent credential configured: the fail-open, the ablation and the rollback in one. */
  sin_cliente: 'El agente no está configurado en este entorno',
  /** The turn died in the provider. Whatever earlier turns gathered is still served. */
  fallo_proveedor: 'El proveedor de IA falló a mitad de la búsqueda',
};

/** The neutral phrase for a value this frontend does not recognise. */
export const UNKNOWN_STOP_REASON = 'El agente terminó por un motivo que esta pantalla no reconoce';

/**
 * What the strip says about why the loop stopped.
 *
 * **Takes the reported value alone.** Passing the counters in would reintroduce exactly what the
 * contract forbids deriving.
 */
export function stopReasonText(stopReason?: string | null): string {
  if (!stopReason) return UNKNOWN_STOP_REASON;
  return STOP_REASON_COPY[stopReason] ?? UNKNOWN_STOP_REASON;
}

/**
 * The five budget reasons, so «this answer was cut short» is a membership test rather than a list
 * restated at each site. Mirrors `AGENT_BUDGET_STOP_REASONS` on the service side.
 */
export const BUDGET_STOP_REASONS = [
  'presupuesto_iteraciones',
  'presupuesto_tools',
  'presupuesto_tokens',
  'presupuesto_contexto',
  'presupuesto_reloj',
] as const;

/** Whether a budget is what ended this answer, which is what the incompleteness ribbon renders. */
export function isBudgetStop(stopReason?: string | null): boolean {
  return !!stopReason && (BUDGET_STOP_REASONS as readonly string[]).includes(stopReason);
}

/**
 * Why the whole AI path degraded, in Spanish. The free query's vocabulary, reused rather than
 * reworded: the same situation with a sixth word would be a second thing to translate.
 */
export const DEGRADED_REASON_COPY: Record<string, string> = {
  switched_off: 'El agente está desactivado en esta tienda',
  credential_rejected: 'El servicio de IA rechazó las credenciales',
  not_implemented: 'El agente no está implementado en este entorno',
  not_indexed: 'El servicio de IA no pudo procesar la conversación',
  ai_unavailable: 'El servicio de IA no está disponible ahora mismo',
  unclassified: 'El servicio de IA falló por un motivo sin clasificar',
};

export function degradedReasonText(reason?: string | null): string {
  if (!reason) return 'El agente no está disponible ahora mismo';
  return DEGRADED_REASON_COPY[reason] ?? 'El agente no está disponible ahora mismo';
}

/**
 * Warning codes **about the conversation**, never about a piece.
 *
 * Measured at **3.9 %** of responses, so this is the exception and not the normal case — which is
 * why the block renders nothing at all when the list is empty rather than showing an empty section.
 */
export const AGENT_WARNING_COPY: Record<string, string> = {
  query_out_of_domain: 'Lo que se pregunta no es de este negocio',
  query_not_in_catalogue: 'Es joyería, pero este catálogo no la tiene',
  knowledge_not_covered: 'La documentación de la casa no cubre esta pregunta',
  filters_too_narrow: 'Los filtros dejaron muy pocas piezas para elegir',
};

export function agentWarningText(code: string): string {
  return AGENT_WARNING_COPY[code] ?? code;
}

/** The two provenance labels. The whole reason the marker travels to the browser. */
export const ORIGIN_COPY: Record<string, string> = {
  catalogo: 'Coincidencias',
  sustitutos: 'Alternativas',
};

/**
 * What a group's heading says.
 *
 * `sustitutos` reads **«Alternativas»** and not «Sustitutos», deliberately: it is what the operator
 * says out loud to a customer. What it must never read is «Coincidencias», because offering a
 * second best as though it were what was asked for is what makes somebody stop trusting the counter.
 */
export function originText(origin?: string | null): string {
  if (!origin) return 'Piezas';
  return ORIGIN_COPY[origin] ?? 'Piezas';
}

/** The failure outcomes of a turn, which are not answers and need their own words. */
export const FAILURE_COPY = {
  'rate-limited':
    'Has agotado los turnos de este minuto. El agente gasta mucho texto, así que espera un momento '
    + 'antes de volver a preguntar.',
  forbidden: 'No tienes acceso a la tienda por la que preguntas.',
  error: 'No se pudo contestar el turno.',
} as const;
