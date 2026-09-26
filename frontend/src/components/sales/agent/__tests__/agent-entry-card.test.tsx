/**
 * The agent's entry card and its three-state gate (EP15 / C42)
 *
 * **The third state is what these tests are for.** A probe that cannot answer must not close a door
 * that may well work — that is the rule the assisted panel's badge already follows, and the failure
 * behind it is the one this family of changes keeps being opened to remove: a screen presenting a
 * capability as available when it is off, or as off when it works.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

import type { AiSearchAvailability } from '@/types/ai-search.types';
import { AgentEntryCard, agentGateState, agentUnavailableText } from '../agent-entry-card';

function availability(overrides: Partial<AiSearchAvailability> = {}): AiSearchAvailability {
  return {
    pointOfSaleId: null,
    semanticSearchAvailable: true,
    assistedAnswerAvailable: true,
    agentAvailable: true,
    ...overrides,
  };
}

function renderCard(props: { availability: AiSearchAvailability | null; settled: boolean }) {
  return render(
    <BrowserRouter>
      <AgentEntryCard {...props} />
    </BrowserRouter>,
  );
}

describe('the gate state', () => {
  it('should open the agent card when the probe says the agent is on', () => {
    expect(agentGateState(availability({ agentAvailable: true }), true)).toBe('available');
  });

  it('should close the agent card when the probe says the agent is off', () => {
    expect(agentGateState(availability({ agentAvailable: false }), true)).toBe('unavailable');
  });

  it('should open the agent card when the probe cannot answer', () => {
    // Null is «the read failed». Closing here would refuse a capability that may well be working.
    expect(agentGateState(null, true)).toBe('unknown');
  });

  it('should treat a probe that never mentions the agent as unknown rather than off', () => {
    // A backend predating C42 leaves the field undefined. Reading that as false would close the door
    // on every deployment not yet updated, which is the opposite of what the third state is for.
    expect(agentGateState(availability({ agentAvailable: undefined }), true)).toBe('unknown');
  });

  it('should hold the state as unknown while the read is still in flight', () => {
    expect(agentGateState(availability(), false)).toBe('unknown');
  });
});

describe('the card', () => {
  it('should offer the agent as an entry method when it is available', () => {
    renderCard({ availability: availability(), settled: true });

    const button = screen.getByRole('button', { name: /preguntar al agente/i });
    expect(button).toBeEnabled();
    // Activating it navigates to the agent's own route, not into the assisted panel.
    expect(screen.getByRole('link')).toHaveAttribute('href', '/sales/new/agent');
  });

  it('should close the agent card when the probe says the agent is off', () => {
    renderCard({
      availability: availability({ agentAvailable: false, agentUnavailableReason: 'switched_off' }),
      settled: true,
    });

    expect(screen.getByRole('button', { name: /preguntar al agente/i })).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent(/desactivado/i);
    // No link at all: a greyed-out button on a clickable surface is the bug this avoids.
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('should open the agent card when the probe cannot answer', () => {
    renderCard({ availability: null, settled: true });

    expect(screen.getByRole('button', { name: /preguntar al agente/i })).toBeEnabled();
    expect(screen.getByRole('status')).toHaveTextContent(/no se pudo confirmar/i);
  });

  it('should show the agent reason and not the assisted answer reason', () => {
    // The state this exists for: the agent has a credential chain of its own, so the two switches
    // are independent — and showing the wrong one explains the wrong switch.
    renderCard({
      availability: availability({
        assistedAnswerAvailable: true,
        assistedAnswerUnavailableReason: null,
        agentAvailable: false,
        agentUnavailableReason: 'switched_off',
      }),
      settled: true,
    });

    const status = screen.getByRole('status');
    expect(status).toHaveTextContent(/el agente est/i);
    expect(status).not.toHaveTextContent(/respuesta asistida/i);
  });

  it('should say nothing about availability while the read is in flight', () => {
    renderCard({ availability: null, settled: false });

    // Neither closed nor warning: the card is simply usable, as it was before the probe existed.
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /preguntar al agente/i })).toBeEnabled();
  });

  it('should state that the agent is slower and dearer than the assisted search', () => {
    renderCard({ availability: availability(), settled: true });

    // The trade-off, on the door rather than after the bill: this route costs several times the
    // deterministic one, measured.
    expect(screen.getByText(/m.s lento y m.s caro/i)).toBeInTheDocument();
  });
});

describe('the unavailable copy', () => {
  it('should name the switch when that is what is off', () => {
    expect(agentUnavailableText('switched_off')).toMatch(/desactivado/i);
  });

  it('should fall back to a neutral phrase for a reason it does not know', () => {
    expect(agentUnavailableText('algo_nuevo')).toBe('El agente no está disponible ahora mismo');
    expect(agentUnavailableText(null)).toBe('El agente no está disponible ahora mismo');
  });
});
