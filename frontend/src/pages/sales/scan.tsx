import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { CameraOff, Flashlight, FlashlightOff, X, ScanLine, Search, FileText } from 'lucide-react';
import { toast } from 'sonner';
import { BarcodeScanningService } from '@/services/barcode-scanning.service';
import { productService } from '@/services/product.service';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ROUTES } from '@/routing/routes';

type ScanState = 'initializing' | 'scanning' | 'error' | 'success';

/** The piece a scan resolved to, kept only so the sale card can be offered for it (C36). */
interface ResolvedProduct {
  id: string;
  name: string;
  sku: string;
}

export function ScanningPage() {
  const navigate = useNavigate();
  const [scanState, setScanState] = useState<ScanState>('initializing');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [flashOn, setFlashOn] = useState(false);
  const [manualSku, setManualSku] = useState('');
  const [isSubmittingManual, setIsSubmittingManual] = useState(false);
  /**
   * The resolved piece, held back from the till for one step so the operator can open its sale
   * card instead (C36).
   *
   * This is the entrance that matters most for the card: the customer has the piece in their
   * hand and is asking about it, and before C36 that situation had no route to the knowledge
   * corpus at all. This page has no point of sale of its own, so none travels — the card offers
   * its role-resolved selector instead.
   */
  const [resolved, setResolved] = useState<ResolvedProduct | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const serviceRef = useRef<BarcodeScanningService | null>(null);

  const isCompatible = useCallback(() => {
    return !!(navigator.mediaDevices?.getUserMedia);
  }, []);

  useEffect(() => {
    if (!isCompatible()) {
      setScanState('error');
      setErrorMessage('Permiso de cámara denegado');
      return;
    }

    const service = new BarcodeScanningService();
    serviceRef.current = service;

    const initCamera = async () => {
      try {
        if (!videoRef.current) return;
        await service.startCamera(videoRef.current);
        setScanState('scanning');

        if (canvasRef.current) {
          service.continuousScan(videoRef.current, canvasRef.current, handleDecode);
        }
      } catch {
        setScanState('error');
        setErrorMessage('No se pudo acceder a la cámara. Verifica los permisos.');
      }
    };

    initCamera();

    return () => {
      service.stopCamera();
      serviceRef.current = null;
    };
  }, []);

  const handleDecode = useCallback(
    async (result: { value: string; type: string }) => {
      const sku = result.value.trim();

      try {
        const products = await productService.searchProducts(sku);
        const exactMatch = products.find(
          (p: any) => p.sku?.toUpperCase() === sku.toUpperCase(),
        );

        if (!exactMatch) {
          toast.error('Producto no encontrado', {
            description: `SKU: ${sku}`,
          });
          return;
        }

        setScanState('success');
        toast.success('Producto seleccionado', {
          description: `${exactMatch.name}`,
        });

        serviceRef.current?.stopContinuousScan();
        setResolved({ id: exactMatch.id, name: exactMatch.name, sku: exactMatch.sku });
      } catch {
        toast.error('Producto no encontrado', {
          description: `SKU: ${sku}`,
        });
      }
    },
    [],
  );

  const handleToggleFlash = async () => {
    if (!serviceRef.current || !videoRef.current) return;
    const result = await serviceRef.current.toggleFlash(videoRef.current);
    setFlashOn(result);
  };

  const handleManualSubmit = async () => {
    if (!manualSku.trim()) return;
    setIsSubmittingManual(true);

    try {
      const products = await productService.searchProducts(manualSku.trim());
      const exactMatch = products.find(
        (p: any) => p.sku?.toUpperCase() === manualSku.trim().toUpperCase(),
      );

      if (!exactMatch) {
        toast.error('Producto no encontrado', {
          description: `SKU: ${manualSku}`,
        });
        setIsSubmittingManual(false);
        return;
      }

      setScanState('success');
      toast.success('Producto seleccionado', {
        description: `${exactMatch.name}`,
      });

      setResolved({ id: exactMatch.id, name: exactMatch.name, sku: exactMatch.sku });
    } catch {
      toast.error('Error al buscar producto');
      setIsSubmittingManual(false);
    }
  };

  /** Carries on to the till exactly as this page did before it offered the card. */
  const handleContinueToSale = (productId: string) => {
    navigate(ROUTES.SALES.NEW, { state: { productId } });
  };

  /**
   * Opens the sale card for the resolved piece (C36).
   *
   * No point of sale travels: this page has never had one. The card offers the same
   * role-resolved selector the assisted search panel offers, and issues no request until one is
   * chosen.
   */
  const handleOpenCard = (productId: string) => {
    navigate(ROUTES.SALES.ASSIST(productId));
  };

  const handleClose = () => {
    serviceRef.current?.stopCamera();
    navigate(ROUTES.SALES.ROOT);
  };

  const handleRetry = () => {
    setScanState('initializing');
    setErrorMessage('');

    const service = new BarcodeScanningService();
    serviceRef.current = service;

    const initCamera = async () => {
      try {
        if (!videoRef.current) return;
        await service.startCamera(videoRef.current);
        setScanState('scanning');

        if (canvasRef.current) {
          service.continuousScan(videoRef.current, canvasRef.current, handleDecode);
        }
      } catch {
        setScanState('error');
        setErrorMessage('No se pudo acceder a la cámara. Verifica los permisos.');
      }
    };

    initCamera();
  };

  return (
    <div className="relative flex h-[calc(100vh-8rem)] flex-col">
      <canvas ref={canvasRef} className="hidden" />

      {/* Scan viewport — always mounted so videoRef is available from the start */}
      <div className={scanState === 'scanning' ? 'relative flex-1 overflow-hidden bg-black' : 'hidden flex-1'}>
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="absolute inset-0 size-full object-cover"
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative size-64">
            <div className="absolute left-0 top-0 size-8 border-l-2 border-t-2 border-white" />
            <div className="absolute right-0 top-0 size-8 border-r-2 border-t-2 border-white" />
            <div className="absolute bottom-0 left-0 size-8 border-b-2 border-l-2 border-white" />
            <div className="absolute bottom-0 right-0 size-8 border-b-2 border-r-2 border-white" />
          </div>
        </div>
        <div className="absolute bottom-24 left-0 right-0 text-center">
          <p className="text-white/80 text-sm bg-black/50 inline-block px-4 py-1 rounded-full">
            Enfoca el código de barras o QR en el recuadro
          </p>
        </div>
      </div>

      {scanState === 'initializing' && (
        <div className="flex flex-1 items-center justify-center">
          <div className="text-center space-y-4">
            <div className="size-8 animate-pulse rounded-full bg-primary/20 mx-auto" />
            <p className="text-muted-foreground">Iniciando cámara...</p>
          </div>
        </div>
      )}

      {/* The piece is resolved and the operator chooses what to do with it. Before C36 this page
          went straight to the till, which left the customer-with-the-piece-in-their-hand
          situation — the one the card exists for — with no route to the knowledge corpus at
          all. Continuing to the sale is still the primary action and still lands exactly where
          it landed before. */}
      {scanState === 'success' && resolved && (
        <div className="flex flex-1 items-center justify-center p-4">
          <Card className="w-full max-w-md" data-testid="scan-resolved">
            <CardContent className="space-y-4 pt-6">
              <div className="text-center">
                <h3 className="text-lg font-semibold">{resolved.name}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{resolved.sku}</p>
              </div>
              <Button className="w-full" onClick={() => handleContinueToSale(resolved.id)}>
                Continuar con la venta
              </Button>
              <Button
                variant="outline"
                className="w-full"
                data-testid="scan-open-card"
                onClick={() => handleOpenCard(resolved.id)}
              >
                <FileText className="mr-2 size-4" />
                Ver ficha de venta
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {scanState === 'error' && (
        <div className="flex flex-1 items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardContent className="pt-6 space-y-4">
              <div className="flex flex-col items-center gap-4 text-center">
                <CameraOff className="size-12 text-destructive" />
                <div>
                  <h3 className="font-semibold text-lg">Error de cámara</h3>
                  <p className="text-sm text-muted-foreground mt-1">{errorMessage}</p>
                </div>
              </div>
              <Button className="w-full" onClick={handleRetry}>
                Reintentar
              </Button>
              <Button variant="outline" className="w-full" onClick={() => navigate(ROUTES.SALES.NEW)}>
                Entrada manual
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Scan controls */}
      <div className={scanState === 'scanning' ? 'flex items-center justify-center gap-4 p-4 bg-background border-t' : 'hidden'}>
        <Button
          variant="outline"
          size="icon"
          onClick={handleToggleFlash}
          title={flashOn ? 'Apagar flash' : 'Encender flash'}
        >
          {flashOn ? <FlashlightOff className="size-5" /> : <Flashlight className="size-5" />}
        </Button>

        <Button variant="outline" size="icon" onClick={handleClose} title="Cerrar">
          <X className="size-5" />
        </Button>
      </div>

      {scanState !== 'initializing' && (
        <div className="p-4 border-t bg-background">
          <div className="flex gap-2">
            <Input
              placeholder="Ingresa SKU manualmente..."
              value={manualSku}
              onChange={(e) => setManualSku(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleManualSubmit();
              }}
              disabled={isSubmittingManual || scanState === 'success'}
            />
            <Button
              onClick={handleManualSubmit}
              disabled={!manualSku.trim() || isSubmittingManual || scanState === 'success'}
            >
              <Search className="mr-2 size-4" />
              Buscar
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ScanningPage;
