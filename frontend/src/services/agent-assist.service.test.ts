/**
 * Sale Agent Service Tests (EP15 / C42)
 *
 * The mapping of failures is the substance here, and on this route more than on its siblings: the
 * quota that binds the agent is tokens per minute at roughly one request a minute, so a throttle is
 * the likeliest of the four failures — and it is the one whose remedy is simply waiting. A service
 * that collapsed the four into one thrown error would make the thread say the wrong thing about
 * three of them.
 *
 * Mocked at the api client with `vi.mock` rather than handled by MSW: an unhandled MSW request only
 * warns, so a test can pass having asserted nothing at all.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

import { agentAssistService } from './agent-assist.service';
import apiClient from './api.service';
import type { AgentAssistRequest, AgentAssistResponse } from '@/types/ai-agent.types';

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

const response: AgentAssistResponse = {
  groups: [],
  pitchStatus: 'generated',
  citations: [],
  warnings: [],
  abstained: false,
  aiAvailable: true,
  partial: false,
  stopReason: 'sin_mas_herramientas',
  iterations: 2,
  toolCallsUsed: 3,
  trace: [],
  agentPromptVersion: 'assist/v6',
  candidatesReturned: 0,
  survivedHydration: 0,
};

const request: AgentAssistRequest = {
  turns: [{ role: 'operario', text: 'busco un anillo de plata' }],
  pointOfSaleId: '22222222-2222-2222-2222-222222222222',
};

describe('agentAssistService.answer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should post the whole transcript to the relative agent route when a turn is sent', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: response });

    const outcome = await agentAssistService.answer(request);

    expect(apiClient.post).toHaveBeenCalledWith('/ai/search/agent', request);
    expect(outcome).toEqual({ kind: 'ok', response });
  });

  it('should send every turn including the assistant ones when the thread has history', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: response });

    // The service keeps no conversation, so the caller owns the context. An assistant turn that
    // never left would strand the deictic reference of the turn after it.
    await agentAssistService.answer({
      turns: [
        { role: 'operario', text: 'busco un anillo' },
        { role: 'asistente', text: 'te enseño estos dos' },
        { role: 'operario', text: '¿y en dorado?' },
      ],
    });

    const sent = vi.mocked(apiClient.post).mock.calls[0][1] as AgentAssistRequest;
    expect(sent.turns).toHaveLength(3);
    expect(sent.turns.map((turn) => turn.role)).toEqual(['operario', 'asistente', 'operario']);
  });

  it('should omit the point of sale rather than blank it when the scope is every shop', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: response });

    await agentAssistService.answer({ turns: request.turns });

    const sent = vi.mocked(apiClient.post).mock.calls[0][1] as AgentAssistRequest;
    expect('pointOfSaleId' in sent).toBe(false);
  });

  it('should report a rate limit as its own outcome when the allowance is spent', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce({ statusCode: 429 });

    const outcome = await agentAssistService.answer(request);

    // Never folded into an error: waiting fixes one of these and does nothing for the other.
    expect(outcome).toEqual({ kind: 'rate-limited' });
  });

  it('should report a forbidden shop as its own outcome when the shop is not assigned', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce({ statusCode: 403 });

    const outcome = await agentAssistService.answer(request);

    expect(outcome).toEqual({ kind: 'forbidden' });
  });

  it('should carry the cap messages through when the transcript is refused', async () => {
    // What the composer shows: the message names which of the three caps was exceeded.
    vi.mocked(apiClient.post).mockRejectedValueOnce({
      statusCode: 400,
      errors: ['La conversación no puede pasar de 4000 caracteres en total, sumando todos los turnos.'],
    });

    const outcome = await agentAssistService.answer(request);

    expect(outcome).toEqual({
      kind: 'invalid',
      errors: ['La conversación no puede pasar de 4000 caracteres en total, sumando todos los turnos.'],
    });
  });

  it('should flatten a field-keyed error dictionary when the API answers with one', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce({
      statusCode: 400,
      errors: { Turns: ['La conversación tiene que llevar al menos un turno del operario.'] },
    });

    const outcome = await agentAssistService.answer(request);

    expect(outcome).toEqual({
      kind: 'invalid',
      errors: ['La conversación tiene que llevar al menos un turno del operario.'],
    });
  });

  it('should fall back to a neutral message when a rejection carries no detail', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce({ statusCode: 400 });

    const outcome = await agentAssistService.answer(request);

    expect(outcome).toEqual({ kind: 'invalid', errors: ['La conversación no es válida.'] });
  });

  it('should report an unclassified failure as an error when the status is unknown', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce({ statusCode: 500, message: 'boom' });

    const outcome = await agentAssistService.answer(request);

    expect(outcome).toEqual({ kind: 'error', message: 'boom' });
  });

  it('should never throw when the client rejects with nothing usable', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce(undefined);

    const outcome = await agentAssistService.answer(request);

    // The thread must be able to say something true rather than showing an application error.
    expect(outcome).toEqual({ kind: 'error', message: 'No se pudo contestar el turno.' });
  });

  it('should return a degraded answer as an answer when the loop reports its provider failed', async () => {
    // A 200 carrying `fallo_proveedor` is a response, not a failure: the backend does not convert
    // it and neither does this. The block has copy for all ten stop reasons for exactly this.
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: { ...response, partial: true, stopReason: 'fallo_proveedor', aiAvailable: true },
    });

    const outcome = await agentAssistService.answer(request);

    expect(outcome.kind).toBe('ok');
    expect(outcome.kind === 'ok' && outcome.response.stopReason).toBe('fallo_proveedor');
  });
});
