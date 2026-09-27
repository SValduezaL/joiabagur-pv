/**
 * Sale Agent Service (EP15 / C42)
 *
 * One call: answering the last turn of a conversation. The availability probe is the free query's
 * — it reports all three paths from one read, which is what keeps the two sibling panels from
 * disagreeing about what is switched on — and reporting a selection is the search-event route's,
 * reused rather than duplicated.
 *
 * Routes are relative: `VITE_API_BASE_URL` already carries `/api`.
 */

import apiClient from './api.service';
import type {
  AgentAssistOutcome,
  AgentAssistRequest,
  AgentAssistResponse,
} from '@/types/ai-agent.types';
import type { SearchFailureOutcome } from '@/types/ai-search.types';
import type { ApiError } from '@/types/api.types';

const AGENT_ENDPOINT = '/ai/search/agent';

/**
 * Flattens the two validation-error shapes the API produces.
 *
 * `ApiError.errors` is typed as a field-keyed dictionary because that is what most controllers
 * return, but the AI endpoints answer with a plain array of messages. Both reach here, so both are
 * handled rather than one of them being assumed — and on this route the messages matter: they name
 * which of the three transcript caps was exceeded, which is what the composer shows the operator.
 */
function toMessages(errors: ApiError['errors'] | string[] | undefined): string[] {
  if (!errors) return [];
  if (Array.isArray(errors)) return errors;
  return Object.values(errors).flat();
}

function toOutcome(error: unknown): SearchFailureOutcome {
  const apiError = error as ApiError;

  switch (apiError?.statusCode) {
    // A member of its own, and on this route it is the likeliest failure of the four: the quota
    // that binds the agent is tokens per minute, at roughly one request a minute. Exceeding the
    // allowance resolves by waiting; an outage does not resolve by waiting at all.
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
          : [apiError.message ?? 'La conversación no es válida.'],
      };
    }

    default:
      return {
        kind: 'error',
        message: apiError?.message ?? 'No se pudo contestar el turno.',
      };
  }
}

export const agentAssistService = {
  /**
   * Answers one turn of a conversation.
   *
   * **Never throws**: every failure is mapped to a typed outcome so the thread can say something
   * true rather than showing an application error. A degradation the loop reports inside a
   * successful response — its provider fell, no credential is configured, a budget cut it short —
   * arrives here as an answer carrying its stop reason, not as a failure, which is why the block
   * has copy for all ten stop reasons.
   *
   * **The whole transcript travels on every call.** The service stores no conversation, so the
   * caller owns the context — and owns the cost, which is why the composer counts the three caps
   * before this is reached.
   */
  answer: async (request: AgentAssistRequest): Promise<AgentAssistOutcome> => {
    try {
      const response = await apiClient.post<AgentAssistResponse>(AGENT_ENDPOINT, request);
      return { kind: 'ok', response: response.data };
    } catch (error) {
      return toOutcome(error);
    }
  },
};

export default agentAssistService;
