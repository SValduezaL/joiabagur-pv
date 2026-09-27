/**
 * Assisted Search Panel (EP14 / C16)
 *
 * The operator describes a piece in their own words and gets back what their shop actually
 * carries, at the price the catalog holds right now. The backend decides everything: this page
 * never re-sorts, never re-filters and never recomputes stock or price.
 *
 * Two rules govern the interaction and are easy to break by accident:
 *
 * 1. **A search is issued only when the operator asks for one.** Never on typing. The candidate
 *    cache is keyed on the whole query string, so no prefix can hit it: a debounced field would
 *    charge several query embeddings per query, of which at most one would be read, and would
 *    exhaust the per-user request budget in five or six searches.
 * 2. **Nothing is shown that the system has not asserted.** Since C21 the retriever's match
 *    reasons carry real provenance, so the origin is read from them per result rather than
 *    decided once for the whole response; the variant label is still null until C18. Neither
 *    is faked; the row degrades instead.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Search, Sparkles, Info } from 'lucide-react';
import { toast } from 'sonner';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
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
  AssistedSearchResultRow,
  searchOrigin,
} from '@/components/sales/assisted-search-result-row';
import { AiAvailabilityBadge } from '@/components/sales/ai-availability-badge';
import { SearchRouteToggle } from '@/components/sales/search-route-toggle';
import {
  FreeQueryAnswer,
  FreeQueryLoading,
} from '@/components/sales/free-query/free-query-answer';
import { useAuth } from '@/providers/auth-provider';
import { aiSearchService } from '@/services/ai-search.service';
import * as pointOfSaleService from '@/services/point-of-sale.service';
import { queryWarnings, warningLabel } from "@/lib/assist-copy";
import {
  EXAMPLE_QUERIES,
  MATERIAL_OPTIONS,
  PIECE_TYPE_OPTIONS,
} from '@/lib/materials-vocabulary';
import { ROUTES } from '@/routing/routes';
import type {
  AiSearchAvailability,
  AssistedSearchResponse,
  AssistedSearchResult,
  FreeQuerySearchResponse,
  SearchRoute,
} from '@/types/ai-search.types';
import type { PointOfSale } from '@/types/point-of-sale.types';

const PAGE_SIZE = 10;

/**
 * The value the scope option carries inside the selector, and **nowhere else** (C40_FIX).
 *
 * A `Select` needs a value for every option, and the scope covering every shop is not a shop, so
 * it needs one that no identifier can collide with. The same pattern the category filter on this
 * page already uses — `value={category || 'all'}` — for the same reason.
 *
 * **It never reaches a request.** Every call site translates it to the *absence* of the point-of-sale
 * field before anything is sent, because what makes this scope safe is that an absent point of sale
 * leaves the availability prefilter unapplied rather than matching every shop. A blank identifier
 * travelling instead would be the wildcard-by-accident that C40 spent a whole group of work closing,
 * and both routes refuse one on purpose.
 */
const ALL_POINTS_OF_SALE = '__all__';

/** Everything the panel can be showing, once a search has settled. */
type PanelState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'answered'; response: AssistedSearchResponse }
  | { kind: 'assisted'; response: FreeQuerySearchResponse }
  | { kind: 'rate-limited' }
  | { kind: 'forbidden' }
  | { kind: 'invalid'; errors: string[] }
  | { kind: 'error'; message: string };

export function AssistedSalesSearchPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.role === 'Administrator';

  /**
   * One search episode per visit to the panel.
   *
   * The episode exists so the reformulations of a visit are not counted as abandoned queries,
   * and reformulations happen inside a visit. Two visits that each end in a selection are two
   * legitimate episodes with nothing to group between them.
   *
   * Initialised lazily: `useRef(crypto.randomUUID())` would evaluate a fresh identifier on every
   * render and throw all of them away, which is a keystroke's worth of waste on a page whose
   * whole point is not to waste work per keystroke.
   */
  const sessionRef = useRef<string | null>(null);
  sessionRef.current ??= crypto.randomUUID();
  const searchSessionId = sessionRef.current;

  /**
   * Guards against out-of-order responses: submit, change shop, submit again, and the first
   * response could otherwise land last and overwrite the second.
   */
  const requestSeq = useRef(0);

  /**
   * The query box, so a clarification can return focus to it.
   *
   * The question the service asks back is an instruction to say more, and leaving the caret
   * wherever it was makes the operator hunt for the field they were just asked to use.
   */
  const queryBoxRef = useRef<HTMLInputElement>(null);

  const focusQueryBox = useCallback(() => {
    queryBoxRef.current?.focus();
  }, []);

  const [query, setQuery] = useState('');
  const [materials, setMaterials] = useState<string[]>([]);
  const [category, setCategory] = useState<string>('');
  const [pointsOfSale, setPointsOfSale] = useState<PointOfSale[]>([]);
  const [pointOfSaleId, setPointOfSaleId] = useState<string>('');
  const [loadingPos, setLoadingPos] = useState(true);
  const [state, setState] = useState<PanelState>({ kind: 'idle' });
  const [showFunnel, setShowFunnel] = useState(false);

  // Read before any search, and re-read when the shop changes: the switches are per point of
  // sale, so the answer is about this shop and not about the installation.
  /**
   * Which route the next search takes.
   *
   * **Defaults to the cheap one, and is not remembered between visits.** Component state and
   * deliberately nothing else: no localStorage, no query parameter, no profile field.
   * Remembering the expensive face is how it gets spent without anybody deciding to, and the
   * assisted route costs four times the time budget and three times the quota.
   */
  const [route, setRoute] = useState<SearchRoute>('semantic');

  const [availability, setAvailability] = useState<AiSearchAvailability | null>(null);
  const [availabilitySettled, setAvailabilitySettled] = useState(false);

  /**
   * Whether the search covers every shop rather than one (C40_FIX).
   *
   * C40 built this scope in full — a third `AiCallScope` class, a third claims profile,
   * authorisation open to both roles, nullable quantities and a row with three states — and left no
   * way into it, so none of it ever ran. This is that way in.
   */
  const scopeIsAllPointsOfSale = pointOfSaleId === ALL_POINTS_OF_SALE;

  /**
   * The point of sale as the network sees it: a real identifier, or **nothing at all**.
   *
   * The single place the selector's sentinel stops being a value. Everything downstream — the
   * availability probe, the search payload — reads this and never `pointOfSaleId`.
   */
  const scopedPointOfSaleId = scopeIsAllPointsOfSale ? undefined : pointOfSaleId || undefined;

  /**
   * Whether the every-shop scope is on offer at all.
   *
   * **Administrators only, and this is a decision of the screen rather than an authorisation
   * boundary.** The free-query route serves the scope to operators too, by its own requirement and
   * with its reason written down, and that stays as it is: the boundary actually being protected is
   * that nobody may *name* a shop they are not assigned to. What the panel declines to offer is a
   * tool that answers the wrong question at a counter — the scope reports no stock at all, so it
   * cannot close a sale, and «is it in another shop?» is precisely what it does not answer.
   */
  const canScopeToAllPointsOfSale = isAdmin;

  /**
   * The route the next search will actually take (C40_FIX).
   *
   * **The every-shop scope pins the assisted one**, because the fast route refuses a request with no
   * point of sale — `POST /api/ai/search` validates it as required and answers 400. Letting the
   * chosen route stand would print «La búsqueda asistida requiere un punto de venta» underneath the
   * control that had just offered the scope: the screen contradicting itself, which is worse than
   * the gap this change came to close.
   *
   * Derived rather than written into state, so that leaving the scope restores whatever the operator
   * had chosen instead of silently keeping them on the expensive route.
   */
  const effectiveRoute: SearchRoute = scopeIsAllPointsOfSale ? 'assisted' : route;

  useEffect(() => {
    const load = async () => {
      try {
        const all = await pointOfSaleService.getPointsOfSale();
        // Only active ones: the endpoint refuses an inactive point of sale for every role, so
        // offering one would be offering a guaranteed error.
        const active = all.filter((pos) => pos.isActive);
        setPointsOfSale(active);
        if (active.length > 0) {
          setPointOfSaleId(active[0].id);
        }
      } catch {
        toast.error('No se pudieron cargar los puntos de venta');
      } finally {
        setLoadingPos(false);
      }
    };
    load();
  }, []);

  /**
   * Reads the two switches for the selected shop, before anything is searched.
   *
   * This costs no AI call and no quota, which is what makes it safe to do on every shop change.
   * It is also the only way the panel can tell the operator that a path is off *before* they use
   * it — the flag inside a search response arrives too late to prevent anything.
   */
  useEffect(() => {
    // Nothing is chosen yet, because the shops are still loading. That is the only state with no
    // scope to read availability for.
    //
    // **The every-shop scope is a scope, not a gap** (C40_FIX). While this guard also caught it,
    // selecting it left `settled` false for good, so the badge stayed on «Comprobando
    // disponibilidad…» and the assisted option came out disabled with no reason to show — the very
    // failure this probe was introduced to remove, reappearing one scope along.
    if (!pointOfSaleId) {
      setAvailability(null);
      setAvailabilitySettled(false);
      return;
    }

    let current = true;
    setAvailabilitySettled(false);

    aiSearchService.getAvailability(scopedPointOfSaleId).then((outcome) => {
      // A stale answer must never overwrite a newer one, the same guard the search itself uses.
      if (!current) return;
      setAvailability(outcome.kind === 'ok' ? outcome.availability : null);
      setAvailabilitySettled(true);
    });

    return () => {
      current = false;
    };
    // `scopedPointOfSaleId` is derived from `pointOfSaleId`, so listing the latter describes when
    // this effect must run without re-running it twice for one change of scope.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pointOfSaleId]);

  const runSearch = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || !pointOfSaleId) return;

      const seq = ++requestSeq.current;
      setState({ kind: 'loading' });

      // **The scope travels as an absence, never as a blank identifier** (C40_FIX). Spreading a
      // conditional rather than assigning `undefined` so the key is not present at all: the route
      // reads the field not being there as «every shop» and refuses a blank one, and the two must
      // stay tellable apart — reading a blank as an absence would turn a client bug into a wider
      // search.
      const payload = {
        query: trimmed,
        ...(scopedPointOfSaleId ? { pointOfSaleId: scopedPointOfSaleId } : {}),
        pageSize: PAGE_SIZE,
        searchSessionId,
        materials,
        category: category || undefined,
      };

      // One request, on the route the operator chose. The two endpoints differ in switch,
      // allowance, time budget and circuit, which is why they are two and not a `mode` field.
      const outcome =
        effectiveRoute === 'assisted'
          ? await aiSearchService.searchAssisted(payload)
          : await aiSearchService.search(payload);

      // A response that is no longer the current one is dropped rather than rendered.
      if (seq !== requestSeq.current) return;

      switch (outcome.kind) {
        case 'ok':
          setState(
            'groups' in outcome.response
              ? { kind: 'assisted', response: outcome.response }
              : { kind: 'answered', response: outcome.response },
          );
          break;
        case 'rate-limited':
          setState({ kind: 'rate-limited' });
          break;
        case 'forbidden':
          setState({ kind: 'forbidden' });
          break;
        case 'invalid':
          setState({ kind: 'invalid', errors: outcome.errors });
          break;
        default:
          setState({ kind: 'error', message: outcome.message });
      }
    },
    // searchSessionId is stable for the life of the panel; listed so the dependency array
    // describes what the callback actually reads rather than what happens to change.
    // `scopedPointOfSaleId` is derived from `pointOfSaleId`, already listed.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [pointOfSaleId, materials, category, searchSessionId, effectiveRoute],
  );

  const handleSubmit = () => runSearch(query);

  const handleExample = (example: string) => {
    setQuery(example);
    // Fills the field *and* searches, in one act: the example is there to teach what can be
    // asked, and making the operator press again would waste the lesson.
    runSearch(example);
  };

  const toggleMaterial = (value: string) => {
    // Toggling never searches: each change of filter is a different cache key, so three toggles
    // would be three charged query embeddings.
    setMaterials((prev) =>
      prev.includes(value) ? prev.filter((m) => m !== value) : [...prev, value],
    );
  };

  const clearFilters = () => {
    setMaterials([]);
    setCategory('');
  };

  const handlePointOfSaleChange = (value: string) => {
    setPointOfSaleId(value);
    // Cleared rather than re-run: another shop is another assortment, and re-running here would
    // charge an embedding the operator did not ask for.
    setState({ kind: 'idle' });
    requestSeq.current += 1;
  };

  const handleSelect = (result: AssistedSearchResult) => {
    // **Both routes, because both responses carry the identifier and both show rows the operator
    // can pick.** Reading only `answered` attributed nothing to a free query: the rows are the
    // same component, the button is the same button, and the event was already persisted — the
    // identifier was simply dropped on the way back, which is the class of loss this change
    // exists to remove.
    const searchEventId =
      state.kind === 'answered' || state.kind === 'assisted'
        ? state.response.searchEventId ?? undefined
        : undefined;

    // Reported at the instant of the click and deliberately not awaited: the server stamps the
    // moment, and a telemetry failure must never block the operator or surface as an error.
    // A null identifier means telemetry did not persist, and the report is skipped in silence.
    if (searchEventId) {
      void aiSearchService.reportSelection(searchEventId, result.productId);
    }

    navigate(ROUTES.SALES.NEW, {
      state: { productId: result.productId, searchEventId },
    });
  };

  /**
   * Opens the sale card for a result, scoped to the point of sale this search was scoped to.
   *
   * **No selection is reported.** Opening a card is not choosing the piece to sell, and counting
   * it as one would inflate the selection rate the search event exists to measure. It issues no
   * search, changes no displayed result and does not end the search episode of this visit — the
   * episode identifier lives in a ref that this navigation does not touch.
   */
  const handleOpenCard = (result: AssistedSearchResult) => {
    navigate(ROUTES.SALES.ASSIST(result.productId), {
      state: { pointOfSaleId },
    });
  };

  const hasFilters = materials.length > 0 || category !== '';

  const response = state.kind === 'answered' ? state.response : null;

  /**
   * The assisted answer, when that is the route that ran.
   *
   * Held apart from `response` rather than merged into it: the two have different shapes —
   * a flat list against families, with prose and citations — and collapsing them would make
   * every render decision below ask which one it is holding.
   */
  const assisted = state.kind === 'assisted' ? state.response : null;
  const shortPage =
    response !== null && response.results.length > 0 && response.results.length < PAGE_SIZE;

  const posName = useMemo(
    () => pointsOfSale.find((pos) => pos.id === pointOfSaleId)?.name ?? '',
    [pointsOfSale, pointOfSaleId],
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link to={ROUTES.SALES.ROOT} aria-label="Volver a ventas">
            <ArrowLeft className="size-5" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Buscar con ayuda</h1>
          <p className="text-muted-foreground">
            {scopeIsAllPointsOfSale
              ? 'Describe la pieza con tus palabras y te enseño lo que hay en el catálogo'
              : 'Describe la pieza con tus palabras y te enseño lo que hay en tu tienda'}
          </p>
        </div>
      </div>

      {/*
        Stated before anything is searched. Until this existed the only way to discover that a
        path was switched off was to use it, which is how the panel spent the whole project
        serving from its degraded route while looking exactly as it does when the AI answers.
      */}
      <AiAvailabilityBadge
        availability={availability}
        settled={availabilitySettled}
        scopeIsAllPointsOfSale={scopeIsAllPointsOfSale}
      />

      <Card>
        <CardContent className="space-y-4 pt-6">
          {pointsOfSale.length > 1 || isAdmin ? (
            <div className="space-y-2">
              <Label htmlFor="assisted-pos">Punto de venta</Label>
              <Select value={pointOfSaleId} onValueChange={handlePointOfSaleChange}>
                <SelectTrigger id="assisted-pos" className="w-full sm:w-72">
                  <SelectValue placeholder="Selecciona un punto de venta" />
                </SelectTrigger>
                <SelectContent>
                  {/*
                    First in the list and set apart, because it is not one more shop: it is a
                    different question. Administrators only — see `canScopeToAllPointsOfSale`.
                  */}
                  {canScopeToAllPointsOfSale ? (
                    <SelectItem value={ALL_POINTS_OF_SALE}>Todas las tiendas</SelectItem>
                  ) : null}
                  {pointsOfSale.map((pos) => (
                    <SelectItem key={pos.id} value={pos.id}>
                      {pos.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/*
                The consequence, stated before searching rather than discovered result by result.
                The scope reports no stock at all, so an administrator who expects «where is it?»
                has to learn here that the answer is «does it exist?».
              */}
              {scopeIsAllPointsOfSale ? (
                <p
                  className="text-sm text-muted-foreground"
                  data-testid="assisted-scope-consequence"
                >
                  Verás piezas de todo el catálogo. Para leer existencias, elige una tienda.
                </p>
              ) : null}
            </div>
          ) : null}

          {/*
            Changing route issues NO request. It picks what the next search will do, and the
            panel's first rule is that a search happens only when the operator asks for one.
          */}
          <SearchRouteToggle
            value={effectiveRoute}
            onChange={setRoute}
            assistedAvailable={availability?.assistedAnswerAvailable ?? false}
            assistedUnavailableReason={availability?.assistedAnswerUnavailableReason}
            semanticUnavailableReason={
              scopeIsAllPointsOfSale
                ? 'La búsqueda rápida trabaja sobre una tienda concreta'
                : null
            }
            scopeIsAllPointsOfSale={scopeIsAllPointsOfSale}
            disabled={state.kind === 'loading'}
          />

          {/*
            The dead end, said out loud (C40_FIX). With the every-shop scope selected the fast route
            cannot serve it and the assisted one is switched off, so both options of the toggle are
            disabled. Left unsaid that is a scope you can pick and cannot search from — which is the
            same silence this whole change exists to remove.

            Stated rather than pre-disabling the scope option: knowing in advance would mean reading
            the probe twice on every load, once for the selected scope and once for the wider one,
            and picking a scope costs no request at all.
          */}
          {scopeIsAllPointsOfSale &&
          availabilitySettled &&
          !(availability?.assistedAnswerAvailable ?? false) ? (
            <p className="text-sm text-warning" data-testid="assisted-scope-dead-end">
              La búsqueda en todas las tiendas usa la respuesta asistida, y está desactivada.
            </p>
          ) : null}
          <div className="space-y-2">
            <Label htmlFor="assisted-query">¿Qué busca el cliente?</Label>
            <div className="flex gap-2">
              <Input
                id="assisted-query"
                ref={queryBoxRef}
                placeholder="Un anillo de plata para regalar..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSubmit();
                }}
                disabled={loadingPos}
              />
              <Button
                onClick={handleSubmit}
                disabled={!query.trim() || !pointOfSaleId || state.kind === 'loading'}
              >
                <Search className="mr-2 size-4" />
                Buscar
              </Button>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-muted-foreground">Prueba con:</span>
            {EXAMPLE_QUERIES.map((example) => (
              <Button
                key={example}
                variant="outline"
                size="sm"
                onClick={() => handleExample(example)}
              >
                <Sparkles className="mr-1.5 size-3.5" />
                {example}
              </Button>
            ))}
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Materiales</Label>
              {hasFilters ? (
                <Button variant="ghost" size="sm" onClick={clearFilters}>
                  Quitar filtros
                </Button>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-2">
              {MATERIAL_OPTIONS.map((option) => {
                const selected = materials.includes(option.value);
                return (
                  <Button
                    key={option.value}
                    type="button"
                    variant={selected ? 'primary' : 'outline'}
                    size="sm"
                    aria-pressed={selected}
                    onClick={() => toggleMaterial(option.value)}
                  >
                    {option.label}
                  </Button>
                );
              })}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="assisted-category">Tipo de pieza</Label>
            <Select value={category || 'all'} onValueChange={(v) => setCategory(v === 'all' ? '' : v)}>
              <SelectTrigger id="assisted-category" className="w-full sm:w-72">
                <SelectValue placeholder="Cualquiera" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Cualquiera</SelectItem>
                {PIECE_TYPE_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* An expectation from the first instant on the assisted route, never a blank pane: the
          budget is ten seconds, and seven of undifferentiated waiting with a customer at the
          counter is where this feature gets abandoned. */}
      {state.kind === 'loading' && route === 'assisted' ? <FreeQueryLoading /> : null}

      {state.kind === 'loading' ? (
        <div className="space-y-3" data-testid="assisted-search-loading">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))}
        </div>
      ) : null}

      {state.kind === 'rate-limited' ? (
        <Alert variant="warning">
          <AlertTitle>Demasiadas búsquedas seguidas</AlertTitle>
          <AlertDescription>
            Espera unos segundos y vuelve a intentarlo.
          </AlertDescription>
        </Alert>
      ) : null}

      {state.kind === 'forbidden' ? (
        <Alert variant="destructive">
          <AlertTitle>No tienes acceso a esta tienda</AlertTitle>
          <AlertDescription>
            Selecciona un punto de venta que tengas asignado.
          </AlertDescription>
        </Alert>
      ) : null}

      {state.kind === 'invalid' ? (
        <Alert variant="destructive">
          <AlertTitle>La búsqueda no es válida</AlertTitle>
          <AlertDescription>{state.errors.join(' ')}</AlertDescription>
        </Alert>
      ) : null}

      {state.kind === 'error' ? (
        <Alert variant="destructive">
          <AlertTitle>No se pudo completar la búsqueda</AlertTitle>
          <AlertDescription>{state.message}</AlertDescription>
        </Alert>
      ) : null}

      {assisted ? (
        <FreeQueryAnswer
          response={assisted}
          onSelect={handleSelect}
          onOpenCard={handleOpenCard}
          onClarificationAsked={focusQueryBox}
          pointOfSaleName={posName}
          isAdmin={isAdmin}
        />
      ) : null}
      {response ? (
        <div className="space-y-4">
          {/* Degraded or switched off. The response cannot tell those apart — telemetry can, the
              API cannot — and for the operator the sentence is the same either way. */}
          {!response.aiAvailable ? (
            <Alert variant="warning">
              <AlertTitle>Búsqueda asistida no disponible</AlertTitle>
              <AlertDescription>
                Estos resultados vienen de la búsqueda por texto.
              </AlertDescription>
            </Alert>
          ) : null}

          {/* The AI service answered, but without its semantic branch — the embedding provider
              failed and it served the lexical branch instead. Left unsaid this is the failure
              that looks healthiest of all: 200, results on screen, and the capability the
              screen is named after never ran. */}
          {searchOrigin(response.results, response.aiAvailable) === 'service-lexical' ? (
            <Alert variant="warning">
              <AlertTitle>Coincidencia semántica no disponible</AlertTitle>
              <AlertDescription>
                Estos resultados vienen de la búsqueda por texto. Prueba a describir la pieza
                con las palabras del catálogo.
              </AlertDescription>
            </Alert>
          ) : null}

          {/* What the retriever said about the QUERY, on the semantic route too. The
              decision behind `filters_too_narrow` belongs to retrieval, so it reaches both
              routes; showing it only on the assisted one would leave an operator who never
              touches the toggle staring at three results and no explanation. Same copy on
              both, from the shared table. */}
          {queryWarnings(response.warnings ?? []).length > 0 ? (
            <Alert variant="warning" data-testid="semantic-query-warnings">
              <AlertDescription>
                {queryWarnings(response.warnings ?? []).map((code) => (
                  <span key={code} className="block">
                    {warningLabel(code)}
                  </span>
                ))}
              </AlertDescription>
            </Alert>
          ) : null}

          {response.results.length === 0 && response.aiAvailable && response.lowConfidence ? (
            <Alert>
              <AlertTitle>No he encontrado nada que encaje</AlertTitle>
              <AlertDescription>
                Prueba a describirlo de otra forma.
              </AlertDescription>
            </Alert>
          ) : null}

          {response.results.length === 0 &&
          response.aiAvailable &&
          !response.lowConfidence &&
          response.candidatesReturned > 0 ? (
            <Alert>
              {/*
                Worded per scope (C40_FIX). «Tu tienda» is false when the search covered every one
                of them, and the fallback these lines carried — «este punto de venta» — was written
                when one shop was the only scope there was. With no shop, what did not survive is
                that nothing in the whole catalogue is on any active shelf.
              */}
              <AlertTitle>
                {scopeIsAllPointsOfSale
                  ? 'Nada de esto está en el catálogo activo'
                  : 'Nada de esto está en tu tienda'}
              </AlertTitle>
              <AlertDescription>
                Encontré {response.candidatesReturned} piezas parecidas, pero ninguna está
                disponible en {scopeIsAllPointsOfSale ? 'ninguna tienda' : posName || 'este punto de venta'}.
                {hasFilters ? ' Prueba a quitar los filtros.' : ''}
              </AlertDescription>
            </Alert>
          ) : null}

          {response.results.length === 0 &&
          response.aiAvailable &&
          !response.lowConfidence &&
          response.candidatesReturned === 0 ? (
            <Alert>
              <AlertTitle>Sin resultados</AlertTitle>
              <AlertDescription>Prueba a describirlo de otra forma.</AlertDescription>
            </Alert>
          ) : null}

          {response.results.length === 0 && !response.aiAvailable ? (
            <Alert>
              <AlertTitle>Sin resultados</AlertTitle>
              <AlertDescription>
                {scopeIsAllPointsOfSale
                  ? 'La búsqueda por texto tampoco ha encontrado nada en el catálogo.'
                  : 'La búsqueda por texto tampoco ha encontrado nada en tu tienda.'}
              </AlertDescription>
            </Alert>
          ) : null}

          {/* Rendered in the order received. No sort(): the rank is the measurement of retrieval
              quality, and re-sorting would make it measure this page instead. */}
          {response.results.map((result) => (
            <AssistedSearchResultRow
              pointOfSaleName={posName}
              key={result.productId}
              result={result}
              onSelect={handleSelect}
              onOpenCard={handleOpenCard}
            />
          ))}

          {/* A short page is the frequent case where assortment coverage is low. Left unsaid it
              reads as the system being unable to search, when the shop simply does not carry it. */}
          {shortPage ? (
            <p className="text-sm text-muted-foreground" data-testid="assisted-search-short-page">
              {response.results.length} resultados en{' '}
              {scopeIsAllPointsOfSale ? 'todas las tiendas' : posName || 'esta tienda'} ·{' '}
              {response.candidatesReturned} candidatos considerados
            </p>
          ) : null}

          {isAdmin ? (
            <div data-testid="assisted-search-funnel">
              <Button variant="ghost" size="sm" onClick={() => setShowFunnel((v) => !v)}>
                <Info className="mr-1.5 size-3.5" />
                Embudo de recuperación
              </Button>
              {showFunnel ? (
                <div className="mt-2 flex flex-wrap gap-2 text-sm text-muted-foreground">
                  <Badge variant="secondary" appearance="outline">
                    Candidatos: {response.candidatesReturned}
                  </Badge>
                  <Badge variant="secondary" appearance="outline">
                    Supervivientes: {response.survivedHydration}
                  </Badge>
                  <Badge variant="secondary" appearance="outline">
                    Mostrados: {response.results.length}
                  </Badge>
                  {response.searchEventId ? (
                    <Badge variant="secondary" appearance="outline">
                      Evento: {response.searchEventId}
                    </Badge>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export default AssistedSalesSearchPage;
