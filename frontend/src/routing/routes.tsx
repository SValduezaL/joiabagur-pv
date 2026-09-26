/**
 * Application Route Constants
 * Centralized route definitions for the application
 */

export const ROUTES = {
  // Public routes
  AUTH: {
    LOGIN: '/auth/login',
  },

  // Protected routes
  DASHBOARD: '/dashboard',

  // Module routes - organized by epic
  PRODUCTS: {
    ROOT: '/products',
    CATALOG: '/products/catalog',
    CREATE: '/products/create',
    EDIT: (id: string) => `/products/${id}/edit`,
    IMPORT: '/products/import',
    COMPONENTS: '/products/components',
    COMPONENT_TEMPLATES: '/products/component-templates',
  },
  INVENTORY: {
    ROOT: '/inventory',
    STOCK: '/inventory/stock',
    ASSIGN: '/inventory/assign',
    IMPORT: '/inventory/import',
    ADJUST: '/inventory/adjust',
    MOVEMENTS: '/inventory/movements',
    CENTRALIZED: '/inventory/centralized',
  },
  SALES: {
    ROOT: '/sales',
    NEW: '/sales/new',
    NEW_SCAN: '/sales/new/scan',
    NEW_IMAGE: '/sales/new/image',
    NEW_ASSISTED: '/sales/new/assisted',
    /**
     * The sale agent's own route (C42), and not a toggle inside the assisted panel.
     *
     * That panel is one query producing one set of results while the agent is a conversation, and
     * it already carries a toggle with a different meaning -- the degraded path against the
     * generative one. Two controls of similar name and different meaning on one screen is the
     * failure the free-query panel was built to remove.
     */
    NEW_AGENT: '/sales/new/agent',
    /**
     * The sale card of one piece (C36). Anchored to a product; the point of sale travels in
     * navigation state, and the card offers a role-resolved selector when it does not.
     */
    ASSIST: (productId: string) => `/sales/new/assist/${productId}`,
    /** Route pattern of the above, for registering it. */
    ASSIST_PATTERN: '/sales/new/assist/:productId',
    CART: '/sales/cart',
    HISTORY: '/sales/history',
    DETAIL: (id: string) => `/sales/${id}`,
  },
  AI_MODEL: '/admin/ai-model',
  FAMILY_REVIEW: '/admin/family-review',
  PROFILE_REVIEW: '/admin/profile-review',
  RETURNS: {
    ROOT: '/returns',
    NEW: '/returns/new',
    HISTORY: '/returns/history',
    DETAIL: (id: string) => `/returns/${id}`,
  },
  PAYMENT_METHODS: '/payment-methods',
  USERS: '/users',
  POINTS_OF_SALE: '/points-of-sale',
  REPORTS: {
    ROOT: '/reports',
    SALES: '/reports/sales',
    PRODUCT_MARGINS: '/reports/product-margins',
    PRODUCTS_WITHOUT_COMPONENTS: '/reports/products-without-components',
    INVENTORY_MOVEMENT_SUMMARY: '/reports/inventory-movement-summary',
  },
} as const;

/**
 * Check if a route is public (doesn't require authentication)
 */
export function isPublicRoute(path: string): boolean {
  const publicRoutes = [ROUTES.AUTH.LOGIN];
  return publicRoutes.some((route) => path.startsWith(route));
}
