// Configuración de ESLint del frontend — formato plano, obligatorio desde ESLint 9.
//
// ESTE FICHERO NO EXISTÍA, y nadie lo sabía. `package.json` declara `"lint": "eslint ."` y
// trae desde el principio las seis dependencias que hacen falta —`@eslint/js`, `eslint`,
// `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`, `globals` y `typescript-eslint`—,
// pero el fichero de configuración nunca llegó al repositorio. Así que `npm run lint` no fallaba
// reglas: **el linter no arrancaba**, con `ESLint couldn't find an eslint.config.(js|mjs|cjs)` y
// código 2.
//
// Se descubrió el 2026-09-27, al encender la CI en C39a: hasta entonces `test-frontend.yml`
// disparaba sobre ramas que no existen y no se había ejecutado nunca, y `npm run lint` no está en
// el camino de nadie —el flujo documentado es `npm run test`, `npm run build` y `tsc --noEmit`
// filtrado—. El workflow moría en el paso de lint y **el de tests quedaba omitido**, así que la CI
// encendía una luz roja sin llegar a medir la suite.
//
// La composición es la del proyecto y no una elección: las mismas capas que el propio
// `package.json` declara.

import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  {
    // Nada de esto es código fuente de este proyecto: son salidas de build, informes y
    // dependencias. Linterlos no informa de nada y sí tarda.
    ignores: [
      'dist/**',
      'coverage/**',
      'node_modules/**',
      'playwright-report/**',
      'test-results/**',
      // La caché de pre-empaquetado de dependencias de Vite. **Faltaba en la primera versión de
      // este fichero**, y el efecto fue engañoso: ESLint recorría `.vite/deps/react-router-dom.js`
      // y reportaba tres errores que no eran violaciones de nada, sino
      // `Definition for rule 'react-hooks/rules-of-hooks' was not found` — comentarios
      // `eslint-disable` de la propia librería, sobre plugins que este fichero no carga para un
      // `.js`. Leídos por encima parecían los tres únicos hallazgos serios del árbol; no existen.
      //
      // Está además **rastreada por git** desde el 2026-02-04, lo cual es otro asunto: 16 ficheros
      // y 3,9 MB de caché regenerable dentro del repositorio. No se arregla desde aquí.
      '.vite/**',
      // Declaraciones generadas por Vite.
      'src/vite-env.d.ts',
    ],
  },
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      // `recommended` y NO `recommendedTypeChecked`, deliberadamente. La variante con tipos
      // necesita el servicio de TypeScript sobre 955 ficheros y multiplica el tiempo de la
      // comprobación; y sobre todo, la comprobación de tipos de este proyecto ya la hace
      // `tsc --noEmit`, que es donde vive esa responsabilidad. Aquí se busca lo que `tsc` no ve:
      // reglas de hooks, exportaciones que rompen el recargado en caliente, y errores de
      // JavaScript que el compilador no considera suyos.
      ...tseslint.configs.recommended,
    ],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      // Avisa, no rompe: una exportación que no es un componente impide el recargado en caliente
      // del módulo, lo cual es una molestia de desarrollo y nunca un defecto del producto.
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      // Un argumento o una variable con guion bajo delante es una omisión declarada, no un olvido:
      // el patrón aparece en este árbol en firmas de callback donde un parámetro intermedio no se
      // usa y no se puede quitar sin cambiar la posición de los siguientes.
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
    },
  },
  {
    // Los ficheros de configuración y los de Playwright corren en Node, no en el navegador, así
    // que sus globales son otras. Sin esto, `process` y `__dirname` se reportan como indefinidos
    // en ficheros que son correctos.
    files: ['*.{ts,js,mjs,cjs}', 'e2e/**/*.ts', 'playwright.config.ts', 'vite.config.ts'],
    languageOptions: {
      globals: { ...globals.node },
    },
  },
  {
    // Los tests usan las globales de Vitest y de jsdom a la vez. `vitest/globals` no está en el
    // paquete `globals`, así que las que importan se declaran aquí en lugar de apagar la regla.
    files: ['**/*.{test,spec}.{ts,tsx}', 'src/test/**/*.{ts,tsx}'],
    languageOptions: {
      globals: {
        ...globals.node,
        vi: 'readonly',
        describe: 'readonly',
        it: 'readonly',
        test: 'readonly',
        expect: 'readonly',
        beforeAll: 'readonly',
        beforeEach: 'readonly',
        afterAll: 'readonly',
        afterEach: 'readonly',
      },
    },
  },
);
