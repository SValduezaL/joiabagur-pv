/**
 * Assisted Search Service Tests (EP14 / C16)
 *
 * The mapping of failures is the substance here. The panel has to say four different things when
 * a search produces nothing, and two of them are decided by the status code rather than by the
 * body — so a service that collapsed them into one thrown error would make the interface lie.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

import { aiSearchService } from './ai-search.service';
import apiClient from './api.service';
import type { AssistedSearchResponse } from '@/types/ai-search.types';

vi.mock('./api.service', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const response: AssistedSearchResponse = {
  results: [],
  searchEventId: '11111111-1111-1111-1111-111111111111',
  aiAvailable: true,
  lowConfidence: false,
  pointOfSaleId: '22222222-2222-2222-2222-222222222222',
  candidatesReturned: 0,
  survivedHydration: 0,
};

const request = {
  query: 'un anillo de plata para regalar',
  pointOfSaleId: '22222222-2222-2222-2222-222222222222',
};

describe('aiSearchService.search', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should post to the relative ai search route when a search is issued', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: response });

    const outcome = await aiSearchService.search(request);

    // Relative on purpose: VITE_API_BASE_URL already carries `/api`, and duplicating it here is
    // the mistake this route has to be protected from.
    expect(apiClient.post).toHaveBeenCalledWith('/ai/search', request);
    expect(outcome).toEqual({ kind: 'ok', response });
  });

  it('should report a rate limit as its own outcome when the server answers 429', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce({ statusCode: 429, message: 'too many' });

    const outcome = await aiSearchService.search(request);

    // Not folded into a generic error: a caller must be able to tell "wait a few seconds" from
    // "the assisted search service is down", which have opposite remedies.
    expect(outcome).toEqual({ kind: 'rate-limited' });
  });

  it('should report a forbidden point of sale as its own outcome when the server answers 403', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce({ statusCode: 403, message: 'forbidden' });

    expect(await aiSearchService.search(request)).toEqual({ kind: 'forbidden' });
  });

  it('should surface the validation messages when the server answers 400 with an array', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce({
      statusCode: 400,
      message: 'bad request',
      errors: ['La búsqueda requiere un texto.'],
    });

    expect(await aiSearchService.search(request)).toEqual({
      kind: 'invalid',
      errors: ['La búsqueda requiere un texto.'],
    });
  });

  it('should surface the validation messages when the server answers 400 with a field dictionary', async () => {
    // Most controllers answer with a field-keyed dictionary while the AI endpoints answer with a
    // plain array. Both shapes reach the client, so both are handled.
    vi.mocked(apiClient.post).mockRejectedValueOnce({
      statusCode: 400,
      message: 'bad request',
      errors: { Query: ['La búsqueda requiere un texto.'] },
    });

    expect(await aiSearchService.search(request)).toEqual({
      kind: 'invalid',
      errors: ['La búsqueda requiere un texto.'],
    });
  });

  it('should fall back to the error message when a 400 carries no details', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce({ statusCode: 400, message: 'bad request' });

    expect(await aiSearchService.search(request)).toEqual({
      kind: 'invalid',
      errors: ['bad request'],
    });
  });

  it('should never throw when the transport fails', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce({ statusCode: 500, message: 'boom' });

    const outcome = await aiSearchService.search(request);

    expect(outcome).toEqual({ kind: 'error', message: 'boom' });
  });
});

describe('aiSearchService.reportSelection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should post the selected product to the event route when a result is selected', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: null });

    await aiSearchService.reportSelection('event-1', 'product-1');

    expect(apiClient.post).toHaveBeenCalledWith('/ai/search-events/event-1/selection', {
      productId: 'product-1',
    });
  });

  it('should resolve rather than reject when reporting the selection fails', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce({ statusCode: 404, message: 'gone' });

    // The caller does not await this in a click handler, so a rejection here would surface as an
    // unhandled promise rejection rather than as anything the operator could act on.
    await expect(aiSearchService.reportSelection('event-1', 'product-1')).resolves.toBeUndefined();
  });
});

/**
 * Availability (C40).
 *
 * The property worth holding is that this never reports a failure as an outage. The panel works
 * without knowing the switches, so a read that fails must degrade to "I could not tell" — saying
 * the assistant is down would be alarming about something that may well be fine.
 */
describe('aiSearchService.getAvailability', () => {
  it('should report both switches when the endpoint answers', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: {
        pointOfSaleId: 'pos-1',
        semanticSearchAvailable: true,
        assistedAnswerAvailable: false,
        assistedAnswerUnavailableReason: 'switched_off',
      },
    } as never);

    const outcome = await aiSearchService.getAvailability('pos-1');

    expect(outcome.kind).toBe('ok');
    if (outcome.kind !== 'ok') throw new Error('expected ok');
    expect(outcome.availability.semanticSearchAvailable).toBe(true);
    expect(outcome.availability.assistedAnswerAvailable).toBe(false);
    expect(outcome.availability.assistedAnswerUnavailableReason).toBe('switched_off');
  });

  it('should send the point of sale as a query parameter', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} } as never);

    await aiSearchService.getAvailability('pos-7');

    expect(apiClient.get).toHaveBeenCalledWith('/ai/search/availability', {
      params: { pointOfSaleId: 'pos-7' },
    });
  });

  it('should return an unknown outcome instead of throwing when the read fails', async () => {
    vi.mocked(apiClient.get).mockRejectedValue({ statusCode: 500 });

    const outcome = await aiSearchService.getAvailability('pos-1');

    // Not 'error', and not a rejection: the panel searches perfectly well without this, so a
    // failure here must not become a message the operator cannot act on.
    expect(outcome).toEqual({ kind: 'unknown' });
  });

  /**
   * C40_FIX, added by its independent verification: the branch this change introduced here had no
   * test of its own.
   *
   * **Omitted, never blanked.** The route reads the key not being there as the scope covering every
   * shop and refuses anything else, so sending `pointOfSaleId: ''` would turn the wider scope into
   * a validation error rather than the wider answer. Asserting on `params` being absent is the
   * point: a truthiness check is easy to "tidy" into a template string later, and nothing downstream
   * would catch it — the page test only sees that this function was called with `undefined`.
   */
  it('should omit the query parameter entirely when no point of sale is given', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} } as never);

    await aiSearchService.getAvailability();

    expect(apiClient.get).toHaveBeenCalledWith('/ai/search/availability', {
      params: undefined,
    });
  });
});

/**
 * The assisted route (C40).
 *
 * Same discipline as the semantic one — never throws, typed outcomes — and the rate-limit member
 * matters three times more here: this route's allowance is a third of search's.
 */
describe('aiSearchService.searchAssisted', () => {
  const assistedRequest = {
    query: '¿la plata se puede mojar?',
    pointOfSaleId: '22222222-2222-2222-2222-222222222222',
  };

  it('should post to the assisted endpoint, which is not the semantic one', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { groups: [] } } as never);

    await aiSearchService.searchAssisted(assistedRequest);

    // Two endpoints and not a `mode` field: a rate limit is an attribute of an endpoint, so one
    // route would have to pick a single allowance for both.
    expect(apiClient.post).toHaveBeenCalledWith('/ai/search/assisted', assistedRequest);
  });

  it('should keep a throttle distinguishable from an outage', async () => {
    vi.mocked(apiClient.post).mockRejectedValue({ statusCode: 429 });

    const outcome = await aiSearchService.searchAssisted(assistedRequest);

    // Opposite remedies: one resolves by waiting a few seconds, the other does not resolve by
    // waiting at all.
    expect(outcome).toEqual({ kind: 'rate-limited' });
    expect(outcome.kind).not.toBe('error');
  });

  it('should return a typed outcome instead of throwing on any failure', async () => {
    for (const [statusCode, kind] of [
      [403, 'forbidden'],
      [400, 'invalid'],
      [500, 'error'],
    ] as const) {
      vi.mocked(apiClient.post).mockRejectedValue({ statusCode });

      const outcome = await aiSearchService.searchAssisted(assistedRequest);

      expect(outcome.kind).toBe(kind);
    }
  });
});
