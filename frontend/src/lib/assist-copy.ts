/**
 * Sale Card Copy Table (EP15 / C36)
 *
 * The backend sends codes; the Spanish a human reads is written here. That split is the rule the
 * assisted search panel's living spec already states for the retriever's match reasons, and the
 * AI service's own vocabulary module states it back from the other side: *"codes on the wire and
 * copy in the presentation layer"*.
 *
 * A module of its own, exported and tested directly, following `ORIGIN_LABELS`/`originLabel` of
 * C16 — not literals scattered through the components. The reason is not tidiness: the warning
 * vocabulary is **closed but versioned**, and a neutral fallback for a value this screen does not
 * know is the only thing standing between a new version of the service and a broken row.
 */

import type { PitchStatus, SubstitutesOutcome } from '@/types/sales-assist.types';

/* -------------------------------------------------------------------------------------------
 * Warnings
 * ---------------------------------------------------------------------------------------- */

/**
 * The missing-size-label code, named because the card treats it differently from every other
 * warning: it is rendered as an attribute of the piece beside its SKU and never as an alert.
 *
 * It fires on **58,3 %** of cards and is almost perfectly anti-correlated with belonging to a
 * family — **4,0 %** with one against **92,5 %** without one — so it states the enrichment status
 * of the catalog rather than a fact about the piece in front of the customer. Rendered as an
 * alert it would crowd out `stock_critical`, which fires on 3,9 % and is the one that can cost a
 * sale.
 *
 * It is **never suppressed**: the frontend does not remove a code the backend emitted.
 */
export const SIZE_LABEL_MISSING = 'size_label_missing';

/**
 * The Spanish for each warning code the assistance routes can emit.
 *
 * **The two router refusal codes gained a row in C40, and until then their absence was correct.**
 * C36 left `query_out_of_domain` and `query_not_in_catalogue` without one on the reasoning that
 * the intent classifier runs only in the free-query mode, and that mode had no screen — so both
 * were unreachable, and writing their Spanish would have bought two green tests over impossible
 * paths. C40 gives that mode a screen, which makes them reachable and makes the copy owed.
 *
 * A lookup rather than a conditional, so a code added by a later version of the service is a new
 * entry here instead of a change to a component.
 */
const WARNING_LABELS: Record<string, string> = {
  family_has_variants: 'Esta pieza tiene otras variantes en esta tienda',
  stock_critical: 'Quedan pocas unidades',
  family_members_out_of_stock: 'Alguna variante de la familia está agotada aquí',
  knowledge_not_covered: 'La documentación no cubre esta pregunta',
  [SIZE_LABEL_MISSING]: 'Sin talla declarada',

  // --- the query's own warnings, reachable since C40 -------------------------------------

  // **Two refusals, two texts, and the distinction is the point.** What an operator says to a
  // customer differs between a trade the shop does not practise and a piece it does not carry,
  // and the AI service emits two codes precisely so the two rates stay separable. Collapsing
  // them into one sentence here would throw away on the screen the distinction the service went
  // to the trouble of making on the wire.
  query_out_of_domain: 'Esto no es una pregunta de joyería',
  query_not_in_catalogue: 'No trabajamos ese tipo de pieza',

  // Neither of the two above is an abstention, which means something else: that the catalogue
  // was searched and nothing matched.
  filters_too_narrow: 'Hay piezas que encajan con tu descripción, pero ninguna pasa los filtros',
};

/**
 * Codes whose subject is **the query** rather than a piece.
 *
 * The partition is by subject and not by list, because the AI service stacks both kinds into one
 * array. A warning about a piece describes the *first member of the first group*, so painting it
 * above a list of fifteen results would state something false about fourteen of them — measured,
 * on a set of fifteen pieces carrying `family_has_variants` and `size_label_missing` for a SKU
 * whose visible group had a single member.
 *
 * The backend already filters to these before sending, and the screen filters again. That is
 * deliberate rather than redundant: the rule is a property of what may be shown, and a screen
 * that trusted the payload would render whatever a later version of the service decides to stack
 * into that array.
 */
export const QUERY_WARNING_CODES: readonly string[] = [
  'query_out_of_domain',
  'query_not_in_catalogue',
  'knowledge_not_covered',
  'filters_too_narrow',
];

/**
 * Whether a warning code describes the query, and may therefore be shown above the results.
 *
 * An **allow-list**, not a deny-list: a code this version does not know is treated as being about
 * a piece and stays off the screen. The other way round, a code added later would leak onto a
 * banner by default, and the failure mode of that is a false statement about every result under
 * it.
 */
export function isQueryWarning(code: string): boolean {
  return QUERY_WARNING_CODES.includes(code);
}

/**
 * The warnings a free-query result list may show, from whatever the service sent.
 */
export function queryWarnings(warnings: readonly string[]): string[] {
  return warnings.filter(isQueryWarning);
}

/**
 * The label for a code this screen does not know.
 *
 * Neutral on purpose: it says that something was flagged without inventing what, which is the
 * honest thing to say about a value whose meaning this version does not hold. The raw code is
 * never shown — it is engineering vocabulary and means nothing at a counter.
 */
export const UNKNOWN_WARNING_LABEL = 'Aviso del catálogo';

/** The Spanish for a warning code, degrading to the neutral label rather than failing. */
export function warningLabel(code: string): string {
  return WARNING_LABELS[code] ?? UNKNOWN_WARNING_LABEL;
}

/** Whether this screen holds a translation for a code, for the tests that assert the fallback. */
export function isKnownWarning(code: string): boolean {
  return code in WARNING_LABELS;
}

/**
 * The warnings that belong in the alert block: everything the backend emitted except the
 * missing-size-label code, which the header renders as an attribute of the piece.
 *
 * The order is the one received. Nothing is added and nothing is removed.
 */
export function alertWarnings(warnings: readonly string[]): string[] {
  return warnings.filter((code) => code !== SIZE_LABEL_MISSING);
}

/* -------------------------------------------------------------------------------------------
 * The state of the argument
 * ---------------------------------------------------------------------------------------- */

/**
 * What the card says about an argument it was not given.
 *
 * `action` is never empty. A message that only states an absence is a dead end for someone
 * standing at a counter with a customer; an honest abstention says what would be needed to get
 * past it.
 */
export interface PitchMessage {
  /** The state itself, so two states that share a text stay distinguishable in the document. */
  status: PitchStatus;
  title: string;
  body: string;
  /** What to do next. */
  action: string;
}

/**
 * Six states, five renderings: `generated` paints the argument, and the other five share four
 * texts between them.
 *
 * **`ai_unavailable` and `not_generated` do not share a message**, however similar they sound.
 * In the first, half the screen is pure catalog — no citations, no match reasons, and the family
 * read from the transactional catalog rather than from the index. In the second the piece's data
 * is the index's, intact. One message for both would make the card misstate where what it is
 * showing came from, which is the one thing the screen must never do.
 *
 * **The two withheld states do share a message**, because nothing the operator can do differs
 * between them. They remain distinguishable in the document through `status`.
 */
const PITCH_MESSAGES: Record<Exclude<PitchStatus, 'generated'>, Omit<PitchMessage, 'status'>> = {
  ai_unavailable: {
    title: 'El asistente no está disponible',
    body: 'Lo que ves viene del catálogo: el precio, las unidades y las variantes son reales, pero no hay argumentario ni fuentes.',
    action: 'Puedes vender con estos datos, o volver a pedir la ficha en un momento.',
  },
  not_generated: {
    title: 'El argumentario no se ha generado',
    body: 'Los datos de la pieza son los del índice y están completos; sólo falta el texto.',
    action: 'Vuelve a pedir la ficha, o pregunta algo concreto sobre la pieza.',
  },
  withheld_by_ai: {
    title: 'Sin argumentario para esta pieza',
    body: 'No he podido redactar algo que pueda sostener con los datos de esta pieza.',
    action: 'Pregunta algo concreto sobre ella y te contesto con las fuentes que tenga.',
  },
  withheld_unresolved: {
    title: 'Sin argumentario para esta pieza',
    body: 'No he podido redactar algo que pueda sostener con los datos de esta pieza.',
    action: 'Pregunta algo concreto sobre ella y te contesto con las fuentes que tenga.',
  },
  withheld_out_of_stock: {
    title: 'Esta pieza está agotada aquí',
    body: 'No redacto un argumentario de algo que no puedes vender hoy en esta tienda.',
    action: 'Te propongo alternativas que sí están disponibles.',
  },
};

/**
 * What to say about the state of the argument, or `null` when there is an argument to paint.
 *
 * An unknown state is treated as one without an argument rather than assumed to be `generated`:
 * claiming a text was delivered when the card does not know what happened would be the worse of
 * the two errors.
 */
/**
 * A piece the AI service could not process, which is not an outage (C40).
 *
 * It is the state of a piece added after the last index synchronisation — one the next
 * synchronisation fixes by itself, with nobody doing anything. Until the backend began reporting
 * why it degraded, this arrived looking exactly like a service that had fallen over, so the one
 * useful thing an operator could know — wait, or sell from the catalog and stop worrying — was
 * the one thing the screen could not say.
 */
const PRODUCT_NOT_INDEXED: Omit<PitchMessage, 'status'> = {
  title: 'Esta pieza todavía no está preparada',
  body: 'Es una pieza reciente y el asistente aún no la ha procesado. El precio, las unidades y las variantes que ves son reales y vienen del catálogo.',
  action: 'Puedes vender con estos datos. Estará lista sin que tengas que hacer nada.',
};

export function pitchMessage(status: PitchStatus, degradedReason?: string | null): PitchMessage | null {
  if (status === 'generated') return null;

  // Only refines the outage message, and only for this one reason. The other five — a switch, a
  // rejected credential, an unimplemented route, a genuine outage, an unclassified failure — all
  // mean the same thing to whoever is standing at the counter: the assistant is not answering.
  // This one does not, because it resolves itself and needs no action at all.
  if (status === 'ai_unavailable' && degradedReason === 'product_not_indexed') {
    return { status, ...PRODUCT_NOT_INDEXED };
  }

  const message = PITCH_MESSAGES[status as Exclude<PitchStatus, 'generated'>];
  if (!message) {
    return {
      status,
      title: 'Sin argumentario para esta pieza',
      body: 'No hay un texto que pueda enseñarte para esta pieza.',
      action: 'Los datos de la pieza que ves son reales; pregunta algo concreto si lo necesitas.',
    };
  }
  return { status, ...message };
}

/** Whether the citations are the sources of a text the operator can actually read. */
export function showsCitations(status: PitchStatus): boolean {
  return status === 'generated';
}

/* -------------------------------------------------------------------------------------------
 * Citations
 * ---------------------------------------------------------------------------------------- */

/** The scope value that marks a claim as a commitment of the house rather than a fact. */
export const ESTABLISHMENT_SCOPE = 'establecimiento';

/** Whether a citation states a commitment of the establishment. */
export function isEstablishmentClaim(claimScope: string): boolean {
  return claimScope === ESTABLISHMENT_SCOPE;
}

/**
 * The badge for a citation's scope.
 *
 * A commitment of the house and a fact of the world are not the same kind of claim, and passing
 * the first to a customer as if it were the second is how a shop ends up owing something it
 * never promised.
 */
export function claimScopeLabel(claimScope: string): string {
  return isEstablishmentClaim(claimScope) ? 'Compromiso de la casa' : 'Información general';
}

/** The sentence an establishment-scope citation carries, and a general one does not. */
export const ESTABLISHMENT_CLAIM_NOTE =
  'Conviene confirmarlo en tienda antes de trasladárselo a un cliente.';

/**
 * What to say when an argument arrived with no citation the gate could verify.
 *
 * **A discreet line, never an alert**, and the wording is load-bearing. The integrity gate
 * withdraws a citation whose supporting span it cannot match — measured in the free-query mode at
 * 26.4 % of declared citations, leaving 24.3 % of knowledge answers with none at all, roughly
 * twice the anchored rate. At that frequency an alert would train an operator to ignore it.
 *
 * And it must **not insinuate an invention**. The citation existed; what could not be verified is
 * the span that was supposed to support it. Saying "this may be made up" about a case that is
 * usually a paraphrase would be both false and corrosive to the one thing the gate is for.
 */
export const NO_VERIFIABLE_SOURCE =
  'Sin fuente verificable para este texto';

/* -------------------------------------------------------------------------------------------
 * The two states with no route (C40)
 * ---------------------------------------------------------------------------------------- */

/**
 * `route=none` is **two states**, and only `intent` tells them apart.
 *
 * Both arrive with results and without an argument, and they look identical on the wire except
 * for that one field — which is exactly why this lives in a named function instead of a ternary
 * inside a component.
 *
 * The distinction is not cosmetic. With `in_domain` the classifier ran and contradicted itself:
 * it admitted the query and then declined to say which index answers it, so asking the operator
 * to put it another way is fair. With `unclassified` the classifier **never ran** — no
 * credential, a two-second timeout with no retry, or a reply that did not parse — and asking
 * them to rephrase would be blaming them for an absent credential. It is not a theoretical path
 * either: with the router's credential missing, *every* query lands there.
 */
export interface NoRouteMessage {
  title: string;
  body: string;
  /** Null when there is nothing useful for the operator to do. */
  action: string | null;
}

export function noRouteMessage(intent: string | null | undefined): NoRouteMessage {
  if (intent === 'unclassified') {
    return {
      title: 'El argumentario no está disponible ahora mismo',
      body: 'Los resultados son reales y puedes trabajar con ellos; lo que falta es el texto.',
      // Deliberately null: the operator did nothing wrong and there is nothing they can do.
      action: null,
    };
  }

  return {
    title: 'No he acabado de entender la consulta',
    body: 'Te enseño lo que he encontrado, pero no he sabido redactar un argumentario sobre ello.',
    action: 'Prueba a formularla de otra manera.',
  };
}

/**
 * Whether the operator should be invited to rephrase.
 *
 * Exported on its own because it is the assertion a test can make directly, and because the
 * negative case is the one that matters: inviting a rephrase when the classifier never ran is
 * the screen blaming a person for a configuration.
 */
export function invitesRephrasing(intent: string | null | undefined): boolean {
  return noRouteMessage(intent).action !== null;
}

/* -------------------------------------------------------------------------------------------
 * Substitutes
 * ---------------------------------------------------------------------------------------- */

/** What the card says about how a substitutes request ended. */
export interface SubstitutesMessage {
  outcome: SubstitutesOutcome;
  title: string;
  body: string;
}

/**
 * Four outcomes, four texts.
 *
 * `product_not_indexed` is **never** painted as an outage. It is a state of the catalog that the
 * next synchronisation fixes, and telling the operator the assistant is down would send them
 * chasing a problem that does not exist.
 */
const SUBSTITUTE_MESSAGES: Record<SubstitutesOutcome, Omit<SubstitutesMessage, 'outcome'>> = {
  ok: {
    title: 'Alternativas disponibles hoy',
    body: 'Piezas parecidas que esta tienda puede vender ahora mismo.',
  },
  none_in_stock: {
    title: 'Ninguna alternativa disponible hoy',
    body: 'He buscado piezas parecidas, pero ninguna tiene unidades en esta tienda.',
  },
  product_not_indexed: {
    title: 'Esta pieza aún no está preparada',
    body: 'Todavía no puedo buscarle alternativas parecidas. Se resuelve solo en la próxima sincronización del catálogo.',
  },
  ai_unavailable: {
    title: 'No he podido buscar alternativas',
    body: 'El asistente no está disponible en este momento.',
  },
};

/** What to say about a substitutes outcome, degrading rather than failing on an unknown one. */
export function substitutesMessage(outcome: SubstitutesOutcome): SubstitutesMessage {
  const message = SUBSTITUTE_MESSAGES[outcome];
  if (!message) {
    return {
      outcome,
      title: 'No he podido buscar alternativas',
      body: 'No hay alternativas que enseñarte para esta pieza.',
    };
  }
  return { outcome, ...message };
}

/**
 * Why no substitutes were asked for at all.
 *
 * Not one of the four outcomes: the request was never issued. With the AI path unavailable it
 * would come back `ai_unavailable` with certainty, so it is more honest to say so than to spend
 * it — but saying nothing would read as a piece with no alternatives, which is a different and
 * false claim.
 */
export const SUBSTITUTES_NOT_REQUESTED =
  'No busco alternativas porque el asistente no está disponible para esta ficha.';

/* -------------------------------------------------------------------------------------------
 * The question box
 * ---------------------------------------------------------------------------------------- */

/**
 * The five suggested questions, drawn from the counter situations the knowledge corpus covers:
 * wetting the piece, sensitive skin, cleaning it at home, a gift with no known size, and the
 * beach or the pool.
 *
 * Baking them into the interface is the remedy S4 prescribes — *"what to ask can be baked into
 * the interface"* — with a reason of its own that was measured rather than assumed: **9 of 40**
 * real counter questions fell into `knowledge_not_covered`, and showing what the corpus does
 * answer raises that coverage as well as being easier to use.
 *
 * Each maps onto a document that exists: `cuidados-generales`, `niquel-y-piel-sensible`,
 * `regalar-sin-saber-la-talla` and `joyas-playa-piscina-y-deporte`.
 */
export const SUGGESTED_QUESTIONS: readonly string[] = [
  '¿Se puede mojar esta pieza?',
  '¿Va bien para una piel sensible?',
  '¿Cómo se limpia en casa?',
  'Es un regalo y no sé la talla, ¿qué hago?',
  '¿Se puede llevar a la playa o a la piscina?',
] as const;

/** What the operator is told when the question is longer than the contract allows. */
export function questionTooLongMessage(max: number): string {
  return `La pregunta es demasiado larga: como mucho ${max} caracteres.`;
}

/**
 * The six causes of degradation, named for a **diagnostic** reader and never for an operator.
 *
 * Two vocabularies over one field, on purpose. `pitchMessage` above turns a cause into what the
 * operator should *do*, and it deliberately collapses several of them: «el asistente no está
 * disponible» is the right sentence for a rejected credential and for an outage alike, because
 * the operator's next move is the same. This table keeps them apart, because the administrator's
 * next move is not: one is a configuration, one is a provider, one is an unindexed piece.
 *
 * Closed, and an unknown code falls back to itself rather than to a guess — a cause this table
 * has not learnt yet is more useful shown raw than translated into the nearest familiar one.
 */
const DEGRADED_REASONS: Record<string, string> = {
  switched_off: 'interruptor apagado',
  credential_rejected: 'credencial rechazada',
  not_implemented: 'ruta no implementada',
  not_indexed: 'pieza no indexada',
  ai_unavailable: 'servicio de IA no disponible',
  unclassified: 'fallo sin clasificar',
};

export function degradedReasonLabel(reason: string): string {
  return DEGRADED_REASONS[reason] ?? reason;
}

/** The causes this screen knows how to name. Read by a test that asserts the list is closed. */
export const DEGRADED_REASON_CODES = Object.keys(DEGRADED_REASONS);

/* -------------------------------------------------------------------------------------------
 * The same states, on the free-query panel
 * ---------------------------------------------------------------------------------------- */

/**
 * What to say about a missing argument **on the free-query panel**, which is not the card.
 *
 * **Found by the real-data check of C40, not by a test.** `PITCH_MESSAGES` above is written for
 * the sale card and every one of its five entries says so: «volver a pedir *la ficha*», «*esta
 * pieza*», «te propongo alternativas». On the assisted panel there is no ficha — nobody asked for
 * one — and there is no single piece: there are several results grouped by family. Reusing the
 * card's copy there named two things that do not exist on the screen showing it.
 *
 * The card's table is left exactly as it is. C36 measured and worded it for its own surface, and
 * a shared sentence that has to serve two surfaces ends up serving neither.
 *
 * **`not_generated` carries no action, deliberately.** The sixteen-state table prescribes for the
 * degraded-router state *«ninguna acción del operario — no se le pide reformular»*: the classifier
 * timed out or was never configured, and asking the operator to do something about it would blame
 * them for an outage. The two states share this status and neither admits an action.
 */
const FREE_QUERY_PITCH_MESSAGES: Record<
  Exclude<PitchStatus, 'generated'>,
  Omit<PitchMessage, 'status'> | null
> = {
  ai_unavailable: {
    title: 'La respuesta asistida no está disponible',
    body: 'Los precios, las unidades y las variantes que ves son reales; lo que falta es el texto y sus fuentes.',
    action: 'Puedes usar la búsqueda rápida, que no necesita el asistente.',
  },
  not_generated: {
    title: 'No he podido preparar el texto',
    body: 'Las piezas y sus datos son los del índice y están completos; sólo falta el argumentario.',
    action: '',
  },
  withheld_by_ai: {
    title: 'Sin argumentario para esta búsqueda',
    body: 'No he podido redactar algo que pueda sostener con las fuentes que tengo.',
    action: 'Las piezas de abajo son reales; prueba a preguntar algo más concreto.',
  },
  // Anchored-mode statuses. They need a piece on the screen, and this route has none — no request
  // of this panel can produce them. Mapped to null rather than to a plausible sentence, so that if
  // one ever arrives it renders nothing instead of a paragraph about a piece that is not there.
  withheld_unresolved: null,
  withheld_out_of_stock: null,
};

export function freeQueryPitchMessage(
  status: PitchStatus,
  degradedReason?: string | null,
): PitchMessage | null {
  if (status === 'generated') return null;

  const message = FREE_QUERY_PITCH_MESSAGES[status as Exclude<PitchStatus, 'generated'>];
  if (!message) return null;

  // The one reason that refines the outage message, kept in step with the card's rule: it
  // resolves itself and needs no action, so it must not read as a failure of the assistant.
  if (status === 'ai_unavailable' && degradedReason === 'product_not_indexed') {
    return { status, ...PRODUCT_NOT_INDEXED };
  }

  return { status, ...message };
}
