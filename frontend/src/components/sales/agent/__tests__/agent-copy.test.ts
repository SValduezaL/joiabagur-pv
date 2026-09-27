/**
 * The copy of the agent panel (EP15 / C42)
 *
 * **The ten stop reasons, walked one by one**, because a value the service publishes and this table
 * does not carry would reach the screen as a neutral phrase where a real one exists — and the
 * neutral phrase is the fallback for the unknown case, not a licence to leave a known one out.
 */

import { describe, it, expect } from 'vitest';

import {
  AGENT_WARNING_COPY,
  BUDGET_STOP_REASONS,
  ORIGIN_COPY,
  STOP_REASON_COPY,
  UNKNOWN_STOP_REASON,
  agentWarningText,
  degradedReasonText,
  isBudgetStop,
  originText,
  stopReasonText,
} from '../agent-copy';

/** `AGENT_STOP_REASONS` on the service side, in its declared order. */
const TEN_STOP_REASONS = [
  'sin_mas_herramientas',
  'presupuesto_iteraciones',
  'presupuesto_tools',
  'presupuesto_tokens',
  'presupuesto_contexto',
  'presupuesto_reloj',
  'aclaracion',
  'rechazado',
  'sin_cliente',
  'fallo_proveedor',
];

describe('stop reason copy', () => {
  it('should state every one of the ten stop reasons in Spanish', () => {
    expect(Object.keys(STOP_REASON_COPY).sort()).toEqual([...TEN_STOP_REASONS].sort());

    for (const reason of TEN_STOP_REASONS) {
      const text = stopReasonText(reason);

      expect(text).not.toBe(UNKNOWN_STOP_REASON);
      expect(text.length).toBeGreaterThan(0);
    }
  });

  it('should give a different statement to each of the ten', () => {
    const statements = TEN_STOP_REASONS.map(stopReasonText);

    // Two reasons sharing a sentence would make the strip unable to tell them apart, which is the
    // whole reason the vocabulary is closed and has ten members rather than three.
    expect(new Set(statements).size).toBe(TEN_STOP_REASONS.length);
  });

  it('should show a neutral statement when the stop reason is not recognised', () => {
    expect(stopReasonText('un_valor_que_no_existe')).toBe(UNKNOWN_STOP_REASON);
    expect(stopReasonText(UNKNOWN_STOP_REASON)).toBe(UNKNOWN_STOP_REASON);
  });

  it('should show a neutral statement rather than a blank when no stop reason arrives', () => {
    expect(stopReasonText(null)).toBe(UNKNOWN_STOP_REASON);
    expect(stopReasonText(undefined)).toBe(UNKNOWN_STOP_REASON);
    expect(stopReasonText('')).toBe(UNKNOWN_STOP_REASON);
  });

  it('should name what ran out on each of the five budget reasons', () => {
    // «Incompleta» alone explains nothing; the operator needs to know whether to rephrase, narrow
    // the question or simply ask again. So each phrase says it is incomplete AND names the budget,
    // which is the clause after the colon — not necessarily with the word «agotó», because one of
    // the five is the accumulated context reaching its ceiling rather than something running out.
    for (const reason of BUDGET_STOP_REASONS) {
      const text = stopReasonText(reason);

      expect(text).toContain('incompleta');

      const named = text.split(':')[1]?.trim() ?? '';
      expect(named.length).toBeGreaterThan(10);
    }
  });

  it('should tell a budget stop from a complete one', () => {
    expect(isBudgetStop('presupuesto_tools')).toBe(true);
    expect(isBudgetStop('presupuesto_reloj')).toBe(true);

    // Neither of these is a budget: one is a complete answer, the other a refusal, and the third a
    // provider fault — which is a degradation but not an exhausted budget.
    expect(isBudgetStop('sin_mas_herramientas')).toBe(false);
    expect(isBudgetStop('rechazado')).toBe(false);
    expect(isBudgetStop('fallo_proveedor')).toBe(false);
    expect(isBudgetStop(null)).toBe(false);
  });

  it('should not describe a clarification or a refusal as an incomplete answer', () => {
    // A clarification is a normal outcome of a conversation and a refusal is a complete answer to a
    // request this shop will not serve. Wording either as «incompleta» would be false.
    expect(stopReasonText('aclaracion')).not.toContain('incompleta');
    expect(stopReasonText('rechazado')).not.toContain('incompleta');
  });
});

describe('group provenance copy', () => {
  it('should label a substitutes group as alternatives and never as matches', () => {
    expect(originText('sustitutos')).toBe('Alternativas');
    expect(originText('sustitutos')).not.toBe(ORIGIN_COPY.catalogo);
  });

  it('should label a catalogue group as matches', () => {
    expect(originText('catalogo')).toBe('Coincidencias');
  });

  it('should fall back to a neutral heading when the provenance is not recognised', () => {
    // Never «Coincidencias» by default: claiming a match for a group of unknown provenance is the
    // exact failure the marker exists to prevent.
    expect(originText('algo_nuevo')).toBe('Piezas');
    expect(originText(null)).toBe('Piezas');
  });
});

describe('degradation and warning copy', () => {
  it('should state each degradation reason the backend can report', () => {
    for (const reason of [
      'switched_off',
      'credential_rejected',
      'not_implemented',
      'not_indexed',
      'ai_unavailable',
      'unclassified',
    ]) {
      expect(degradedReasonText(reason)).not.toBe('El agente no está disponible ahora mismo');
    }
  });

  it('should fall back to a neutral phrase when the degradation reason is unknown', () => {
    expect(degradedReasonText('algo_nuevo')).toBe('El agente no está disponible ahora mismo');
    expect(degradedReasonText(null)).toBe('El agente no está disponible ahora mismo');
  });

  it('should state the four warnings that describe the conversation', () => {
    expect(Object.keys(AGENT_WARNING_COPY).sort()).toEqual([
      'filters_too_narrow',
      'knowledge_not_covered',
      'query_not_in_catalogue',
      'query_out_of_domain',
    ]);
  });

  it('should show the raw code rather than a guess when a warning is not recognised', () => {
    // Visible and ugly beats invisible: an unknown code on screen is a bug report, and a blank is a
    // warning the operator never sees.
    expect(agentWarningText('un_codigo_nuevo')).toBe('un_codigo_nuevo');
  });
});
