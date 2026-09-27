/**
 * Sale Assist Service (EP15 / C36)
 *
 * Two calls, and only two: the sale card of a piece and the substitutes of a piece. Both are
 * anchored to one product and scoped to one point of sale, and neither is ever cached — the
 * card carries the price and the units of right now, and the living spec of C34 forbids it.
 *
 * Modelled on `ai-search.service.ts`: **nothing here ever throws**. Every failure is mapped to a
 * member of a discriminated union so the screen can say something true instead of showing an
 * application error, which on a screen used standing at the counter is the difference between an
 * answer and a dead end.
 *
 * Routes are relative: `VITE_API_BASE_URL` already carries `/api`.
 */

import apiClient from './api.service';
import type {
  SalesAssistOutcome,
  SalesAssistRequest,
  SalesAssistResponse,
  SubstitutesRequestOutcome,
  SubstitutesResponse,
} from '@/types/sales-assist.types';
import type { ApiError } from '@/types/api.types';

/** Both routes hang off the product, which is what anchors them. */
const PRODUCTS_ENDPOINT = '/ai/products';

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

/**
 * Maps a failure to its outcome, shared by both routes because both refuse for the same reasons.
 *
 * The two members worth pointing at:
 *
 * - **429** stays a member of its own. Exceeding the request budget is not an outage: the
 *   generative route allows ten per minute per user, and folding it into `error` would show an
 *   outage message to an operator who only has to wait a few seconds.
 * - **404** means the point of sale does not carry the piece — C34 answers it before calling the
 *   AI — and reads as itself rather than as a generic failure.
 *
 * A 400 from these routes is either an unknown or inactive point of sale or a question the
 * contract refuses; its messages are already written in Spanish by .NET, so they are passed
 * through rather than replaced.
 */
function toOutcome(error: unknown): Exclude<SalesAssistOutcome, { kind: 'ok' }> {
  const apiError = error as ApiError;

  switch (apiError?.statusCode) {
    case 429:
      return { kind: 'rate-limited' };

    case 403:
      return { kind: 'forbidden' };

    case 404:
      return { kind: 'not-found' };

    case 400: {
      const messages = toMessages(apiError.errors);
      return {
        kind: 'invalid',
        errors: messages.length
          ? messages
          : [apiError.message ?? 'La petición no es válida.'],
      };
    }

    default:
      return {
        kind: 'error',
        message: apiError?.message ?? 'No se pudo preparar la ficha de venta.',
      };
  }
}

export const salesAssistService = {
  /**
   * Asks for the sale card of a piece at a point of sale, with or without the customer's
   * question.
   *
   * A POST although it writes nothing, and the question in the body only: it is free text about
   * a customer, and a GET is cacheable by definition, so a prefetch could trigger a paid call.
   *
   * Never throws.
   */
  assist: async (
    productId: string,
    request: SalesAssistRequest,
  ): Promise<SalesAssistOutcome> => {
    try {
      const response = await apiClient.post<SalesAssistResponse>(
        `${PRODUCTS_ENDPOINT}/${productId}/sales-assist`,
        request,
      );
      return { kind: 'ok', response: response.data };
    } catch (error) {
      return toOutcome(error);
    }
  },

  /**
   * Asks for the substitutes of a piece that the point of sale can sell today.
   *
   * Calls no model provider and answers in under a second. `pageSize` is left to the server's
   * configured default rather than chosen here, so the page the card declares is the one the
   * backend decided.
   *
   * Never throws. Note that the four substitute outcomes are **not** failures: they arrive
   * inside a perfectly good 200 and are told apart by `response.outcome`.
   */
  substitutes: async (
    productId: string,
    pointOfSaleId: string,
    pageSize?: number,
  ): Promise<SubstitutesRequestOutcome> => {
    try {
      const response = await apiClient.get<SubstitutesResponse>(
        `${PRODUCTS_ENDPOINT}/${productId}/substitutes`,
        { params: { pointOfSaleId, ...(pageSize ? { pageSize } : {}) } },
      );
      return { kind: 'ok', response: response.data };
    } catch (error) {
      return toOutcome(error);
    }
  },
};

export default salesAssistService;
