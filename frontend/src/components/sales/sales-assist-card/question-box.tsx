/**
 * Sale Card — the customer's question (EP15 / C36)
 *
 * The box that gives the knowledge corpus a route to the counter. The question is the customer's
 * and literal, so there is no prompting delegated here — but the five suggestions are baked into
 * the interface anyway, for a reason that was measured rather than assumed: **9 of 40** real
 * counter questions fell into "the documentation does not cover this question", and showing what
 * the corpus does answer raises that coverage.
 *
 * Each suggestion fills the field **and sends it, in one act**, the pattern the assisted search
 * panel's example queries already established: the suggestion is there to teach what can be
 * asked, and making the operator press again would waste the lesson.
 *
 * Two rules this component owns:
 *
 * - The question is refused **before being sent** when it is blank or over the limit, so an
 *   over-long question costs no paid request at all.
 * - It never leaves this component except through the submit callback, which puts it in the body
 *   of a POST. It is never written to the address of the page nor to router state, both of which
 *   end up in the browser's history.
 */

import { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { SUGGESTED_QUESTIONS, questionTooLongMessage } from '@/lib/assist-copy';
import { QUESTION_MAX_LENGTH } from '@/types/sales-assist.types';

interface QuestionBoxProps {
  /** Issues the second assist request. Called only with a question that already passed the bound. */
  onAsk: (question: string) => void;
  /** True while either request is in flight, so a second one cannot be started on top of it. */
  busy: boolean;
}

export function QuestionBox({ onAsk, busy }: QuestionBoxProps) {
  const [question, setQuestion] = useState('');
  const [error, setError] = useState<string | null>(null);

  const submit = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    if (trimmed.length > QUESTION_MAX_LENGTH) {
      // Refused here, so it never becomes a request. .NET validates the same bound, but a
      // round trip to be told the obvious costs one of the ten the operator has per minute.
      setError(questionTooLongMessage(QUESTION_MAX_LENGTH));
      return;
    }

    setError(null);
    onAsk(trimmed);
  };

  const handleSuggestion = (suggestion: string) => {
    setQuestion(suggestion);
    // Fills the field *and* asks, in one act.
    submit(suggestion);
  };

  return (
    <Card data-testid="assist-question-box">
      <CardHeader>
        <CardTitle className="text-base">¿Te ha preguntado algo el cliente?</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((suggestion) => (
            <Button
              key={suggestion}
              variant="outline"
              size="sm"
              disabled={busy}
              onClick={() => handleSuggestion(suggestion)}
            >
              <Sparkles className="me-1.5 size-3.5" />
              {suggestion}
            </Button>
          ))}
        </div>

        <div className="space-y-2">
          <Label htmlFor="assist-question">Pregunta del cliente</Label>
          <Textarea
            id="assist-question"
            rows={3}
            placeholder="¿Se puede duchar con ella?"
            value={question}
            onChange={(e) => {
              setQuestion(e.target.value);
              if (error) setError(null);
            }}
            disabled={busy}
          />
          <div className="flex items-center justify-between gap-2">
            <span
              className="text-xs text-muted-foreground"
              data-testid="assist-question-counter"
            >
              {question.length} / {QUESTION_MAX_LENGTH}
            </span>
            <Button
              onClick={() => submit(question)}
              disabled={!question.trim() || busy}
            >
              <Send className="me-2 size-4" />
              Preguntar
            </Button>
          </div>
          {error ? (
            <p className="text-sm text-destructive" data-testid="assist-question-error">
              {error}
            </p>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

export default QuestionBox;
