/**
 * Assisted Search Service (EP14 / C16)
 *
 * Two calls, and only two: running a search and reporting the selection made on it. Everything
 * else about a search event — the rank, the timings, the origin, the displayed list — the server
 * either already stored or derives itself.
 *
 * Routes are relative: `VITE_API_BASE_URL` already carries `/api`.
 */

import apiClient from './api.service';
import type {
  AiSearchAvailability,
  FreeQuerySearchOutcome,
  FreeQuerySearchRequest,
  FreeQuerySearchResponse,
  AiSearchAvailabilityOutcome,
  AssistedSearchOutcome,
  AssistedSearchRequest,
  AssistedSearchResponse,
  SearchFailureOutcome,
} from '@/types/ai-search.types';
import type { ApiError } from '@/types/api.types';

const SEARCH_ENDPOINT = '/ai/search';
const ASSISTED_ENDPOINT = '/ai/search/assisted';
const AVAILABILITY_ENDPOINT = '/ai/search/availability';
const SEARCH_EVENTS_ENDPOINT = '/ai/search-events';

/**
 * Flattens the two validation-error shapes the API produces.
 *
 * `ApiError.errors` is typed as a field-keyed dictionary because that is what most controllers
 * return, but the AI endpoints answer with a plain array of messages. Both reach here, so both
 * are handled rather than one of them being assumed.
 */
function toMessages(errors: ApiError['errors'] | string[] | undefined): string[] {
  if (!errors) return [];
  if (Array.isArray(errors)) return errors;
  return Object.values(errors).flat();
}

function toOutcome(error: unknown): SearchFailureOutcome {
  const apiError = error as ApiError;

  switch (apiError?.statusCode) {
    // Kept as a member of its own on purpose. The endpoint's contract requires that exceeding
    // the request budget stays distinguishable from the AI service being unavailable: one is a
    // fault, the other is the system protecting itself, and folding them together would show an
    // outage message to an operator who only has to wait a few seconds.
    case 429:
      return { kind: 'rate-limited' };

    case 403:
      return { kind: 'forbidden' };

    case 400: {
      const messages = toMessages(apiError.errors);
      return {
        kind: 'invalid',
        errors: messages.length
          ? messages
          : [apiError.message ?? 'La búsqueda no es válida.'],
      };
    }

    default:
      return {
        kind: 'error',
        message: apiError?.message ?? 'No se pudo completar la búsqueda.',
      };
  }
}

export const aiSearchService = {
  /**
   * Runs an assisted search.
   *
   * Never throws: every failure is mapped to a typed outcome so the panel can say something
   * true on screen instead of showing an application error.
   */
  search: async (request: AssistedSearchRequest): Promise<AssistedSearchOutcome> => {
    try {
      const response = await apiClient.post<AssistedSearchResponse>(SEARCH_ENDPOINT, request);
      return { kind: 'ok', response: response.data };
    } catch (error) {
      return toOutcome(error);
    }
  },

  /**
   * Runs the assisted answer: the other route of the panel's toggle. C40.
   *
   * Never throws, and maps `rate-limited` to a member of its own for the same reason the semantic
   * path does: exceeding the allowance and the AI being unavailable have opposite remedies, and
   * this route's allowance is three times tighter, so the case is three times more reachable.
   */
  searchAssisted: async (
    request: FreeQuerySearchRequest,
  ): Promise<FreeQuerySearchOutcome> => {
    try {
      const response = await apiClient.post<FreeQuerySearchResponse>(
        ASSISTED_ENDPOINT,
        request,
      );
      return { kind: 'ok', response: response.data };
    } catch (error) {
      return toOutcome(error);
    }
  },

  /**
   * Reads which assisted paths are switched on for a scope: one point of sale, or every one of
   * them when none is given.
   *
   * Never throws, and never reports a failure as an outage: a panel that cannot read the switches
   * still searches perfectly well, so the badge says it could not tell rather than announcing a
   * problem the operator can neither verify nor fix.
   *
   * Costs no AI call and no quota, which is what makes it safe to ask before every search — and
   * what makes it safe to ask again whenever the scope changes.
   *
   * **The parameter is omitted rather than blanked** when there is no shop. The route refuses a
   * blank identifier on purpose and reads only a genuine absence as the wider scope, so sending
   * an empty string here would turn the wider scope into a validation error.
   */
  getAvailability: async (pointOfSaleId?: string): Promise<AiSearchAvailabilityOutcome> => {
    try {
      const response = await apiClient.get<AiSearchAvailability>(AVAILABILITY_ENDPOINT, {
        params: pointOfSaleId ? { pointOfSaleId } : undefined,
      });
      return { kind: 'ok', availability: response.data };
    } catch {
      return { kind: 'unknown' };
    }
  },

  /**
   * Reports the product the operator picked from the displayed results.
   *
   * **Do not await this in a click handler.** The server stamps the moment, so the call has to
   * leave at the instant of the click; and its failure is invisible by design — a telemetry
   * problem must never block the operator or surface as an error. The promise is returned only
   * so tests can settle it.
   */
  reportSelection: (searchEventId: string, productId: string): Promise<void> =>
    apiClient
      .post(`${SEARCH_EVENTS_ENDPOINT}/${searchEventId}/selection`, { productId })
      .then(() => undefined)
      .catch(() => undefined),
};

export default aiSearchService;
