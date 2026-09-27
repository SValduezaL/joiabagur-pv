import { lazy, Suspense } from 'react';
import { Route, Routes, Navigate } from 'react-router';
import { Layout8 } from '@/components/layouts/layout-8';
import { ProtectedRoute, AdminRoute, PublicRoute } from '@/components/auth';
import { ROUTES } from './routes';

// Lazy load pages for optimal bundle size
const LoginPage = lazy(() => import('@/pages/auth/login'));
const DashboardPage = lazy(() => import('@/pages/dashboard/page'));
const ProductsPage = lazy(() => import('@/pages/products'));
const ProductCatalogPage = lazy(() => import('@/pages/products/catalog'));
const ProductCreatePage = lazy(() => import('@/pages/products/create'));
const ProductEditPage = lazy(() => import('@/pages/products/edit'));
const ProductImportPage = lazy(() => import('@/pages/products/import'));
const InventoryPage = lazy(() => import('@/pages/inventory'));
const InventoryAssignPage = lazy(() => import('@/pages/inventory/assign'));
const InventoryImportPage = lazy(() => import('@/pages/inventory/import'));
const InventoryAdjustPage = lazy(() => import('@/pages/inventory/adjust'));
const InventoryMovementsPage = lazy(() => import('@/pages/inventory/movements'));
const InventoryCentralizedPage = lazy(() => import('@/pages/inventory/centralized'));
const SalesPage = lazy(() => import('@/pages/sales'));
const ManualSalesPage = lazy(() => import('@/pages/sales/new'));
const ScanSalesPage = lazy(() => import('@/pages/sales/scan'));
const ImageRecognitionSalesPage = lazy(() => import('@/pages/sales/new-image'));
const AssistedSalesSearchPage = lazy(() => import('@/pages/sales/assisted'));
// Lazily loaded like its three siblings: the agent panel is a fourth way of starting a sale and
// not the default one, so its code must not enter the initial bundle.
const AgentSalesPage = lazy(() => import('@/pages/sales/agent'));
const SalesAssistCardPage = lazy(() => import('@/pages/sales/assist'));
const SalesCartPage = lazy(() => import('@/pages/sales/cart'));
const SalesHistoryPage = lazy(() => import('@/pages/sales/history'));
const ReturnsPage = lazy(() => import('@/pages/returns'));
const NewReturnPage = lazy(() => import('@/pages/returns/new'));
const ReturnsHistoryPage = lazy(() => import('@/pages/returns/history'));
const AIModelPage = lazy(() => import('@/pages/admin/ai-model'));
const FamilyReviewPage = lazy(() => import('@/pages/admin/family-review'));
const ProfileReviewPage = lazy(() => import('@/pages/admin/profile-review'));
const PaymentMethodsPage = lazy(() => import('@/pages/payment-methods'));
const UsersPage = lazy(() => import('@/pages/users'));
const PointsOfSalePage = lazy(() => import('@/pages/points-of-sale'));
const ReportsPage = lazy(() => import('@/pages/reports'));
const ComponentListPage = lazy(() => import('@/pages/products/components'));
const ComponentTemplatesPage = lazy(() => import('@/pages/products/component-templates'));
const ProductMarginsPage = lazy(() => import('@/pages/reports/product-margins'));
const ProductsWithoutComponentsPage = lazy(() => import('@/pages/reports/products-without-components'));
const SalesReportPage = lazy(() => import('@/pages/reports/sales'));
const InventoryMovementSummaryPage = lazy(() => import('@/pages/reports/inventory-movement-summary'));

/**
 * Loading fallback component for lazy-loaded pages
 */
function PageLoader() {
  return (
    <div className="flex h-full min-h-[400px] items-center justify-center">
      <div className="text-muted-foreground">Cargando...</div>
    </div>
  );
}

/**
 * Main Application Routing Setup
 * Configures all routes with Layout 8 as the primary layout
 * Uses ProtectedRoute for authentication and AdminRoute for admin-only pages
 */
export function AppRoutingSetup() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public Routes - Redirect to dashboard if already authenticated */}
        <Route element={<PublicRoute />}>
          <Route path={ROUTES.AUTH.LOGIN} element={<LoginPage />} />
        </Route>

        {/* Protected Routes - Require authentication */}
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout8 />}>
            {/* Routes accessible by all authenticated users */}
            <Route path={ROUTES.DASHBOARD} element={<DashboardPage />} />
            <Route path={ROUTES.PRODUCTS.CATALOG} element={<ProductCatalogPage />} />
            <Route path={ROUTES.INVENTORY.ROOT} element={<InventoryPage />} />
            <Route path={ROUTES.INVENTORY.STOCK} element={<InventoryPage />} />
            <Route path={ROUTES.INVENTORY.MOVEMENTS} element={<InventoryMovementsPage />} />
            <Route path={ROUTES.SALES.ROOT} element={<SalesPage />} />
            <Route path={ROUTES.SALES.NEW} element={<ManualSalesPage />} />
            <Route path={ROUTES.SALES.NEW_SCAN} element={<ScanSalesPage />} />
            <Route path={ROUTES.SALES.NEW_IMAGE} element={<ImageRecognitionSalesPage />} />
            <Route path={ROUTES.SALES.NEW_ASSISTED} element={<AssistedSalesSearchPage />} />
            <Route path={ROUTES.SALES.NEW_AGENT} element={<AgentSalesPage />} />
            <Route path={ROUTES.SALES.ASSIST_PATTERN} element={<SalesAssistCardPage />} />
            <Route path={ROUTES.SALES.CART} element={<SalesCartPage />} />
            <Route path={ROUTES.SALES.HISTORY} element={<SalesHistoryPage />} />
            <Route path={ROUTES.RETURNS.ROOT} element={<ReturnsPage />} />
            <Route path={ROUTES.RETURNS.NEW} element={<NewReturnPage />} />
            <Route path={ROUTES.RETURNS.HISTORY} element={<ReturnsHistoryPage />} />
          </Route>
        </Route>

        {/* Admin-only Routes - Require Administrator role */}
        <Route element={<AdminRoute />}>
          <Route element={<Layout8 />}>
            {/* Inventory admin routes */}
            <Route path={ROUTES.INVENTORY.ASSIGN} element={<InventoryAssignPage />} />
            <Route path={ROUTES.INVENTORY.IMPORT} element={<InventoryImportPage />} />
            <Route path={ROUTES.INVENTORY.ADJUST} element={<InventoryAdjustPage />} />
            <Route path={ROUTES.INVENTORY.CENTRALIZED} element={<InventoryCentralizedPage />} />
            
            <Route path={ROUTES.PRODUCTS.ROOT} element={<ProductsPage />} />
            <Route path={ROUTES.PRODUCTS.CREATE} element={<ProductCreatePage />} />
            <Route path="/products/:productId/edit" element={<ProductEditPage />} />
            <Route path={ROUTES.PRODUCTS.IMPORT} element={<ProductImportPage />} />
            <Route path={ROUTES.PRODUCTS.COMPONENTS} element={<ComponentListPage />} />
            <Route path={ROUTES.PRODUCTS.COMPONENT_TEMPLATES} element={<ComponentTemplatesPage />} />
            <Route path={ROUTES.PAYMENT_METHODS} element={<PaymentMethodsPage />} />
            <Route path={ROUTES.USERS} element={<UsersPage />} />
            <Route path={ROUTES.POINTS_OF_SALE} element={<PointsOfSalePage />} />
            <Route path={ROUTES.REPORTS.ROOT} element={<ReportsPage />} />
            <Route path={ROUTES.REPORTS.SALES} element={<SalesReportPage />} />
            <Route path={ROUTES.REPORTS.PRODUCT_MARGINS} element={<ProductMarginsPage />} />
            <Route path={ROUTES.REPORTS.PRODUCTS_WITHOUT_COMPONENTS} element={<ProductsWithoutComponentsPage />} />
            <Route path={ROUTES.REPORTS.INVENTORY_MOVEMENT_SUMMARY} element={<InventoryMovementSummaryPage />} />
            <Route path={ROUTES.AI_MODEL} element={<AIModelPage />} />
            <Route path={ROUTES.FAMILY_REVIEW} element={<FamilyReviewPage />} />
            <Route path={ROUTES.PROFILE_REVIEW} element={<ProfileReviewPage />} />
          </Route>
        </Route>

        {/* Default redirect to dashboard */}
        <Route path="/" element={<Navigate to={ROUTES.DASHBOARD} replace />} />

        {/* Catch-all redirect to dashboard */}
        <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
      </Routes>
    </Suspense>
  );
}
