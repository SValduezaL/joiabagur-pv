/**
 * The sale agent's panel. C42.
 *
 * **The fourth way of starting a sale, on a route of its own.** Not a toggle inside the assisted
 * panel: that panel is one query producing one set of results, this is a conversation, and it already
 * carries a toggle with a different meaning — the degraded path against the generative one. Two
 * controls of similar name and different meaning on one screen is the failure the free-query panel
 * was built to remove.
 *
 * **The thread is the axis.** Every answer is a block anchored to the turn that produced it, and only
 * the last one is open. A single results area refreshed on each turn leaves the operator reading one
 * turn's argument while the rows beneath already belong to the next — and when the loop pivots to
 * substitutes, the piece being looked at disappears with no explanation. That pivot is exactly what
 * this panel exists to show: the substitutes tool was invoked 125 times in the measured pass.
 *
 * **Pieces repeat across turns and are never de-duplicated between them**, because each turn's
 * evidence is its own: a piece that survived a second search is a stronger recommendation, not a
 * duplicate row.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Bot, ChevronDown, TriangleAlert } from 'lucide-react';
import { toast } from 'sonner';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AgentAnswerBlock } from '@/components/sales/agent/agent-answer-block';
import { AgentComposer } from '@/components/sales/agent/agent-composer';
import { FAILURE_COPY, degradedReasonText } from '@/components/sales/agent/agent-copy';
import {
  AgentSessionCostBar,
  EMPTY_SESSION_COST,
  accrue,
} from '@/components/sales/agent/agent-session-cost';
import {
  buildTranscript,
  countTranscript,
} from '@/components/sales/agent/agent-transcript';
import { useAuth } from '@/providers/auth-provider';
import { ROUTES } from '@/routing/routes';
import { agentAssistService } from '@/services/agent-assist.service';
import { aiSearchService } from '@/services/ai-search.service';
import * as pointOfSaleService from '@/services/point-of-sale.service';
import type { AgentExchange, AgentSessionCost } from '@/types/ai-agent.types';
import type { AiSearchAvailability, AssistedSearchResult } from '@/types/ai-search.types';
import type { PointOfSale } from '@/types/point-of-sale.types';

/**
 * The sentinel of the shop selector, exactly as the sibling panel spells it.
 *
 * It stops being a value at `scopedPointOfSaleId` below and never travels: the route reads the field
 * not being there as the wider scope and refuses a blank one.
 */
const ALL_POINTS_OF_SALE = '__all__';

export function AgentSalesPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.role === 'Administrator';

  const [pointsOfSale, setPointsOfSale] = useState<PointOfSale[]>([]);
  const [loadingPos, setLoadingPos] = useState(true);
  const [pointOfSaleId, setPointOfSaleId] = useState<string>('');

  const [availability, setAvailability] = useState<AiSearchAvailability | null>(null);
  const [availabilitySettled, setAvailabilitySettled] = useState(false);

  const [exchanges, setExchanges] = useState<AgentExchange[]>([]);
  const [draft, setDraft] = useState('');
  const [pending, setPending] = useState(false);
  const [openBlockId, setOpenBlockId] = useState<string | null>(null);
  const [cost, setCost] = useState<AgentSessionCost>(EMPTY_SESSION_COST);

  /** The visit this conversation belongs to, so a rephrasing is not a new episode. */
  const searchSessionId = useRef(crypto.randomUUID());
  const composerRef = useRef<HTMLDivElement>(null);

  const scopeIsAllPointsOfSale = pointOfSaleId === ALL_POINTS_OF_SALE;

  /** The point of sale as the network sees it: a real identifier, or nothing at all. */
  const scopedPointOfSaleId = scopeIsAllPointsOfSale ? undefined : pointOfSaleId || undefined;

  /**
   * Whether the every-shop scope is on offer.
   *
   * **The sibling panel's rule, copied and not hardened.** Two sibling panels with two different
   * authorisation rules break without any test failing. The backend serves the scope to both roles by
   * its own requirement; what the screen declines to offer an operator is a tool that answers the
   * wrong question at a counter.
   */
  const canScopeToAllPointsOfSale = isAdmin;

  useEffect(() => {
    const load = async () => {
      try {
        const all = await pointOfSaleService.getPointsOfSale();
        // Only active ones: the endpoint refuses an inactive point of sale for every role.
        const active = all.filter((pos) => pos.isActive);
        setPointsOfSale(active);
        if (active.length > 0) setPointOfSaleId(active[0].id);
      } catch {
        toast.error('No se pudieron cargar los puntos de venta');
      } finally {
        setLoadingPos(false);
      }
    };
    load();
  }, []);

  /**
   * Reads the switches for the chosen scope, before anything is asked.
   *
   * Costs no AI call and no quota, which is what makes it safe on every change of shop — and it is
   * the only way the panel can say the agent is off *before* a turn is spent finding out.
   */
  useEffect(() => {
    if (!pointOfSaleId) {
      setAvailability(null);
      setAvailabilitySettled(false);
      return;
    }

    let current = true;
    setAvailabilitySettled(false);

    aiSearchService.getAvailability(scopedPointOfSaleId).then((outcome) => {
      if (!current) return;
      setAvailability(outcome.kind === 'ok' ? outcome.availability : null);
      setAvailabilitySettled(true);
    });

    return () => {
      current = false;
    };
    // `scopedPointOfSaleId` derives from `pointOfSaleId`, so listing the latter describes when this
    // must run without running it twice for one change of scope.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pointOfSaleId]);

  /**
   * The transcript the next turn would send, and its count.
   *
   * **Counted here and not in the composer**, because it is the history that dominates it: the
   * assistant's turns carry the argument back whole, so the count moves when an answer arrives rather
   * than when a key is pressed.
   */
  const transcript = useMemo(() => buildTranscript(exchanges, draft), [exchanges, draft]);
  const count = useMemo(
    // `hasDraft` is what lets the turn cap close one turn early: a turn is indivisible, so with the
    // history already at twelve, any question at all overflows.
    () => countTranscript(transcript, draft.trim().length > 0),
    [transcript, draft],
  );

  /**
   * Changing the shop restarts the thread, **after warning**.
   *
   * The evidence already gathered was gathered in another shop: its prices, its stock and its
   * assortment. Carrying it into a new scope would leave rows on screen that the new shop cannot sell.
   */
  const handlePointOfSaleChange = (value: string) => {
    if (value === pointOfSaleId) return;

    if (exchanges.length > 0) {
      const confirmed = window.confirm(
        'Cambiar de tienda reinicia la conversación: lo que el agente ha encontrado hasta ahora era '
        + 'de la tienda anterior. ¿Seguimos?',
      );
      if (!confirmed) return;

      toast.info('Conversación reiniciada: el ámbito ha cambiado');
    }

    setPointOfSaleId(value);
    setExchanges([]);
    setDraft('');
    setOpenBlockId(null);
    setCost(EMPTY_SESSION_COST);
    searchSessionId.current = crypto.randomUUID();
  };

  const send = useCallback(async () => {
    const question = draft.trim();
    if (!question || !pointOfSaleId || pending) return;

    const id = crypto.randomUUID();
    const turns = buildTranscript(exchanges, question);

    setExchanges((current) => [...current, { id, question, answer: null }]);
    setOpenBlockId(id);
    setDraft('');
    setPending(true);

    const outcome = await agentAssistService.answer({
      turns,
      ...(scopedPointOfSaleId ? { pointOfSaleId: scopedPointOfSaleId } : {}),
      searchSessionId: searchSessionId.current,
    });

    setPending(false);

    if (outcome.kind === 'ok') {
      setExchanges((current) =>
        current.map((exchange) =>
          exchange.id === id ? { ...exchange, answer: outcome.response } : exchange,
        ),
      );
      // Accumulated, never replaced: one turn's cost says nothing about a conversation's.
      setCost((current) => accrue(current, outcome.response.usage));

      // A clarification returns the focus to the composer: the agent asked, and the answer is typed.
      if (outcome.response.clarificationQuestion) {
        composerRef.current?.querySelector('textarea')?.focus();
      }
      return;
    }

    setExchanges((current) =>
      current.map((exchange) =>
        exchange.id === id ? { ...exchange, failure: outcome } : exchange,
      ),
    );
  }, [draft, exchanges, pending, pointOfSaleId, scopedPointOfSaleId]);

  /**
   * Selling from a block reuses the existing sale path and reports the selection.
   *
   * The identifier comes from **the block the row belongs to**, not from the latest answer: only the
   * open block can be sold from, and attributing a selection to a later turn would measure the wrong
   * search.
   */
  const handleSelect = (exchange: AgentExchange) => (result: AssistedSearchResult) => {
    const searchEventId = exchange.answer?.searchEventId ?? undefined;

    // Not awaited: the server stamps the moment, and a telemetry failure must never block a sale.
    if (searchEventId) {
      void aiSearchService.reportSelection(searchEventId, result.productId);
    }

    navigate(ROUTES.SALES.NEW, {
      state: { productId: result.productId, searchEventId },
    });
  };

  const handleOpenCard = (result: AssistedSearchResult) => {
    navigate(ROUTES.SALES.ASSIST(result.productId), { state: { pointOfSaleId } });
  };

  const posName = useMemo(
    () => pointsOfSale.find((pos) => pos.id === pointOfSaleId)?.name ?? '',
    [pointsOfSale, pointOfSaleId],
  );

  const agentOff = availabilitySettled && availability?.agentAvailable === false;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link to={ROUTES.SALES.ROOT} aria-label="Volver a ventas">
            <ArrowLeft className="size-5" />
          </Link>
        </Button>
        <div className="flex-1">
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Bot className="h-6 w-6 text-primary" />
            Preguntar al agente
          </h1>
          <p className="text-muted-foreground">
            Conversa con el agente: busca por su cuenta, consulta existencias y propone alternativas
          </p>
        </div>
        {/* The same question asked in both panels is comparable at a glance, which is the whole
            point of the agent living on a route of its own. */}
        <Button variant="outline" size="sm" asChild>
          <Link to={ROUTES.SALES.NEW_ASSISTED}>Panel directo</Link>
        </Button>
      </div>

      {/* The fixed bar: scope, session cost, and what the wait looks like. */}
      <Card>
        <CardContent className="flex flex-wrap items-center gap-4 p-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Ámbito</span>
            <Select
              value={pointOfSaleId}
              onValueChange={handlePointOfSaleChange}
              disabled={loadingPos}
            >
              <SelectTrigger aria-label="Punto de venta" className="w-[220px]">
                <SelectValue placeholder="Elige una tienda" />
              </SelectTrigger>
              <SelectContent>
                {pointsOfSale.map((pos) => (
                  <SelectItem key={pos.id} value={pos.id}>
                    {pos.name}
                  </SelectItem>
                ))}
                {canScopeToAllPointsOfSale && (
                  <SelectItem value={ALL_POINTS_OF_SALE}>Todas las tiendas</SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>

          <AgentSessionCostBar cost={cost} />

          <span className="ml-auto flex items-center gap-1.5 text-sm text-muted-foreground">
            <TriangleAlert className="h-4 w-4 shrink-0" aria-hidden="true" />
            Modo agente · ~5 s típico, hasta 12 s
          </span>
        </CardContent>
      </Card>

      {/* The consequence of the wider scope, stated **when it is selected**. Not a display
          preference: with no shop the availability label can never say the shop is out of stock, so
          the loop never pivots — a capability lost. */}
      {scopeIsAllPointsOfSale && (
        <p
          data-testid="agent-all-shops-warning"
          role="status"
          className="flex items-start gap-2 text-sm text-muted-foreground"
        >
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          Con todas las tiendas el agente no puede saber si algo está agotado, así que{' '}
          <strong>no ofrecerá alternativas</strong> y tampoco dirá existencias.
        </p>
      )}

      {agentOff && (
        <p data-testid="agent-unavailable" role="status" className="text-sm text-muted-foreground">
          {degradedReasonText(availability?.agentUnavailableReason)}
        </p>
      )}

      {/* The thread. Only the last block is open; the earlier ones collapse to one line with chips
          and reopen when activated, so the act of selling always belongs to what is open. */}
      <div data-testid="agent-thread" className="space-y-4">
        {exchanges.map((exchange) => {
          const open = exchange.id === openBlockId;

          return (
            <div
              key={exchange.id}
              data-testid="agent-exchange"
              data-open={open}
              className="space-y-3 rounded-lg border p-4"
            >
              <p className="text-sm font-medium">
                <span className="text-muted-foreground">Tú: </span>
                {exchange.question}
              </p>

              {exchange.failure && (
                <p data-testid="agent-exchange-failure" role="status" className="text-sm text-muted-foreground">
                  {exchange.failure.kind === 'invalid'
                    ? exchange.failure.errors.join(' ')
                    : exchange.failure.kind === 'error'
                      ? exchange.failure.message
                      : FAILURE_COPY[exchange.failure.kind]}
                </p>
              )}

              {!exchange.answer && !exchange.failure && (
                <p className="text-sm text-muted-foreground">El agente está buscando…</p>
              )}

              {exchange.answer && !open && (
                // The collapsed line has to be cheap: up to six blocks, each with rows and photos.
                <button
                  type="button"
                  data-testid="agent-exchange-summary"
                  onClick={() => setOpenBlockId(exchange.id)}
                  className="flex w-full items-center gap-2 text-start text-sm text-muted-foreground hover:text-foreground"
                >
                  <ChevronDown className="h-4 w-4 shrink-0" aria-hidden="true" />
                  <Badge variant="secondary">
                    {exchange.answer.groups.reduce(
                      (total, group) => total + group.members.length,
                      0,
                    )}{' '}
                    piezas
                  </Badge>
                  <Badge variant="outline">{exchange.answer.iterations} vueltas</Badge>
                  <span>Ver la respuesta</span>
                </button>
              )}

              {exchange.answer && open && (
                <AgentAnswerBlock
                  answer={exchange.answer}
                  onSelect={handleSelect(exchange)}
                  onOpenCard={handleOpenCard}
                  pointOfSaleName={scopeIsAllPointsOfSale ? null : posName}
                />
              )}
            </div>
          );
        })}

        {exchanges.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Pregunta al agente lo que un cliente te acaba de preguntar. Puede buscar en el catálogo,
            mirar existencias, consultar la documentación de la casa y proponer alternativas.
          </p>
        )}
      </div>

      <div ref={composerRef}>
        <AgentComposer
          draft={draft}
          onDraftChange={setDraft}
          onSend={send}
          count={count}
          pending={pending}
          disabled={!pointOfSaleId || agentOff}
        />
      </div>
    </div>
  );
}

export default AgentSalesPage;
