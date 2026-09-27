/**
 * Sale Card — warnings (EP15 / C36)
 *
 * Four codes with Spanish of their own, and a neutral label for anything else. Nothing is added
 * that the backend did not emit, and nothing it emitted is removed — the missing size label is
 * not removed either, it is rendered by the header as an attribute of the piece.
 *
 * The raw code is never shown: it is engineering vocabulary and says nothing at a counter.
 */

import { AlertTriangle } from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { alertWarnings, isKnownWarning, warningLabel } from '@/lib/assist-copy';

interface WarningsBlockProps {
  warnings: readonly string[];
}

export function WarningsBlock({ warnings }: WarningsBlockProps) {
  const codes = alertWarnings(warnings);

  if (codes.length === 0) return null;

  return (
    <Alert variant="warning" data-testid="assist-warnings">
      <AlertTriangle className="size-4" />
      <AlertTitle>A tener en cuenta</AlertTitle>
      <AlertDescription>
        <ul className="list-disc space-y-1 ps-4">
          {codes.map((code) => (
            <li
              key={code}
              data-testid="assist-warning"
              /* So a test can tell a translated row from a degraded one without reading the
                 code itself, which is never rendered. */
              data-known={isKnownWarning(code) ? 'true' : 'false'}
            >
              {warningLabel(code)}
            </li>
          ))}
        </ul>
      </AlertDescription>
    </Alert>
  );
}

export default WarningsBlock;
