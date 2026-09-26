import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ScanLine, PenLine, History, ShoppingCart, Sparkles } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AgentEntryCard } from '@/components/sales/agent/agent-entry-card';
import { useCart } from '@/providers/cart-provider';
import { ROUTES } from '@/routing/routes';
import { aiSearchService } from '@/services/ai-search.service';
import type { AiSearchAvailability } from '@/types/ai-search.types';

export function SalesPage() {
  const { lineCount } = useCart();

  /**
   * The agent's gate, read **on mount** rather than on press (C42).
   *
   * The probe makes no AI call, consumes no request-rate quota and runs no model — that is its
   * entire reason for existing — so asking before the operator acts costs nothing, and it is the
   * only way the card can state that the agent is off *before* somebody presses a button with
   * nothing behind it.
   *
   * **No point of sale is named**, so this reads the default state of the deployment: the landing
   * page has no shop selector, and the agent's own panel reads the probe again for whichever shop
   * is chosen there. Inventing a shop here to have something to send would report about a scope
   * nobody asked about.
   */
  const [availability, setAvailability] = useState<AiSearchAvailability | null>(null);
  const [settled, setSettled] = useState(false);

  useEffect(() => {
    let current = true;

    aiSearchService.getAvailability().then((outcome) => {
      if (!current) return;
      setAvailability(outcome.kind === 'ok' ? outcome.availability : null);
      setSettled(true);
    });

    return () => {
      current = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Ventas</h1>
          <p className="text-muted-foreground">
            Registra ventas en punto de venta
          </p>
        </div>
        <div className="flex gap-2">
          {lineCount > 0 && (
            <Button variant="default" size="sm" asChild>
              <Link to={ROUTES.SALES.CART}>
                <ShoppingCart className="mr-2 h-4 w-4" />
                Carrito
                <Badge variant="secondary" className="ml-2">
                  {lineCount}
                </Badge>
              </Link>
            </Button>
          )}
          <Button variant="outline" size="sm" asChild>
            <Link to={ROUTES.SALES.HISTORY}>
              <History className="mr-2 h-4 w-4" />
              Historial
            </Link>
          </Button>
        </div>
      </div>

      {/* Registration Options */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Barcode/QR Scanning */}
        <Card className="cursor-pointer transition-shadow hover:shadow-lg">
          <Link to={ROUTES.SALES.NEW_SCAN}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ScanLine className="h-5 w-5 text-primary" />
                Escanear Código
              </CardTitle>
              <CardDescription>
                Escanea el código de barras o QR del producto para una selección instantánea
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="space-y-1 text-sm text-muted-foreground">
                  <p>• Escanea código de barras o QR</p>
                  <p>• Selección instantánea del producto</p>
                  <p>• Ingreso manual como alternativa</p>
                </div>
                <ScanLine className="h-12 w-12 text-muted-foreground/50" />
              </div>
              <Button className="mt-4 w-full">
                Escanear Código
              </Button>
            </CardContent>
          </Link>
        </Card>

        {/* Manual Registration */}
        <Card className="cursor-pointer transition-shadow hover:shadow-lg">
          <Link to={ROUTES.SALES.NEW}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PenLine className="h-5 w-5 text-primary" />
                Registro Manual
              </CardTitle>
              <CardDescription>
                Busca productos por SKU o nombre y registra la venta manualmente
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="space-y-1 text-sm text-muted-foreground">
                  <p>• Búsqueda por SKU o nombre</p>
                  <p>• Selección de método de pago</p>
                  <p>• Cantidad editable</p>
                </div>
                <ShoppingCart className="h-12 w-12 text-muted-foreground/50" />
              </div>
              <Button className="mt-4 w-full">
                Registrar Venta Manual
              </Button>
            </CardContent>
          </Link>
        </Card>

        {/* Assisted natural-language search. Third entry method: it selects a product and hands
            it to the manual flow, which keeps owning quantity, payment method and stock. */}
        <Card className="cursor-pointer transition-shadow hover:shadow-lg">
          <Link to={ROUTES.SALES.NEW_ASSISTED}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                Buscar con Ayuda
              </CardTitle>
              <CardDescription>
                Describe la pieza con tus palabras y encuentra lo que hay en tu tienda
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="space-y-1 text-sm text-muted-foreground">
                  <p>• Búsqueda en lenguaje natural</p>
                  <p>• Filtros por material y tipo de pieza</p>
                  <p>• Precio y stock reales de tu punto de venta</p>
                </div>
                <Sparkles className="h-12 w-12 text-muted-foreground/50" />
              </div>
              <Button className="mt-4 w-full">
                Buscar con Ayuda
              </Button>
            </CardContent>
          </Link>
        </Card>

        {/* The sale agent. Fourth entry method (C42), and a route of its own rather than a toggle
            inside the card above: that panel is one query producing one set of results, and this is
            a conversation. Its gate has three states and the card reads the probe on mount. */}
        <AgentEntryCard availability={availability} settled={settled} />
      </div>
    </div>
  );
}

export default SalesPage;
