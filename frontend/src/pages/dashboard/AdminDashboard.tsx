import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  ShoppingCart,
  TrendingUp,
  TrendingDown,
  RotateCcw,
  AlertTriangle,
  ExternalLink,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Alert, AlertDescription, AlertIcon, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { dashboardService } from '@/services/dashboard.service';
import { salesService } from '@/services/sales.service';
import { aiHealthService } from '@/services/ai-health.service';
import type { DashboardStats, PaginatedLowStockResult } from '@/types/dashboard.types';
import type { AiHealthOutcome, AiHealthProjection } from '@/types/ai-health.types';
import type { Sale } from '@/types/sales.types';
import { ROUTES } from '@/routing/routes';

const CHART_COLORS = [
  '#2563eb', '#dc2626', '#16a34a', '#ca8a04', '#9333ea',
  '#0891b2', '#e11d48', '#65a30d', '#d97706', '#7c3aed',
];

const DONUT_COLORS = ['#2563eb', '#16a34a', '#dc2626', '#ca8a04', '#9333ea', '#0891b2'];

const formatCurrency = (amount: number) =>
  new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(amount);

const formatCompact = (amount: number) =>
  new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(amount);

interface TrendDataPoint {
  date: string;
  [posName: string]: string | number;
}

interface PosRevenueItem {
  name: string;
  revenue: number;
}

const STOCK_PAGE_SIZE = 10;

const formatCount = (value: number) => new Intl.NumberFormat('es-ES').format(value);

/**
 * How long ago the projection was drained, in words.
 *
 * Words and not seconds, because this is a diagnostic line a person reads rather than a figure
 * anybody measures with — the exact value is in the element's `title` for when it is needed.
 * The phrasing names the *drain*, never a shop: the instant it comes from is one per feed, so
 * "hace 12 minutos en esta tienda" would be false for ten of the eleven.
 */
const describeProjectionFreshness = (projection: AiHealthProjection): string => {
  if (projection.status === 'unavailable') {
    return 'No se ha podido leer el estado de la sincronización.';
  }
  if (projection.ageSeconds === null || projection.ageSeconds === undefined) {
    return 'La sincronización no se ha ejecutado nunca en este entorno.';
  }

  const seconds = Math.max(Math.floor(projection.ageSeconds), 0);
  if (seconds < 60) return 'Última sincronización: hace menos de un minuto.';

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `Última sincronización: hace ${minutes} ${minutes === 1 ? 'minuto' : 'minutos'}.`;
  }

  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `Última sincronización: hace ${hours} ${hours === 1 ? 'hora' : 'horas'}.`;
  }

  const days = Math.floor(hours / 24);
  return `Última sincronización: hace ${days} ${days === 1 ? 'día' : 'días'}.`;
};

export function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [trendData, setTrendData] = useState<TrendDataPoint[]>([]);
  const [posRevenue, setPosRevenue] = useState<PosRevenueItem[]>([]);
  const [posNames, setPosNames] = useState<string[]>([]);
  const [lowStockResult, setLowStockResult] = useState<PaginatedLowStockResult | null>(null);
  const [stockPage, setStockPage] = useState(1);
  const [stockLoading, setStockLoading] = useState(false);
  const [recentSales, setRecentSales] = useState<Sale[]>([]);
  const [loading, setLoading] = useState(true);
  const [aiHealth, setAiHealth] = useState<AiHealthOutcome | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [dashStats, salesHistory, lowStock] = await Promise.all([
          dashboardService.getStats(),
          salesService.getSalesHistory({
            startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            pageSize: 1000,
            page: 1,
          }),
          dashboardService.getLowStock(1, STOCK_PAGE_SIZE),
        ]);

        setStats(dashStats);
        setLowStockResult(lowStock);

        const salesWithoutReturns = salesHistory.sales.filter((s) => !s.hasReturn);

        // Recent 8 sales (exclude returned)
        setRecentSales(salesWithoutReturns.slice(0, 8));

        // Build 30-day trend data grouped by day and POS
        const salesByDayPos = new Map<string, Map<string, number>>();
        const allPosNames = new Set<string>();

        for (const sale of salesWithoutReturns) {
          const day = sale.saleDate.split('T')[0];
          const pos = sale.pointOfSaleName;
          allPosNames.add(pos);

          if (!salesByDayPos.has(day)) salesByDayPos.set(day, new Map());
          const dayMap = salesByDayPos.get(day)!;
          dayMap.set(pos, (dayMap.get(pos) ?? 0) + sale.total);
        }

        // Build sorted date range for last 30 days
        const days: string[] = [];
        for (let i = 29; i >= 0; i--) {
          const d = new Date(Date.now() - i * 24 * 60 * 60 * 1000);
          days.push(d.toISOString().split('T')[0]);
        }

        const posNamesArr = Array.from(allPosNames);
        setPosNames(posNamesArr);

        const trend: TrendDataPoint[] = days.map((day) => {
          const point: TrendDataPoint = { date: day.slice(5) };
          const dayMap = salesByDayPos.get(day);
          for (const pos of posNamesArr) {
            point[pos] = dayMap?.get(pos) ?? 0;
          }
          return point;
        });
        setTrendData(trend);

        // Revenue by POS (current month, exclude returned)
        const revenueMap = new Map<string, number>();
        const monthStart = new Date();
        monthStart.setDate(1);
        monthStart.setHours(0, 0, 0, 0);

        for (const sale of salesWithoutReturns) {
          if (new Date(sale.saleDate) >= monthStart) {
            revenueMap.set(
              sale.pointOfSaleName,
              (revenueMap.get(sale.pointOfSaleName) ?? 0) + sale.total,
            );
          }
        }

        setPosRevenue(
          Array.from(revenueMap.entries())
            .map(([name, revenue]) => ({ name, revenue }))
            .sort((a, b) => b.revenue - a.revenue),
        );
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  // Loaded on its own, deliberately outside the Promise.all above. The AI service is a separate
  // deployment behind a gateway with its own time budget: folding it into the batch that gates
  // `loading` would let a slow or unreachable AI service delay — or, if it threw, blank — a
  // dashboard whose sales, revenue and stock have nothing to do with it. The service itself
  // never rejects; `unreachable` is a state the card renders.
  useEffect(() => {
    const abortController = new AbortController();

    aiHealthService.getHealth(abortController.signal).then((outcome) => {
      if (!abortController.signal.aborted) setAiHealth(outcome);
    });

    return () => abortController.abort();
  }, []);

  const stockPageInitialRef = useRef(true);
  useEffect(() => {
    if (stockPageInitialRef.current) {
      stockPageInitialRef.current = false;
      return;
    }
    const abortController = new AbortController();
    const loadPage = async () => {
      setStockLoading(true);
      try {
        const result = await dashboardService.getLowStock(stockPage, STOCK_PAGE_SIZE, abortController.signal);
        setLowStockResult(result);
      } catch (err) {
        if (abortController.signal.aborted) return;
        console.error('Failed to load low stock page:', err);
      } finally {
        if (!abortController.signal.aborted) setStockLoading(false);
      }
    };
    loadPage();
    return () => abortController.abort();
  }, [stockPage]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-muted-foreground">Cargando dashboard...</div>
      </div>
    );
  }

  if (!stats) return null;

  const yoyChange = stats.previousYearMonthlyRevenue
    ? ((stats.monthlyRevenue - stats.previousYearMonthlyRevenue) / stats.previousYearMonthlyRevenue) * 100
    : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Visión global del negocio</p>
      </div>

      {/* Row 1 — KPI Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ventas hoy</CardTitle>
            <ShoppingCart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(stats.salesTodayTotal)}</div>
            <p className="text-xs text-muted-foreground">{stats.salesTodayCount} ventas registradas</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ingresos del mes</CardTitle>
            {yoyChange !== null && yoyChange >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : yoyChange !== null ? (
              <TrendingDown className="h-4 w-4 text-red-600" />
            ) : (
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(stats.monthlyRevenue)}</div>
            {yoyChange !== null ? (
              <p className={`text-xs ${yoyChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {yoyChange >= 0 ? '+' : ''}{yoyChange.toFixed(1)}% vs. mismo mes del año anterior
              </p>
            ) : (
              <p className="text-xs text-muted-foreground">Sin datos comparativos</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Devoluciones del mes</CardTitle>
            <RotateCcw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.monthlyReturnsCount}</div>
            <p className="text-xs text-muted-foreground">{formatCurrency(stats.monthlyReturnsTotal)} devueltos</p>
          </CardContent>
        </Card>
      </div>

      {/* Row 2 — Stock crítico (full width) */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Stock crítico
            </CardTitle>
            <CardDescription>Productos con stock &le; 2 unidades</CardDescription>
          </div>
          <Link
            to={ROUTES.INVENTORY.ADJUST}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-primary hover:underline flex items-center gap-1"
          >
            Ajustar <ExternalLink className="h-3 w-3" />
          </Link>
        </CardHeader>
        <CardContent>
          {!lowStockResult || lowStockResult.totalCount === 0 ? (
            <p className="text-sm text-muted-foreground">No hay productos con stock crítico.</p>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Producto</TableHead>
                    <TableHead>SKU</TableHead>
                    <TableHead>POS</TableHead>
                    <TableHead className="text-right">Stock</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {stockLoading ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-muted-foreground py-6">
                        Cargando...
                      </TableCell>
                    </TableRow>
                  ) : (
                    lowStockResult.items.map((item, i) => (
                      <TableRow key={`${item.sku}-${item.pointOfSaleName}-${i}`}>
                        <TableCell className="font-medium">{item.productName}</TableCell>
                        <TableCell className="text-muted-foreground">{item.sku}</TableCell>
                        <TableCell>{item.pointOfSaleName}</TableCell>
                        <TableCell className="text-right">
                          <span className={item.stock === 0 ? 'text-red-600 font-bold' : 'text-amber-600 font-semibold'}>
                            {item.stock}
                          </span>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
              {lowStockResult.totalPages > 1 && (
                <div className="flex items-center justify-between pt-4">
                  <p className="text-sm text-muted-foreground">
                    Página {lowStockResult.page} de {lowStockResult.totalPages} ({lowStockResult.totalCount} artículos)
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={stockPage === 1 || stockLoading}
                      onClick={() => setStockPage((p) => p - 1)}
                    >
                      Anterior
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={stockPage >= lowStockResult.totalPages || stockLoading}
                      onClick={() => setStockPage((p) => p + 1)}
                    >
                      Siguiente
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Row 3 — Últimas ventas (full width) */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base">Últimas ventas</CardTitle>
            <CardDescription>8 ventas más recientes</CardDescription>
          </div>
          <Link
            to={ROUTES.SALES.HISTORY}
            className="text-xs text-primary hover:underline flex items-center gap-1"
          >
            Ver todo <ExternalLink className="h-3 w-3" />
          </Link>
        </CardHeader>
        <CardContent>
          {recentSales.length === 0 ? (
            <p className="text-sm text-muted-foreground">No hay ventas recientes.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fecha</TableHead>
                  <TableHead>Producto</TableHead>
                  <TableHead>POS</TableHead>
                  <TableHead>Operador</TableHead>
                  <TableHead className="text-right">Importe</TableHead>
                  <TableHead>Pago</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentSales.map((sale) => (
                  <TableRow key={sale.id}>
                    <TableCell className="text-xs">
                      {new Date(sale.saleDate).toLocaleDateString('es-ES')}
                    </TableCell>
                    <TableCell className="font-medium max-w-[120px] truncate">{sale.productName}</TableCell>
                    <TableCell className="text-xs">{sale.pointOfSaleName}</TableCell>
                    <TableCell className="text-xs">{sale.userName}</TableCell>
                    <TableCell className="text-right font-medium">{formatCurrency(sale.total)}</TableCell>
                    <TableCell className="text-xs">{sale.paymentMethodName}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Row 4 — Trend + POS revenue charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Tendencia de ventas (30 días)</CardTitle>
            <CardDescription>Ingresos diarios por punto de venta</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => formatCompact(v)} />
                <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                <Legend />
                {posNames.slice(0, 5).map((pos, i) => (
                  <Line
                    key={pos}
                    type="monotone"
                    dataKey={pos}
                    stroke={CHART_COLORS[i % CHART_COLORS.length]}
                    strokeWidth={2}
                    dot={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Ingresos por POS (mes actual)</CardTitle>
            <CardDescription>Comparativa de rendimiento</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={Math.max(200, posRevenue.length * 40)}>
              <BarChart data={posRevenue} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={(v) => formatCompact(v)} tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={120} />
                <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                <Bar dataKey="revenue" fill="#2563eb" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Row 5 — Donut charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Ventas por método de pago</CardTitle>
            <CardDescription>Distribución del mes actual</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            {stats.paymentMethodDistribution && stats.paymentMethodDistribution.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={stats.paymentMethodDistribution}
                    dataKey="amount"
                    nameKey="methodName"
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    label={({ name, percent }) =>
                      `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`
                    }
                    labelLine={false}
                  >
                    {stats.paymentMethodDistribution.map((_, i) => (
                      <Cell key={i} fill={DONUT_COLORS[i % DONUT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground py-12">Sin datos este mes.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Devoluciones por categoría</CardTitle>
            <CardDescription>Distribución del mes actual</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            {stats.returnCategoryDistribution && stats.returnCategoryDistribution.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={stats.returnCategoryDistribution}
                    dataKey="count"
                    nameKey="category"
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    label={({ name, percent }) =>
                      `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`
                    }
                    labelLine={false}
                  >
                    {stats.returnCategoryDistribution.map((_, i) => (
                      <Cell key={i} fill={DONUT_COLORS[i % DONUT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground py-12">Sin datos este mes.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/*
        Estado del servicio de IA — sólo en el panel de administración.

        El navegador no puede preguntar directamente al servicio de IA: es privado por diseño y
        no publica ningún puerto, así que esto lo sirve `GET /api/ai/health`, restringido a
        administradores porque describe infraestructura.

        Dos condiciones se presentan como error y EN TEXTO, nunca sólo por color:
          - el modelo de embeddings configurado no coincide con el del índice, que devuelve ruido
            con un 200 y sin traza;
          - el servicio no responde, que degrada la búsqueda asistida al camino léxico.
      */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Servicio de IA</CardTitle>
          <CardDescription>
            Búsqueda asistida: base de datos, índice vectorial y proveedor de embeddings
          </CardDescription>
        </CardHeader>
        <CardContent>
          {aiHealth === null ? (
            <div className="space-y-3" data-testid="ai-service-status-loading">
              <Skeleton className="h-4 w-56" />
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-4 w-48" />
            </div>
          ) : aiHealth.kind === 'unreachable' ? (
            <Alert variant="destructive" appearance="light">
              <AlertIcon>
                <AlertTriangle />
              </AlertIcon>
              <AlertTitle>El servicio de IA no responde</AlertTitle>
              <AlertDescription>
                La búsqueda asistida sigue disponible en modo degradado, con búsqueda léxica. El
                resto del panel no se ve afectado.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-4">
              {aiHealth.report.index.status === 'model_mismatch' && (
                <Alert variant="destructive" appearance="light">
                  <AlertIcon>
                    <AlertTriangle />
                  </AlertIcon>
                  <AlertTitle>Modelo de embeddings incompatible con el índice</AlertTitle>
                  <AlertDescription>
                    El servicio consulta con <strong>{aiHealth.report.index.configuredModel}</strong> y
                    el índice se generó con <strong>{aiHealth.report.index.model}</strong>. Las
                    búsquedas comparan dos espacios vectoriales distintos y devuelven resultados sin
                    sentido, sin dar ningún error. Hay que reindexar o corregir la configuración.
                  </AlertDescription>
                </Alert>
              )}

              <dl className="grid gap-3 sm:grid-cols-3">
                <div className="space-y-1">
                  <dt className="text-xs text-muted-foreground">Base de datos</dt>
                  <dd>
                    {aiHealth.report.database === 'ok' ? (
                      <Badge variant="success" appearance="light">
                        Accesible
                      </Badge>
                    ) : (
                      <Badge variant="destructive" appearance="light">
                        No accesible
                      </Badge>
                    )}
                  </dd>
                </div>

                <div className="space-y-1">
                  <dt className="text-xs text-muted-foreground">Documentos indexados</dt>
                  <dd className="text-lg font-semibold">
                    {formatCount(aiHealth.report.index.documents)}
                  </dd>
                </div>

                <div className="space-y-1">
                  <dt className="text-xs text-muted-foreground">Proveedor de embeddings</dt>
                  <dd>
                    {aiHealth.report.provider === 'configured' ? (
                      <Badge variant="success" appearance="light">
                        Credencial configurada
                      </Badge>
                    ) : (
                      <Badge variant="destructive" appearance="light">
                        Credencial ausente
                      </Badge>
                    )}
                  </dd>
                </div>

                {/*
                  Rendered only when the AI service reports it: a deployment can run an older
                  `jbg-ai` image than this API, and painting "desconocido" for that would be
                  noise about a version skew rather than about the projection.
                */}
                {aiHealth.report.projection ? (
                  <div className="space-y-1" data-testid="ai-projection-freshness">
                    <dt className="text-xs text-muted-foreground">
                      Disponibilidad por tienda
                    </dt>
                    <dd className="space-y-1">
                      {aiHealth.report.projection.status === 'ok' ? (
                        <Badge variant="success" appearance="light">
                          Al día
                        </Badge>
                      ) : aiHealth.report.projection.status === 'never_drained' ? (
                        <Badge variant="destructive" appearance="light">
                          Sin sincronizar nunca
                        </Badge>
                      ) : aiHealth.report.projection.status === 'stale' ? (
                        <Badge variant="warning" appearance="light">
                          Desactualizada
                        </Badge>
                      ) : (
                        <Badge variant="secondary" appearance="light">
                          Sin datos
                        </Badge>
                      )}

                      <p
                        className="text-xs text-muted-foreground"
                        title={
                          aiHealth.report.projection.syncedAt ??
                          'La sincronización no se ha ejecutado nunca'
                        }
                      >
                        {describeProjectionFreshness(aiHealth.report.projection)}
                      </p>

                      {/*
                        The copy is about COMPLETENESS and never about correctness. The backend
                        applies the truth when it hydrates, so a stale projection costs a short
                        page — it never shows a piece the shop does not carry, and it never hides
                        one from the authority. "Los resultados no son fiables" would be false.
                      */}
                      {aiHealth.report.projection.stale ? (
                        <p className="text-xs text-muted-foreground">
                          Las búsquedas asistidas pueden devolver menos resultados de los
                          disponibles.
                        </p>
                      ) : null}

                      {(aiHealth.report.projection.shopsWithoutScope ?? 0) > 0 ? (
                        <p className="text-xs text-destructive">
                          {aiHealth.report.projection.shopsWithoutScope === 1
                            ? '1 tienda sin surtido sincronizado: su búsqueda asistida no funciona.'
                            : `${aiHealth.report.projection.shopsWithoutScope} tiendas sin surtido sincronizado: su búsqueda asistida no funciona.`}
                        </p>
                      ) : null}

                      {(aiHealth.report.projection.failedPages ?? 0) > 0 ? (
                        <p className="text-xs text-muted-foreground">
                          {aiHealth.report.projection.failedPages} página(s) con errores
                          registrados.
                        </p>
                      ) : null}
                    </dd>
                  </div>
                ) : null}
              </dl>

              <Separator />

              <p className="text-xs text-muted-foreground">
                Versión {aiHealth.report.version}
                {aiHealth.report.index.model ? ` · Modelo del índice: ${aiHealth.report.index.model}` : ''}
              </p>

              {/*
                Stated rather than offered as a button. With the drain running at start-up and
                every ten minutes, a "refresh now" control would save at most one interval of
                waiting, and it would cost a route on a frozen contract. What a person actually
                needs from here is the FULL reconciliation — after the injected sales clock
                moves, or after failed pages — and only a person knows when that applies.
              */}
              {aiHealth.report.projection &&
              aiHealth.report.projection.status !== 'ok' &&
              aiHealth.report.projection.status !== 'unavailable' ? (
                <p className="text-xs text-muted-foreground">
                  Reconciliación completa:{' '}
                  <code className="text-[11px]">
                    docker exec -i jbg-demo-ai python -m jbg_ai.indexing sync-pos --full
                  </code>
                </p>
              ) : null}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default AdminDashboard;
