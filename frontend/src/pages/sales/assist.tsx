/**
 * Sale Card Page (EP15 / C36)
 *
 * The one screen of this project that puts the RAG layer in front of a person. Anchored to one
 * piece and one point of sale, reached from the assisted search results, from the manual sale
 * page and from a scanned code.
 *
 * Four rules govern the interaction, and every one of them is easy to break by accident:
 *
 * 1. **Exactly one assist request per visit**, issued on entry. Navigating here *is* the explicit
 *    act the assisted search panel's living spec demands for an expensive call — and this one is
 *    ten times more expensive. The budget is ten requests per minute per user and the response
 *    cannot be cached, so re-rendering, a response arriving and a failure must none of them
 *    produce another.
 * 2. **No automatic retry.** On a route whose p95 is 7,1 s, a retry doubles both the cost and the
 *    wait. The operator asks for it with a button.
 * 3. **The customer's question is a second explicit request**, and it travels in the body. Never
 *    in the address of the page and never in router state, both of which end up in the browser's
 *    history and in the proxy's access log.
 * 4. **Substitutes are triggered by the anchored member's stock**, not by the state of the
 *    argument: the first is present in every state the backend served, the second only reports
 *    the absence of stock when no question was asked.
 *
 * Leaving and coming back is another visit and pays again. That is said in the spec rather than
 * hidden behind a cache the living spec of C34 forbids.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';

import {
  FamilyBlock,
  PieceHeader,
  PitchBlock,
  QuestionBox,
  SubstitutesBlock,
  WarningsBlock,
  type SubstitutesState,
} from '@/components/sales/sales-assist-card';
import { useAuth } from '@/providers/auth-provider';
import { salesAssistService } from '@/services/sales-assist.service';
import * as pointOfSaleService from '@/services/point-of-sale.service';
import { ROUTES } from '@/routing/routes';
import type {
  SalesAssistMember,
  SalesAssistResponse,
  SubstituteResult,
} from '@/types/sales-assist.types';
import type { PointOfSale } from '@/types/point-of-sale.types';

/** The point of sale the caller was working in, handed over the same way scan and image do. */
interface LocationState {
  pointOfSaleId?: string;
}

/** Everything the card can be showing once an assist request has settled. */
type CardState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'answered'; response: SalesAssistResponse }
  | { kind: 'rate-limited' }
  | { kind: 'forbidden' }
  | { kind: 'not-found' }
  | { kind: 'invalid'; errors: string[] }
  | { kind: 'error'; message: string };

export function SalesAssistCardPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { productId } = useParams<{ productId: string }>();
  const { user } = useAuth();
  const isAdmin = user?.role === 'Administrator';

  const navigatedPointOfSaleId = (location.state as LocationState | null)?.pointOfSaleId;

  /**
   * One episode per visit to the card.
   *
   * Initialised lazily: `useRef(crypto.randomUUID())` would mint a fresh identifier on every
   * render and throw all of them away. Copied from the assisted search panel, where the same
   * guard is already tested.
   */
  const visitRef = useRef<string | null>(null);
  visitRef.current ??= crypto.randomUUID();

  /**
   * Guards against out-of-order responses: ask, then ask a question, and the first response
   * could otherwise land last and overwrite the second.
   */
  const requestSeq = useRef(0);

  /**
   * The point of sale the one request of this visit was issued for, or null before it was.
   *
   * A ref and not state, because it must be set *before* the render that follows the request
   * rather than after it — a state flag would let a second effect run first and pay twice.
   *
   * It holds the point of sale rather than a boolean so that the one thing that legitimately
   * asks for another card is told apart from the three that must not. Re-rendering, the
   * response arriving and a failure all leave it equal and issue nothing; an operator naming a
   * different shop is an explicit act, like navigating here in the first place, and the card it
   * asks for is a different card. Keeping the old shop's prices under the new shop's name would
   * be the screen stating something false.
   */
  const askedForRef = useRef<string | null>(null);

  const [pointsOfSale, setPointsOfSale] = useState<PointOfSale[]>([]);
  const [pointOfSaleId, setPointOfSaleId] = useState<string>(navigatedPointOfSaleId ?? '');
  const [loadingPos, setLoadingPos] = useState(!navigatedPointOfSaleId);
  const [state, setState] = useState<CardState>({ kind: 'idle' });
  const [asking, setAsking] = useState(false);
  const [substitutes, setSubstitutes] = useState<SubstitutesState>({ kind: 'idle' });

  /**
   * The point-of-sale selector is only loaded when the card was opened cold.
   *
   * With one in navigation state there is nothing to choose, and loading the list would be a
   * request for a control that is never shown.
   */
  useEffect(() => {
    if (navigatedPointOfSaleId) return;

    const load = async () => {
      try {
        const all = await pointOfSaleService.getPointsOfSale();
        // Only active ones: the endpoint refuses an inactive point of sale for every role, so
        // offering one would be offering a guaranteed error.
        const active = all.filter((pos) => pos.isActive);
        setPointsOfSale(active);
        // A single assigned shop is not a choice, so it is taken and the card proceeds. With
        // several, nothing is requested until the operator names one.
        if (active.length === 1) setPointOfSaleId(active[0].id);
      } catch {
        toast.error('No se pudieron cargar los puntos de venta');
      } finally {
        setLoadingPos(false);
      }
    };
    load();
  }, [navigatedPointOfSaleId]);

  /**
   * The name of the point of sale that travelled in navigation state.
   *
   * The list above is deliberately not loaded on that path — there is nothing to choose — but
   * without a name the header falls back to «en esta tienda», and that is ambiguous the moment
   * more than one shop is in play. An ambiguous stock figure is the kind that costs a sale.
   *
   * One product read, no AI, and its failure is invisible on purpose: the name is what the
   * sentence would rather say, not something the card depends on. The selector stays hidden
   * because its own guard is `!navigatedPointOfSaleId`, not the length of this list.
   */
  useEffect(() => {
    if (!navigatedPointOfSaleId) return;

    let current = true;
    void pointOfSaleService
      .getPointOfSale(navigatedPointOfSaleId)
      .then((pos) => {
        if (current && pos) setPointsOfSale([pos]);
      })
      .catch(() => undefined);

    return () => {
      current = false;
    };
  }, [navigatedPointOfSaleId]);

  /** Issues one assist request, with or without the customer's question. */
  const requestAssist = useCallback(
    async (question?: string) => {
      if (!productId || !pointOfSaleId) return;

      const seq = ++requestSeq.current;
      if (question) {
        setAsking(true);
      } else {
        setState({ kind: 'loading' });
      }

      const outcome = await salesAssistService.assist(productId, {
        pointOfSaleId,
        ...(question ? { question } : {}),
      });

      // A response that is no longer the current one is dropped rather than rendered.
      if (seq !== requestSeq.current) return;

      setAsking(false);

      switch (outcome.kind) {
        case 'ok':
          setState({ kind: 'answered', response: outcome.response });
          break;
        case 'rate-limited':
          setState({ kind: 'rate-limited' });
          break;
        case 'forbidden':
          setState({ kind: 'forbidden' });
          break;
        case 'not-found':
          setState({ kind: 'not-found' });
          break;
        case 'invalid':
          setState({ kind: 'invalid', errors: outcome.errors });
          break;
        default:
          setState({ kind: 'error', message: outcome.message });
      }
    },
    [productId, pointOfSaleId],
  );

  /**
   * The one request of the visit.
   *
   * Guarded by a ref rather than by the dependency array alone: the array is what decides when
   * the effect runs, and the ref is what makes running it twice harmless. **A failure never
   * re-enters here** — the retry button calls `requestAssist` directly.
   */
  useEffect(() => {
    if (!productId || !pointOfSaleId) return;
    if (askedForRef.current === pointOfSaleId) return;
    askedForRef.current = pointOfSaleId;
    void requestAssist();
  }, [productId, pointOfSaleId, requestAssist]);

  const response = state.kind === 'answered' ? state.response : null;

  /** The anchored member: exactly one member of the group is, and it is the piece on screen. */
  const anchor = useMemo<SalesAssistMember | undefined>(() => {
    const members = response?.groups?.[0]?.members ?? [];
    return members.find((member) => member.isAnchor) ?? members[0];
  }, [response]);

  /**
   * Substitutes, asked for automatically when and only when the anchored member has no stock
   * **and** the AI path served this card.
   *
   * The trigger is `hasStock`, never `pitchStatus`: the first is present in every state the
   * backend served, the second reports the absence of stock only when no question was asked. On
   * a degraded card the call would come back `ai_unavailable` with certainty, so it is not spent
   * and the card says why instead.
   */
  useEffect(() => {
    if (!response || !productId || !anchor) return;
    if (anchor.hasStock) {
      // Cleared rather than left behind: another shop is another assortment, and a block of
      // alternatives for a piece that this shop does have would answer a question nobody asked.
      setSubstitutes({ kind: 'idle' });
      return;
    }

    if (!response.aiAvailable) {
      setSubstitutes({ kind: 'not-requested' });
      return;
    }

    let current = true;
    setSubstitutes({ kind: 'loading' });

    void salesAssistService
      .substitutes(productId, response.pointOfSaleId)
      .then((outcome) => {
        if (!current) return;
        if (outcome.kind === 'ok') {
          setSubstitutes({ kind: 'answered', response: outcome.response });
        } else if (outcome.kind === 'rate-limited') {
          setSubstitutes({
            kind: 'failed',
            message: 'Demasiadas peticiones seguidas. Espera unos segundos.',
          });
        } else {
          setSubstitutes({
            kind: 'failed',
            message: 'No se pudieron buscar alternativas en este momento.',
          });
        }
      });

    return () => {
      current = false;
    };
  }, [response, productId, anchor]);

  const posName = useMemo(
    () => pointsOfSale.find((pos) => pos.id === pointOfSaleId)?.name ?? '',
    [pointsOfSale, pointOfSaleId],
  );

  /**
   * Hands the chosen piece to the manual sale page, the mechanism scanning, image recognition
   * and assisted search already use.
   *
   * The identifier is the one whose button was pressed, and never the anchored piece when a
   * different member was chosen. The card does not duplicate the payment method, the quantity,
   * the price or the stock logic that page owns.
   */
  const handleSell = useCallback(
    (piece: { productId: string }) => {
      navigate(ROUTES.SALES.NEW, { state: { productId: piece.productId } });
    },
    [navigate],
  );

  const handleRetry = () => {
    void requestAssist();
  };

  /**
   * The customer's question: a second explicit request.
   *
   * The bound is checked inside the question box, before this is ever called, so an over-long
   * question costs nothing. The text is passed straight into the request body and is never put
   * anywhere the browser records.
   */
  const handleAsk = useCallback(
    (question: string) => {
      void requestAssist(question);
    },
    [requestAssist],
  );

  const busy = state.kind === 'loading' || asking;

  /* Opened cold with several shops: nothing is requested until one is named. */
  const needsPointOfSale = !pointOfSaleId && !loadingPos;

  return (
    <div className="space-y-6" data-testid="sales-assist-card" data-visit={visitRef.current}>
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link to={ROUTES.SALES.ROOT} aria-label="Volver a ventas">
            <ArrowLeft className="size-5" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Ficha de venta</h1>
          <p className="text-muted-foreground">
            Lo que puedes contar de esta pieza, con su precio y sus unidades reales
          </p>
        </div>
      </div>

      {/* The same role-resolved selector the assisted search panel offers. Shown only when the
          card was opened without a point of sale, and no request leaves until one is chosen. */}
      {!navigatedPointOfSaleId && (pointsOfSale.length > 1 || isAdmin) ? (
        <Card>
          <CardContent className="space-y-2 pt-6">
            <Label htmlFor="assist-pos">Punto de venta</Label>
            <Select value={pointOfSaleId} onValueChange={setPointOfSaleId}>
              <SelectTrigger id="assist-pos" className="w-full sm:w-72">
                <SelectValue placeholder="Selecciona un punto de venta" />
              </SelectTrigger>
              <SelectContent>
                {pointsOfSale.map((pos) => (
                  <SelectItem key={pos.id} value={pos.id}>
                    {pos.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>
      ) : null}

      {needsPointOfSale ? (
        <Alert data-testid="assist-needs-pos">
          <AlertTitle>Elige un punto de venta</AlertTitle>
          <AlertDescription>
            La ficha enseña el precio y las unidades de una tienda concreta, así que necesito
            saber en cuál estás.
          </AlertDescription>
        </Alert>
      ) : null}

      {/* A loading state from the first instant, never a blank screen: the wait is 4 to 8 s and
          there is a customer in front of the operator. */}
      {state.kind === 'loading' ? (
        <div className="space-y-3" data-testid="assist-loading">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : null}

      {state.kind === 'rate-limited' ? (
        <Alert variant="warning" data-testid="assist-rate-limited">
          <AlertTitle>Demasiadas fichas seguidas</AlertTitle>
          <AlertDescription>
            {/* Deliberately different from the outage message: this is the system protecting
                itself, and the operator only has to wait. */}
            <p>Espera unos segundos y vuelve a pedirla.</p>
            <Button variant="outline" size="sm" className="mt-2" onClick={handleRetry}>
              <RefreshCw className="me-1.5 size-3.5" />
              Volver a pedir la ficha
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}

      {state.kind === 'not-found' ? (
        <Alert data-testid="assist-not-found">
          <AlertTitle>Esta tienda no lleva esta pieza</AlertTitle>
          <AlertDescription>
            No está asignada a {posName || 'este punto de venta'}, así que no puedo enseñarte ni
            su precio ni sus unidades aquí.
          </AlertDescription>
        </Alert>
      ) : null}

      {state.kind === 'forbidden' ? (
        <Alert variant="destructive" data-testid="assist-forbidden">
          <AlertTitle>No tienes acceso a esta tienda</AlertTitle>
          <AlertDescription>Selecciona un punto de venta que tengas asignado.</AlertDescription>
        </Alert>
      ) : null}

      {state.kind === 'invalid' ? (
        <Alert variant="destructive" data-testid="assist-invalid">
          <AlertTitle>No se pudo preparar la ficha</AlertTitle>
          <AlertDescription>{state.errors.join(' ')}</AlertDescription>
        </Alert>
      ) : null}

      {state.kind === 'error' ? (
        <Alert variant="destructive" data-testid="assist-error">
          <AlertTitle>No se pudo preparar la ficha</AlertTitle>
          <AlertDescription>
            <p>{state.message}</p>
            {/* The retry is explicit and always the operator's. Nothing on this page retries
                on its own. */}
            <Button variant="outline" size="sm" className="mt-2" onClick={handleRetry}>
              <RefreshCw className="me-1.5 size-3.5" />
              Volver a pedir la ficha
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}

      {response && anchor ? (
        <div className="space-y-4">
          <PieceHeader
            piece={anchor}
            warnings={response.warnings}
            pointOfSaleName={posName}
          />

          <WarningsBlock warnings={response.warnings} />

          {asking ? (
            <Skeleton className="h-24 w-full" data-testid="assist-asking" />
          ) : (
            <PitchBlock
              pitchStatus={response.pitchStatus}
              pitch={response.pitch}
              citations={response.citations}
              clarificationQuestion={response.clarificationQuestion}
              degradedReason={response.degradedReason}
            />
          )}

          <FamilyBlock
            group={response.groups[0]}
            pointOfSaleName={posName}
            onSell={handleSell}
          />

          <SubstitutesBlock
            state={substitutes}
            pointOfSaleName={posName}
            onSell={(result: SubstituteResult) => handleSell(result)}
          />

          <QuestionBox onAsk={handleAsk} busy={busy} />
        </div>
      ) : null}
    </div>
  );
}

export default SalesAssistCardPage;
