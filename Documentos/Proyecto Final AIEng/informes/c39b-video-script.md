# C39b — guion del vídeo de entrega

**Duración objetivo:** 2-3 minutos. El reparto de abajo suma **2:50**, con ~10 s de holgura.
**Entorno:** <https://52-49-209-14.sslip.io> · **fecha del guion:** 2026-09-27, sobre el despliegue
`36344846739`, verificado en verde.

> **La grabación NO es parte de este change.** Una sesión de Claude Code no tiene navegador. Lo que
> este documento entrega es el guion: qué se cuenta, en qué orden, con qué cuenta se entra en cada
> tramo, **qué consulta exacta se teclea** y qué debe aparecer para que el tramo haya demostrado lo que
> dice demostrar. Lo que falta para producirlo es grabarlo siguiendo estos siete tramos.

---

## 0 · Antes de empezar: las dos cosas en rojo, explicadas de antemano

**Están aquí a propósito y en primer lugar.** Las dos aparecen —o pueden aparecer— durante la
grabación, las dos parecen una avería y **ninguna lo es**. Decirlas antes de que salgan es la
diferencia entre un evaluador que entiende lo que ve y uno que cree haber encontrado un fallo.

### 0.1 · Un aviso rojo salta al entrar como administrador, y no es de lo que se evalúa

Al iniciar sesión con `demo.admin` aparece, **durante diez segundos y una sola vez por sesión**, un
aviso con icono rojo:

> 🔴 **Modelo de IA: Acción Requerida** — *No hay modelo de IA disponible. Entrene el primer modelo.*

Y en `/admin/ai-model` el mismo estado se pinta como alerta destructiva, **«Acción Requerida»**.

**Qué decir en el vídeo, literalmente:**

> «Ese aviso es del **reconocimiento de imagen**, que es funcionalidad **del MVP y no del Proyecto
> Final**. No se puede entrenar nada aquí porque el catálogo de este entorno **no tiene ni una
> fotografía** —1.200 productos, 0 con foto—, así que no hay material del que aprender. El nivel
> `CRITICAL` está mal elegido: describe algo roto, y lo que hay es una funcionalidad **no alimentada**.
> Está declarado como limitación con su arreglo escrito.»

**Guion de cámara:** cerrar el aviso y seguir. No navegar a `/admin/ai-model` — no es lo que se evalúa
y gastaría veinte segundos del presupuesto.

### 0.2 · El pivote del agente sólo se alcanza nombrando la pieza por su REFERENCIA

Si en el tramo del agente se nombra la pieza **por su nombre** en vez de por su referencia, el agente
**no pivota a sustitutos** y el tramo enseña un fallo en lugar del pilar. Está medido:

| Cómo se nombra | Qué hace el bucle | ¿Pivota? |
|---|---|---|
| **`SKU759`** | `consultar_disponibilidad` → **`buscar_sustitutos`** | ✅ sí — 6 grupos, todos alternativas |
| «Anillo Luna Creciente S» | `consultar_disponibilidad` ❗`referencia_desconocida` → `buscar_catalogo` → `consultar_disponibilidad` | ❌ no — 8 grupos, todos de catálogo |

**La causa es estructural y no del modelo:** `buscar_catalogo` no devuelve el nombre del producto, así
que el modelo recibe ocho candidatos identificados sólo por SKU, material y variante y **no tiene con
qué saber cuál es la pieza que el cliente nombró**. Limitación declarada, con su arreglo costado.

**Qué decir en el vídeo, en una frase:** *«el cliente trae la pieza con su etiqueta delante, así que el
mostrador teclea la referencia — y si se teclea el nombre, el agente no llega a comprobar si la tienda
la tiene: está declarado como limitación.»*

---

## 1 · Las cuatro cuentas, y por qué hacen falta cuatro

**El surtido de cada tienda es parte de lo que hay que probar.** La abstención, los sustitutos y el
pivote del agente **sólo son observables desde la tienda que los provoca**: con una sola cuenta de
operación el vídeo dejaría fuera comportamientos que sí existen.

| Cuenta | Rol | Tienda | Qué tramo es suyo |
|---|---|---|---|
| `op-ciutadella` | Operator | `CIU-CENTRE` | surtido máximo (871 filas) — **el camino feliz** (tramos 2 y 3) |
| `op-fornells` | Operator | `FORNELLS` | surtido mínimo (241, 29 agotadas) — **abstención, sustitutos y avisos** (tramo 4) |
| `op-aeroport` | Operator | `MAO-AIR` | más agotados — **el agente y su pivote** (tramo 5) |
| `demo.admin` | Administrator | — | **la tarjeta de salud de la IA** (tramo 6) |

Los tres operarios entran con `Operator123!`, que es una constante pública documentada del mundo
sintético. **La contraseña de `demo.admin` no está en el repositorio** —se generó fuera del anfitrión y
sólo viajó el hash—: hay que tenerla a mano antes de grabar. Tabla completa en el **§5.8 de
`deploy/demo/README.md`**.

> **Y una cuenta que debe seguir fallando:** `admin` está **desactivada a propósito** en este entorno,
> porque el sembrador la recrea con una constante pública. Si alguien la prueba y la ve rechazada, el
> entorno está funcionando. No aparece en el vídeo.

---

## 2 · Tramo 1 — qué es esto · **0:00 → 0:15**

**Pantalla:** la URL pública con el candado del certificado a la vista.

**Qué se cuenta:**

> «Sistema de gestión de punto de venta de una joyería de Menorca con once tiendas abiertas. Sobre él,
> el Proyecto Final añade una capa de IA: búsqueda semántica, argumentario de venta con fuentes
> citadas y un agente que decide por sí mismo qué consultar. Catálogo real, 1.200 documentos
> vectorizados, desplegado en una cuenta AWS propia.»

**Qué debe aparecer:** la pantalla de login y el certificado válido. Nada más: quince segundos.

---

## 3 · Tramo 2 — búsqueda rápida, el camino feliz · **0:15 → 0:35**

**Cuenta:** `op-ciutadella` · **Ruta:** `/sales/new/assisted`, vía **búsqueda rápida**

**Se teclea, literalmente:**

```text
gargantilla de plata
```

**Qué debe aparecer, y es el punto del tramo:**

- Resultados **con el precio y las existencias de esa tienda** — no del catálogo global.
- Cada fila dice **por qué vía la encontró**: el catálogo no llama «gargantilla» a nada, lo llama
  «collar». El diccionario de sinónimos está **curado a mano** y es corregible en un commit.
- El panel dice **antes de la primera búsqueda** qué vías están encendidas.

**Qué decir:** *«el buscador que había acertaba 0,092 de nDCG@5; el que se entrega, 0,740. Tokenizar en
español aporta la mitad del salto y es gratis; la recuperación semántica y la fusión en dos etapas, la
otra mitad.»*

---

## 4 · Tramo 3 — la consulta libre, sin ninguna pieza delante · **0:35 → 1:05**

**Cuenta:** `op-ciutadella` · **Ruta:** `/sales/new/assisted`, vía **respuesta asistida**

**El coste se dice antes de pulsar**, y eso se enseña: treinta búsquedas por minuto contra diez,
respuesta inmediata contra unos segundos. **La elección no se recuerda entre visitas**, a propósito.

**Se teclea, literalmente:**

```text
algo para regalar a mi madre, que no sea muy llamativo
```

**Qué debe aparecer:**

- Las piezas **agrupadas por familia** y explicadas **en prosa**.
- **Fuentes desplegables**, distinguiendo un dato general de un **compromiso de la casa**.
- Ninguna cifra inventada: precio y existencias **los rellena el backend** con la verdad de la tienda.

**Y el segundo tecleo del tramo, que es el que demuestra el guardarraíl:**

```text
un salero de plata
```

**Qué debe aparecer:** una negativa que dice **«esto no es de una joyería»**, y no un «sin resultados».
Son códigos distintos porque ante un cliente se dicen de forma distinta.

**Qué decir:** *«118 de 120 argumentarios no escriben un solo dígito, y tres comprobaciones
deterministas —sin ningún segundo modelo haciendo de juez— revisan cada uno antes de que salga.»*

---

## 5 · Tramo 4 — la tienda pequeña: abstención, agotados y sustitutos · **1:05 → 1:30**

**Cuenta:** `op-fornells` · **Ruta:** `/sales/new/assisted` → ficha de venta

**Por qué esta cuenta:** `FORNELLS` lleva **241 filas de surtido, 29 de ellas agotadas**. Es la tienda
donde estos tres comportamientos **existen**; desde `CIU-CENTRE` no se verían.

**Se teclea, literalmente:**

```text
anillo de oro con perla
```

**Qué debe aparecer:**

- Lo agotado **baja en la lista, no desaparece** — esconder lo que la tienda quizá pueda vender es peor
  que mostrarlo último.
- Al abrir la **ficha de venta** de una pieza agotada: en lugar del argumentario, **los sustitutos que
  esa tienda sí puede vender hoy**, cada uno diciendo **por qué está ahí**.
- Si la pieza tiene varias tallas: **una fila y un botón por talla, ninguna preseleccionada**. Vender la
  talla equivocada exige elegirla a mano.

**Y la pregunta sobre la pieza**, en la caja de la ficha:

```text
¿se puede mojar?
```

**Qué debe aparecer:** la respuesta **citada**, resolviendo al fichero y al apartado exactos del corpus
—32 documentos, 161 fragmentos—. Y si el corpus no cubre la pregunta, **lo dice** en vez de contestar de
memoria.

---

## 6 · Tramo 5 — el agente, y el pivote · **1:30 → 2:15**

**Cuenta:** `op-aeroport` · **Ruta:** `/sales/new/agent`

**Es el tramo más largo del vídeo a propósito:** es el único pilar que no se puede enseñar de otra
forma, y el único que **no existía en pantalla** hasta el último mes del proyecto.

**Primer turno, literalmente:**

```text
busco un anillo de plata para un regalo
```

**Qué debe aparecer:**

- El ámbito por defecto es **su tienda**, nunca «todas».
- La cinta de espera dice **«~5 s típico, hasta 12 s»**, que es lo medido.
- La **tira de estado** dice por qué paró, cuántas vueltas y cuántas consultas — **y ninguno de los
  diez motivos de parada se pinta como avería**: pedir una aclaración o declinar cortésmente son
  desenlaces normales de una conversación.
- **«Cómo lo ha averiguado»** se despliega y enseña la escalera de pasos con el nombre de cada
  herramienta. **No debe aparecer ningún argumento de herramienta ni contenido de observación.**

**Segundo turno — el pivote, y se nombra por la REFERENCIA (véase §0.2), literalmente:**

```text
El cliente quiere la referencia SKU759, ¿la tenemos?
```

**Qué debe aparecer, y es lo que hay que provocar:**

- En la traza: `consultar_disponibilidad` → **`buscar_sustitutos`**. Que aparezca `buscar_sustitutos` es
  **la prueba de que pivotó** y no de que la búsqueda trajo otra cosa.
- Las piezas bajo **«Alternativas»**, rotuladas como tales. **Un sustituto nunca debe salir bajo
  «Coincidencias»**: ofrecer un segundo mejor haciéndolo pasar por lo que se pedía es lo que un cliente
  nota.
- El bloque del **primer turno colapsa a una línea** y el nuevo queda abierto. **Cada pregunta conserva
  su respuesta**: una pantalla que refrescara un único bloque dejaría al joyero leyendo el argumento de
  una pregunta sobre las piezas de la siguiente.

> **Piezas agotadas de verdad, comprobadas en `ai.pos_projection`** — por si hay que repetir la toma:
> `CIU-CENTRE` → `SKU759`, `SKU783`, `SKU813` · `MAO-AIR` → `SKU1136`, `SKU1112`.

**Qué decir:** *«seis herramientas de sólo lectura, hasta ocho consultas por respuesta, y la capacidad
de cambiar de idea a mitad de camino. De veinte escenarios de calibración, **diecisiete cumplen su
expectativa**, y los tres que no están nombrados en el informe con su motivo — no se publica una tasa
porcentual porque el ruido entre pasadas está medido en dos de veinte.»*

---

## 7 · Tramo 6 — el panel de administración · **2:15 → 2:35**

**Cuenta:** `demo.admin` · **Ruta:** el dashboard

**Al entrar salta el aviso de §0.1.** Se cierra y se sigue: ya está explicado.

**Qué se enseña, que es la tarjeta de salud de la IA:**

- El servicio responde, la base de datos está alcanzable, **1.200 documentos** indexados, y el modelo de
  *embeddings* configurado **coincide** con el del índice — una discrepancia ahí devolvería resultados
  sin sentido **sin dar ningún error**.
- La **edad de la proyección** del surtido: se refresca al arrancar y cada diez minutos. En la lectura
  del 2026-09-27: **95 s** de edad contra un techo de 3.600 s.
- **Ninguna línea roja de tiendas sin surtido sincronizado**, y eso es el final de una historia: esa
  línea existió, marcó en rojo un despliegue sano porque contaba una tienda **cerrada a propósito** como
  una tienda rota, y se arregló contando sólo tiendas activas. Hoy `shops_without_scope` es **0**.
- El diagnóstico separa **lo que tardó el proveedor de lo que tardamos nosotros**, con el modelo y los
  tokens, y **nunca un importe**: una tarifa escrita en una pantalla está mal el día que el proveedor la
  mueve.

---

## 8 · Tramo 7 — cierre: qué se midió y qué no · **2:35 → 2:50**

**Pantalla:** el informe de evidencias o la tabla de ablations.

**Qué se cuenta, y es lo que hay que decir para cerrar:**

> «Nada de lo anterior se decidió por intuición. **48 consultas juzgadas a mano** con una escala de tres
> grados y un criterio escrito **antes** de etiquetar; una tabla de ablations que va del buscador que la
> joyería tenía hasta el que se entrega; y tres objetivos numéricos que **no se alcanzaron y se declaran
> como tales** en lugar de bajar el listón después de medir.
>
> Y las limitaciones están escritas con su vía de cierre: el agente no llega a la pieza si se la nombra
> por su nombre; el reconocimiento de imagen no puede tener modelo en este entorno; el golden set lo
> etiquetó **una sola persona**, así que no hay acuerdo entre anotadores que publicar; y hay un solo
> agente, el de venta — el de inventario está diseñado y no implementado.»

---

## 9 · Lista de comprobación antes de grabar

- [ ] Contraseña de `demo.admin` a mano. **No está en el repositorio.**
- [ ] El entorno responde: `https://52-49-209-14.sslip.io` con certificado válido.
- [ ] La proyección **no está rancia** — la tarjeta de salud lo dice; hoy, 95 s contra 3.600.
- [ ] `SKU759` **sigue agotada** en `CIU-CENTRE`, o se usa otra de la lista del tramo 5.
- [ ] **Cuota del proveedor:** del orden de **una petición por minuto** (~13.000 tokens contra 25.000
      TPM). Suficiente para un recorrido; **no para dos mostradores a la vez**. Si hay que repetir una
      toma del tramo del agente, esperar entre intentos.
- [ ] Los tramos 3, 4 y 6 **no se pueden hacer con la misma cuenta**: el surtido es lo que los hace
      observables.
- [ ] Ensayo en seco de los tramos 5 y 6 seguidos, que son los que llevan el presupuesto de tiempo más
      justo.
