/**
 * Sale Assist Service Tests (EP15 / C36)
 *
 * The substance is the mapping of failures, exactly as it is for the assisted search service.
 * Two of the card's sentences are decided by the status code and not by the body — "wait a few
 * seconds" and "this shop does not carry this piece" — so a service that collapsed them into one
 * thrown error would make the screen lie about what happened and about what to do next.
 *
 * The other half of the substance is that **nothing here throws**. The card is used standing at
 * the counter with a customer in front of the operator, and an unhandled rejection there is a
 * blank screen.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

import { salesAssistService } from './sales-assist.service';
import apiClient from './api.service';
import type {
  SalesAssistResponse,
  SubstitutesResponse,
} from '@/types/sales-assist.types';

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

const PRODUCT_ID = '33333333-3333-3333-3333-333333333333';
const POS_ID = '22222222-2222-2222-2222-222222222222';

const assistResponse: SalesAssistResponse = {
  aiAvailable: true,
  pointOfSaleId: POS_ID,
  productId: PRODUCT_ID,
  intent: 'product_pitch',
  groups: [],
  pitch: 'Una pieza de plata de ley.',
  pitchStatus: 'generated',
  citations: [],
  warnings: [],
  clarificationQuestion: null,
  promptVersion: 'v1',
  traceId: 'trace-1',
};

const substitutesResponse: SubstitutesResponse = {
  outcome: 'ok',
  results: [],
  candidatesReturned: 5,
  survivedHydration: 3,
  pointOfSaleId: POS_ID,
  traceId: 'trace-2',
};

/** Every status code the two routes can answer with, and the member each one must fall into. */
const FAILURES = [
  { statusCode: 429, expected: { kind: 'rate-limited' } },
  { statusCode: 403, expected: { kind: 'forbidden' } },
  { statusCode: 404, expected: { kind: 'not-found' } },
  { statusCode: 401, expected: { kind: 'error' } },
  { statusCode: 500, expected: { kind: 'error' } },
] as const;

describe('salesAssistService.assist', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should post to the relative sales assist route when a card is requested', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: assistResponse } as never);

    const outcome = await salesAssistService.assist(PRODUCT_ID, { pointOfSaleId: POS_ID });

    // Relative on purpose: VITE_API_BASE_URL already carries `/api`.
    expect(apiClient.post).toHaveBeenCalledWith(
      `/ai/products/${PRODUCT_ID}/sales-assist`,
      { pointOfSaleId: POS_ID },
    );
    expect(outcome).toEqual({ kind: 'ok', response: assistResponse });
  });

  it('should send the question in the body when one is asked', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: assistResponse } as never);

    await salesAssistService.assist(PRODUCT_ID, {
      pointOfSaleId: POS_ID,
      question: '¿Se puede mojar?',
    });

    // The body, and only the body. The question is free text about a customer, and a URL is
    // recorded by the proxy's access log, the browser's history and any intermediate cache.
    const [url, body] = vi.mocked(apiClient.post).mock.calls[0];
    expect(url).not.toContain('mojar');
    expect(body).toEqual({ pointOfSaleId: POS_ID, question: '¿Se puede mojar?' });
  });

  it('should distinguish a rate limited response from an unavailable service', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce({ statusCode: 429, message: 'too many' });
    const limited = await salesAssistService.assist(PRODUCT_ID, { pointOfSaleId: POS_ID });

    vi.mocked(apiClient.post).mockRejectedValueOnce({ statusCode: 503, message: 'down' });
    const down = await salesAssistService.assist(PRODUCT_ID, { pointOfSaleId: POS_ID });

    // Exceeding the budget is the system protecting itself and the operator only has to wait;
    // an outage is a fault. Opposite remedies, so they may never share a member.
    expect(limited).toEqual({ kind: 'rate-limited' });
    expect(down.kind).toBe('error');
    expect(limited).not.toEqual(down);
  });

  it('should report a piece the shop does not carry as its own outcome when the server answers 404', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce({ statusCode: 404, message: 'not found' });

    // C34 answers this before calling the AI at all, so it is not a failure of the assistant:
    // it is an answer about the assortment, and it deserves its own sentence.
    expect(await salesAssistService.assist(PRODUCT_ID, { pointOfSaleId: POS_ID })).toEqual({
      kind: 'not-found',
    });
  });

  it.each(FAILURES)(
    'should map status $statusCode to its own member when the request fails',
    async ({ statusCode, expected }) => {
      vi.mocked(apiClient.post).mockRejectedValueOnce({ statusCode, message: 'failed' });

      const outcome = await salesAssistService.assist(PRODUCT_ID, { pointOfSaleId: POS_ID });

      expect(outcome.kind).toBe(expected.kind);
    },
  );

  it('should pass through the backend validation messages when the request is refused as invalid', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce({
      statusCode: 400,
      message: 'bad request',
      errors: ['El punto de venta no existe o no está activo.'],
    });

    // Already written in Spanish by .NET, so they are surfaced rather than replaced by a
    // generic sentence that would say less than the server already said.
    expect(await salesAssistService.assist(PRODUCT_ID, { pointOfSaleId: POS_ID })).toEqual({
      kind: 'invalid',
      errors: ['El punto de venta no existe o no está activo.'],
    });
  });

  it('should flatten a field keyed validation body when the server answers with one', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce({
      statusCode: 400,
      message: 'bad request',
      errors: { question: ['La pregunta es demasiado larga.'] },
    });

    // Both shapes reach this service: most controllers key errors by field, the AI endpoints
    // answer with a plain array. Assuming one of them would drop the other's messages.
    expect(await salesAssistService.assist(PRODUCT_ID, { pointOfSaleId: POS_ID })).toEqual({
      kind: 'invalid',
      errors: ['La pregunta es demasiado larga.'],
    });
  });

  it('should never propagate an exception when the client rejects with something unexpected', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce(new Error('Network Error'));

    // Not `rejects`: the point is that there is nothing to reject. A thrown error here is a
    // blank screen at the counter.
    const outcome = await salesAssistService.assist(PRODUCT_ID, { pointOfSaleId: POS_ID });

    expect(outcome.kind).toBe('error');
  });
});

describe('salesAssistService.substitutes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should get the relative substitutes route scoped to the point of sale', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: substitutesResponse } as never);

    const outcome = await salesAssistService.substitutes(PRODUCT_ID, POS_ID);

    expect(apiClient.get).toHaveBeenCalledWith(
      `/ai/products/${PRODUCT_ID}/substitutes`,
      { params: { pointOfSaleId: POS_ID } },
    );
    expect(outcome).toEqual({ kind: 'ok', response: substitutesResponse });
  });

  it('should leave the page size to the server when none is given', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: substitutesResponse } as never);

    await salesAssistService.substitutes(PRODUCT_ID, POS_ID);

    // The page the card declares has to be the one the backend decided, so the default is not
    // duplicated here where it could drift from the configured one.
    const [, config] = vi.mocked(apiClient.get).mock.calls[0] as [string, { params: object }];
    expect(config.params).not.toHaveProperty('pageSize');
  });

  it('should send the page size when one is given', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: substitutesResponse } as never);

    await salesAssistService.substitutes(PRODUCT_ID, POS_ID, 3);

    expect(apiClient.get).toHaveBeenCalledWith(
      `/ai/products/${PRODUCT_ID}/substitutes`,
      { params: { pointOfSaleId: POS_ID, pageSize: 3 } },
    );
  });

  it.each(FAILURES)(
    'should map status $statusCode to its own member when the substitutes request fails',
    async ({ statusCode, expected }) => {
      vi.mocked(apiClient.get).mockRejectedValueOnce({ statusCode, message: 'failed' });

      const outcome = await salesAssistService.substitutes(PRODUCT_ID, POS_ID);

      expect(outcome.kind).toBe(expected.kind);
    },
  );

  it('should never propagate an exception when the client rejects with something unexpected', async () => {
    vi.mocked(apiClient.get).mockRejectedValueOnce(new Error('Network Error'));

    expect((await salesAssistService.substitutes(PRODUCT_ID, POS_ID)).kind).toBe('error');
  });

  it('should treat the four substitute outcomes as answers and not as failures', async () => {
    // They arrive inside a perfectly good 200 and are told apart by `outcome`. A service that
    // mapped `ai_unavailable` to an error member would make the card unable to say the four
    // different things the spec requires of it.
    for (const outcome of ['ok', 'none_in_stock', 'product_not_indexed', 'ai_unavailable'] as const) {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        data: { ...substitutesResponse, outcome },
      } as never);

      const result = await salesAssistService.substitutes(PRODUCT_ID, POS_ID);

      expect(result.kind).toBe('ok');
      expect(result.kind === 'ok' && result.response.outcome).toBe(outcome);
    }
  });
});
