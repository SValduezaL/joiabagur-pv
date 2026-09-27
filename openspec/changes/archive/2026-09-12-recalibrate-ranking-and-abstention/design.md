## Context

El recuperador está completo —expansión (C20), fusión RRF (C21), prefiltro por punto de venta
(C22)— y desde C24 existe un juez: 48 consultas juzgadas a mano con relevancia graduada y un
criterio escrito antes de etiquetar. Al usarlo aparecieron cosas que ningún argumento había
detectado, y este change las resuelve.

**Estado verificado antes de diseñar** (mediciones completas en
[c25-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c25-exploration-measurements.md)):

| Hecho | Cifra |
|---|---|
| `descripcion-sin-anclaje`, la categoría más grande | híbrido **0,172** frente a vectorial sola **0,431** |
| Dónde cae el grado 2 que la vectorial pone en el #1 | **posición 33** en `q06`, `q08`, `q10` |
| Los 32 anteriores | **sólo léxicos**; la cola conserva **exactamente** el orden vectorial |
| Penalización de disponibilidad de C22 en la evaluación | **no se disparó ni una vez** en 192 filas |
| Abstención sobre fuera-de-dominio | **0,000** en las tres configuraciones de pipeline |
| `Recall@5` sobre la porción real | **0,483** contra un criterio de 0,85 |
| Consultas de la partición de ajuste en el techo del nDCG@5 | **6 de 8** (y **8 de 8** en Recall@5, P@3 y MRR) |
| Consultas de ajuste procedentes de la lista curada de C20/C21 | **7 de 8** |
| `sales_30d` no nulo sobre pares asignados | **23,54 %** (1.424 de 6.050) — se lee para diagnóstico y **no ordena** (D10) |
| `p95` de recuperación contra presupuesto | 128,6 ms contra 500 ms |

**Restricciones que gobiernan el diseño.** El pool de conexiones está capado en 5 con
`max_overflow=0`. `ai-service/openapi.json` está congelado desde C02. `fusion.py` es puro y sin
dominio por decisión de C21. La cantidad exacta de stock es de .NET y nunca sale del bucket. El
reloj de las ventanas de venta es el `computed_as_of` de cada fila y nunca `now()`, porque el
mundo de C10 termina el 2026-08-23.

## Goals / Non-Goals

**Goals:**

- Que la rama vectorial pueda colocar un resultado en el top-5 **sin permiso de la léxica**, y que
  la corrección **no cobre peaje** donde la léxica acierta.
- Que la disponibilidad real del punto de venta pese en el orden, **medida** y no supuesta — y
  que lo que no se pueda medir no pese, que es lo que retiró la rotación (D10).
- Que el buscador tenga una regla para no contestar, fijada con la cantidad que de verdad decide.
- Que cada efecto sea **atribuible a su causa** en la tabla de ablations.
- Que la línea base publicada por C24 siga siendo reproducible después del change.

**Non-Goals:**

- Alcanzar el criterio absoluto del §11.2 (`Recall@5 ≥ 0,85`): es +0,37 y ninguna palanca de este
  change puede cerrarlo. Se sustituye por criterio relativo y se declara la brecha.
- Penalizar la variante ambigua dentro de familia — retirado, refutado por medición (D16).
- Calibrar `1-2` frente a `3+` — retirado, refutado por construcción (D17).
- **Ordenar por rotación** — retirado durante el apply, refutado por medición (D10).
- Reranking, sustitutos (C26), RAGAS y escenarios de agente (C38).
- Migración de Alembic, ruta HTTP nueva, regeneración de `openapi.json`, reindexado.
- Cualquier diff en `backend/`, `frontend/`, `terraform/` o `.github/workflows/`.
- **Retirar la fusión plana.** La tabla necesita su fila de referencia; la limpieza es el change
  posterior `clean-plain-fusion`.

## Decisions

### D1 · Dos capacidades, no una

`business-signals-ranking` y `retrieval-abstention`. Comparten el golden set y nada más: ponderar
el orden y decidir si contestar son preocupaciones distintas, con requisitos y tests distintos.

*Alternativa descartada:* una capacidad única. Habría mezclado en un mismo documento normativo la
regla que ordena y la que calla, y el aviso del `CLAUDE.md` sobre las tres specs malformadas de
agosto pesa aquí: tres requisitos ajenos modificados desde una capacidad nueva es la forma de
sincronización que queda bien formada y falsa.

### D2 · Criterio de aceptación relativo

`v2b` bate a `v2` y `v3` bate a `v2b`, en las lecturas que decide D14 y por encima del margen de
0,05. La brecha absoluta contra el §11.2 se declara como limitación del README.

*Razón:* `Recall@5` real está en 0,483 contra 0,85, y la única palanca de relevancia medida
—subir el peso vectorial— dio +0,057 global. El recall a 5 depende de **qué** entra en la ventana
y las señales sólo reordenan lo que ya entró. *Precedente:* C18 encontró que *«el umbral del §7.5
no existe, y el plan se contradecía»*; el 0,85 se fijó antes de que existiera un golden set y
antes de saber que `relevant_total` puede valer 144 para una consulta.

*Alternativa descartada:* medir contra el 0,85 y declarar el fallo. No distingue «no mejoró» de
«el listón estaba mal puesto».

> **Corrección del denominador, 2026-09-11.** Las lecturas de relevancia se promedian sobre las
> consultas **contestables**, no sobre todas. Una de `fuera-de-dominio` tiene el ideal vacío, así
> que puntúa 0 para toda configuración por construcción: promediarla no informa del orden y
> **comprime toda diferencia**. Medido al ampliar la categoría de 5 a 20, la mejora de la fusión
> por rama leyó **+0,053** con ellas dentro y **+0,084** fuera — con un margen de 0,05, una mejora
> real se quedó a tres milésimas de ser vetada por la composición del conjunto en vez de por su
> mérito, y crecer más la categoría la vetaría del todo. Una métrica se promedia sobre las
> consultas que puede medir; `fuera-de-dominio` se informa por la tasa de abstención.
>
> **Resultado medido el 2026-09-11, al cerrar la fase C.** El criterio se cumple para una de las
> dos filas y **no** para la otra, y las dos cosas se declaran:
>
> | | lectura | delta | ¿supera 0,05? |
> |---|---|---:|---|
> | `v2b` contra `v2` | `new` | **+0,073** | **sí** |
> | `v3` contra `v2b` | operativa | +0,027 | **no** |
> | `v3` contra `v2b` | pura (`new`) | −0,014 | no |
>
> **`v3` se adopta igualmente, y por qué no es una excepción *ad hoc*.** Son dos preguntas
> distintas con dos reglas distintas. La regla de adopción del peso —la que define la capacidad
> `business-signals-ranking`— pregunta *¿es seguro encender esta señal?* y se cumple entera:
> el objetivo operativo sube, el guardarraíl de relevancia pura aguanta con −0,014 y ninguna
> categoría veta. D2 pregunta *¿ha demostrado esta fila que merece existir?* y la respuesta
> honesta es **no con este instrumento**.
>
> Lo que falta es **resolución**, no evidencia. El golden set es estructuralmente ciego a la
> disponibilidad —hallazgo 1 de la exploración: `criterion.md` no menciona stock ni rotación—, y
> la métrica operativa de D3 lo hace visible sin darle más resolución a un conjunto de 48
> consultas cuyo margen resoluble es 0,05. Exigir que una señal que la rúbrica no ve supere el
> umbral de ruido de la rúbrica es pedirle al instrumento que mida lo que declaró no medir.
>
> A favor de encenderla pesan tres cosas que el agregado no muestra: el signo se mantiene en
> **los tres puntos de venta** con magnitud proporcional a la densidad de la señal (+0,027 al
> 34,4 % de surtido a cero, +0,013 y +0,004 al 12 %); el efecto es **quirúrgico**, sólo mueve
> las 13 consultas afectadas de 48; y retira el **91 %** de las piezas agotadas del top-5, que
> es un fallo operativo —enseñar al cliente algo que no está en el cajón— que ninguna métrica de
> relevancia captura.
>
> *Alternativa descartada:* apagar la señal y enviar la capacidad inerte. Es defendible y más
> conservadora, pero confunde «el instrumento no resuelve esta diferencia» con «no hay
> diferencia», y deja sin entregar lo único que C22 construyó la proyección para habilitar.
> La brecha se **declara**, que es lo que D2 ya hace con la absoluta del §11.2: dos limitaciones
> escritas valen más que una escondida.

### D3 · Métrica objetivo derivada, sin re-etiquetar

```
g_efectivo(doc) =  grado                si qty_bucket ≠ '0'
                   máx(grado − 1, 0)     si qty_bucket = '0'
```

Objetivo: `nDCG@5 operativo`. **Guardarraíl:** `nDCG@5` de relevancia pura no cae más de 0,05.
Las dos se publican, y `judgements.jsonl` no se modifica.

> **Pre-registro, escrito el 2026-09-11 antes de calcular ninguna métrica** (tarea 1.5). La
> función de ganancia operativa queda fijada arriba y **no se retoca después de ver un
> resultado**: `g_efectivo = grado` cuando `qty_bucket ≠ '0'`, y `máx(grado − 1, 0)` cuando
> `qty_bucket = '0'`. Un candidato **sin fila de proyección** —porque la consulta corrió sin
> alcance de lectura, o porque ese punto de venta no lo lleva— **conserva su grado**: la ausencia
> de señal no es evidencia de stock cero, y tratarla como `'0'` convertiría la cobertura de
> surtido en una penalización de relevancia.
>
> **Justificación desde la escala de `criterion.md`, no desde una constante nueva.** La rúbrica
> define el grado 1 como *«sustituto plausible que el operador ofrecería como segunda opción»*, y
> una pieza que no se puede poner sobre el paño es exactamente eso: bajar un peldaño por
> agotamiento **aplica** la rúbrica en lugar de torcerla. El grado 0 no puede bajar más, de ahí
> el `máx(·, 0)`. Por eso la transformación no introduce ningún número mágico —no hay
> multiplicador, no hay `+0,3 si hay stock`— y `criterion.md`, `judgements.jsonl` y
> `golden_set_version` quedan **intactos**.
>
> **Guardarraíl y su umbral, fijados aquí:** una configuración que mejore el operativo y degrade
> la relevancia pura más de **0,05** —en agregado o en cualquier categoría medida— **no se
> adopta**, y el informe registra la diferencia medida y la decisión de no actuar.

*Razón:* `criterion.md` no menciona stock ni rotación, así que un barrido que maximice nDCG@5
converge a **peso 0** en todas las señales — la instrucción de la ficha, tomada al pie de la
letra, es una máquina para demostrar que la funcionalidad no debe existir. Y la transformación
**no inventa una constante: reutiliza la escala**, porque el grado 1 ya está definido como
*«sustituto plausible que el operador ofrecería como segunda opción»* y una pieza que no se puede
poner sobre el paño es exactamente eso. *Precedente:* C24 ya publica dos lecturas de la misma
anotación y declara la comparación robusta porque ordenan igual.

*Alternativas descartadas:* re-etiquetar con disponibilidad en la rúbrica (mueve `criterion.md`,
mueve `golden_set_version` y destruye la comparabilidad con la línea base); inventar un
multiplicador (`+0,3 si hay stock`), que es el número mágico del que avisa el apunte de S10.

### D4 · La señal de punto de venta se separa del alcance

Dos parámetros independientes de `retrieve_products`, no un flag `scoped` que hace dos cosas:

```sql
WITH scope AS MATERIALIZED (
  SELECT product_id, qty_bucket, sales_30d
  FROM ai.pos_projection
  WHERE pos_id = :pos_id AND is_assigned_hint IS TRUE
)
-- alcance (C22):  JOIN scope s ...        restringe el universo
-- señal  (C25):   LEFT JOIN scope s ...   sólo lee
```

En evaluación: `scope_pos_id = None`, `signal_pos_id = <POS de referencia>`. **Calibrar en
MAO-AIR** (34,4 % del surtido a cero), **validar en FORNELLS** (12,0 %) y **HT-GALDANA** (11,7 %).
`HT-ARTRUTX` excluido: surtido cero, responde 503.

*Razón:* mide la reordenación **sin** pagar el coste de recall del prefiltro, que es la confusión
que C22 se negó a introducir y que su propia configuración declara como no medida. Y calibrar
donde la señal apenas aparece es calibrar sobre ruido; calibrar sólo en el extremo es ajustar a
una tienda atípica — de ahí la validación en dos típicas, que es la disciplina de las tres
lecturas de C24 trasplantada al eje del punto de venta.

*Alternativa descartada:* activar el prefiltro en la fila de evaluación. Mide lo que el operador
vive, a costa de confundir en una cifra la reordenación con el coste de recall.
*Descartada también:* promediar sobre los once puntos de venta — una media que ninguna tienda
experimenta, y once veces el barrido.

### D5 · Fusión en dos etapas, con pesos por rama

```
   ETAPA 1 — dentro de la rama léxica
     typed     (websearch_to_tsquery del texto crudo, AND)   w_int = 0,5
     expanded  (OR de los grupos de equivalencia de C20)     w_int = 0,5
          └─── fuse(k, depth) ───▶ UNA lista léxica          (sólo sobrevive el ORDEN)

   ETAPA 2 — entre ramas
     lexical / vector                                        w_lex / w_vec
          └─── fuse(k, depth) ───▶ lista final
```

*Razón, en tres partes.* **(a)** El voto total de la rama pasa a ser exactamente `w_lex`, sin
depender de cuántas de sus listas dispararon: hoy el umbral de cruce es **0,469 o 0,938** según si
el AND de `websearch` casó, una propiedad de la consulta que nadie declaró y que gobierna el
resultado. **(b)** Arregla un segundo sesgo que nadie había visto: `typed` y `expanded` se truncan
por separado, así que la rama léxica puede meter **120 documentos** frente a los 60 de la
vectorial — **el doble de huecos y el triple de voto**, corregidos con un solo cambio.
**(c)** En la etapa 2 hay dos listas que son dos ramas, así que `len(ranks) > 1` **es** el
consenso entre ramas y `low_confidence` deja de necesitar la excepción que su docstring explica
hoy.

*Coste declarado:* de la etapa 1 sólo sobrevive el orden, así que la **magnitud** del consenso
intra-léxico se aplana — un documento #1 en las dos listas y otro #1 en una y #40 en la otra
pueden acabar adyacentes. La defensa es que eso es lo que RRF hace en todos sus niveles: su
premisa es que el rango es la moneda comparable, y el **orden** del premio al consenso se conserva
íntegro.

*Reparto interno 0,5 / 0,5, fijo y no barrido.* La evidencia de C21 establece que las dos listas
son **necesarias** —`typed` rescata los nueve productos llamados «Sortija», `expanded` rescata
`gargantilla`— no que una valga más. Una asimetría sería un número mágico sin hipótesis, y una
perilla sin hipótesis se ajusta al ruido de 48 consultas.

### D6 · Sólo importa el cociente, así que el barrido es de una dimensión

Medido ejecutando `fuse()`: escalar los dos pesos preserva el orden, luego sólo cuenta
`ρ = w_vec / w_lex`. Posición del #1 vectorial con lista léxica de 60 sin consenso (predicción del
modelo y medición coincidentes en los once puntos):

| `ρ` | 0,33 | 0,50 | 0,75 | 0,85 | 0,90 | **0,95** | 0,98 | 1,00 | ≥1,10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| posición | 61 | 61 | 22 | 12 | 8 | **5** | 3 | 2 | 1 |

**Banda útil `ρ ∈ [0,9 ; 1,1]`**, donde la rejilla de C24 tenía **un solo punto**: por eso su
óptimo parecía un filo de cuchillo — `wC = 1,0` es el umbral de cruce exacto del régimen en que
las dos listas léxicas coinciden. Rejilla: `{0,6 · 0,8 · 0,9 · 0,95 · 1,0 · 1,05 · 1,1 · 1,25}`,
normalizada como `w_lex + w_vec = 1`. `k` y `depth` se conservan en 60/60 y se re-barren **juntos**
por la regla de C21 (*depth ≈ k*).

**Arranque `ρ = 1,0`**, valor **de principio** y no ajustado: *cada rama tiene un voto; el mejor
resultado de cada rama ocupa uno de los dos primeros puestos, y lo que las dos señalan va
primero*. Con `ρ = 1` el resultado es consenso primero y **round-robin** después, que es la
propiedad que se puede explicar en una frase — la prueba que exige el apunte de S10.

### D7 · Ponderación adaptativa por cobertura, con cero parámetros

```
                coordinación del MEJOR documento de la lista expandida
   cobertura = ───────────────────────────────────────────────────────
                grupos contables cuya tsquery NO es vacía

   w_lex_efectivo = w_lex × cobertura
```

El numerador es gratis: la lista viene `ORDER BY coordination DESC`, luego
`expanded_hits[0].coordination` **es** el máximo. La señal ya se calcula, viaja en `LexicalHit` y
**el orquestador no la lee nunca** — cuarto cable pelado, tras `tsv`, la expansión y `qty_bucket`.
C21 confió en una ponderación adaptativa *emergente* y no emerge: `ts_rank` sigue ordenando 60
documentos que siguen ganando todos.

*Razón para preferirla a subir `ρ` globalmente:* ataca el daño **donde está**. `wC = 1,0` paga
`sinonimos` −0,039 y `materiales` −0,010 en todas las consultas; la adaptativa tiene **efecto
predicho cero** en las categorías de cobertura 1,00.

**Se adopta la forma continua** (pregunta abierta 4, opción por defecto) por tener cero
parámetros.

> **Cerrado por medición el 2026-09-11, durante el apply.** La forma binaria se implementó, se
> midió y **se retiró**; y el barrido que la comparaba resultó estar mal planteado.
>
> **(a) La binaria es indistinguible de la continua** en los 16 puntos de la rejilla, hasta el
> último decimal. No por un fallo de cableado —el log da `w_lex_effective` 0,1250 con la continua
> y 0,2500 con la binaria para la misma cobertura de 0,250— sino por dos razones: `α = 0,5`
> coincide con la cobertura parcial **más frecuente** del conjunto, que es 0,50, donde las dos
> calculan lo mismo; y donde sí difieren, ambas dejan el cociente efectivo **por encima del punto
> de saturación** de la fusión. Comprobado con `α = 0,1`: mismo top-5. Pierde por **coste**, no
> por resultado, y con ella desaparece el último número que parecía ajustado del change.
>
> **(b) Faltaba el brazo de control.** Comparar dos formas de la misma idea no dice si la idea
> sirve. Añadido `coverage_rule: none` —la misma fusión con la regla apagada— la respuesta es
> inequívoca:
>
> | | control | adaptativa | delta |
> |---|---:|---:|---:|
> | `descripcion-sin-anclaje` (n=12) | 0,289 | **0,417** | **+0,128** |
> | las otras **siete** categorías | — | — | **+0,000 exacto** |
> | `new` (decide) | 0,571 | **0,608** | **+0,037** |
>
> **(c) Y la regla hace algo que el nDCG agregado no deja ver: convierte `rho` de acantilado en
> meseta.** El recorrido del barrido sobre `rho` en la lectura que decide pasa de **0,070 sin la
> regla a 0,007 con ella**. El control reproduce exactamente el cruce que predijo la exploración
> —0,536 en `rho = 0,9` contra 0,606 en `rho = 1,1`—, que es el «filo de cuchillo» de C24 medido.
> Más aún: **la adaptativa bate al mejor `rho` afinado a mano** (0,608 en el arranque de principio
> contra 0,606 del mejor control), y llega sin ajustar nada. La razón es que `rho` es global y la
> cobertura es por consulta: subir `rho` ayuda a las consultas sin anclaje y **paga** en las
> ancladas, mientras que la adaptativa sube el cociente efectivo **sólo donde hace falta**.
>
> Quedan **dos** valores de `coverage_rule` y ninguno es un parámetro de fuerza: `continuous`
> (adoptada) y `none` (control y marcha atrás).

### D8 · El denominador excluye los grupos de `tsquery` vacía

Es el punto crítico del change. Medido con `expand_query` + `counting_flags`, las palabras vacías
**cuentan como grupo** y su `plainto_tsquery` es vacía:

```
'sortija de plata'       →  ['sortija','anillo','aro de dedo']  ['de']  ['plata']
'anillo de plata y oro'  →  ['anillo','aro de dedo'] ['de'] ['plata'] ['y'] ['oro']
```

| consulta | denominador ingenuo | corregido | nDCG@5 hoy |
|---|---:|---:|---:|
| `sortija de plata` | 2/3 = **0,67** ✗ | 2/2 = **1,00** ✓ | 1,000 |
| `anillo de plata y oro` | 3/5 = **0,60** ✗ | 3/3 = **1,00** ✓ | — |
| `una bicicleta antigua` | 1/3 = 0,33 | 1/2 = **0,50** ✓ | 0,000 |
| `follaje seco que cae en septiembre` | 1/6 = 0,17 | 1/4 = **0,25** ✓ | 0,100 |

**Con el ingenuo la regla recorta un tercio del peso léxico en una consulta que puntúa nDCG
1,000**: destruiría exactamente las categorías que existe para no tocar, y lo haría pareciendo
que funciona porque el agregado global podría subir igual.

*Implementación:* el denominador es constante por consulta y se calcula en la **misma sentencia**
que ya tally-a la coordinación, con `numnode(<fragmento del grupo>) > 0`. Sin viaje extra al pool.

*Alternativa descartada:* usar la vacuidad de la lista `typed` como discriminador. Misfire medido:
`bano de oro` no casa el AND (el corpus dice «baño») y la regla crujiría una consulta que puntúa
1,000.

### D9 · Score continuo sólo en el último bloque

```
  HOY   (precio↑, talla↑, material↑, stock↑)           cuatro enteros
  C25   (precio↑, talla↑, material↑) ▸ −score_negocio   continuo en la cola
```

*Razón:* conserva el requisito vivo de `pos-projection` —*«dentro del techo precede a fuera, sea
cual sea el stock»*—, acota el radio de explosión de los números mágicos que el apunte de S10
avisa, y **no pierde alcance**: `demote()` hace *early return* cuando ningún filtro tecleado se
dispara, que es el caso mayoritario, así que la clave es `(0,0,0)` para todos y el bloque de cola
**es la lista entera** donde importa.

*Alternativa descartada:* suma ponderada de todo. Seis pesos acoplados, rompe la garantía
lexicográfica —suficiente evidencia de stock derribaría un techo de precio explícito— y es
exactamente el sistema del que S10 dice que *«nadie sabe ya por qué un documento quedó tercero»*.

### D10 · La rotación se retira del orden: se lee para diagnóstico y no ordena nada

> **Corregido el 2026-09-11, durante el apply y por medición.** La versión anterior de esta
> decisión metía `sales_30d` como última clave con peso fijo y declarado. Se retira del orden.
> `sales_30d` **se sigue leyendo y viajando** en los *hits* y en las ventanas capturadas, para
> que el informe publique su distribución y C26 tenga insumo; lo que desaparece es el término
> del score y su peso. La prohibición vuelve a ser **estructural**: el protocolo `Constrained`
> que lee `demote` no tiene el campo, así que la ordenación no puede consumirlo ni por
> accidente.

*Razón, y es de medición y no de cautela.* La frase que justificaba el desempate —*«entre dos
piezas que el recuperador y el stock empatan, enseña la que se vende»*— sigue siendo cierta en un
mostrador. Lo que la medición establece es que **este recuperador no produce la situación que la
frase describe**, y que implementarla como clave hace algo muy distinto de lo que declara:

| lectura | qué hace | cifra |
|---|---|---|
| **desempate estricto**, como decía su propio requisito | actuar sólo entre candidatos que la fusión ordena **igual** | **0 pares** del top-5 en las 48 consultas |
| **clave de ordenación**, como estaba implementada | partir el bloque entero en dos y reordenarlo | **11.067** pares invertidos |

Los empates exactos existen y son frecuentes —**662 pares, el 35 %** de los candidatos, porque
en RRF `w/(k+1) + w/(k+2)` empata con `w/(k+2) + w/(k+1)`— pero **ninguno dentro del top-5**
enfrentaba a un vendedor con un no-vendedor. Y como clave no desempataba: sólo el **3,4 %** de
los pares que invertía eran adyacentes en la fusión, mientras que el **71,2 %** estaban separados
por más de diez puestos, con un salto mediano de **21 posiciones**. La razón es estructural: un
indicador binario al final de una clave lexicográfica **no desempata, particiona**, y como el
40 % del surtido de MAO-AIR vendió algo, partía la lista casi por la mitad.

Donde actuaba, costaba: **6 de las 22** entradas nuevas al top-5 desplazaban a un documento de
mejor grado, y el agregado pagaba en las dos lecturas —relevancia pura 0,595 → 0,584, operativa
0,656 → 0,645—. **Un mecanismo que sólo puede ser un no-op o un error no se ajusta: se retira.**
Es la misma aritmética de D17 aplicada aquí: cuando las lecturas legítimas se cancelan, el peso
honesto es cero, y un peso declarado que no ordena nada es peor de explicar que no tenerlo.

*Se gana además la propiedad que más vale:* el modelo de negocio queda en **un solo peso** y en
una sola frase — *«una pieza de la que la tienda se ha quedado sin existencias se enseña después
de las piezas comparables que sí tiene»*.

*Alternativas descartadas.* Conservar el término en cero sin retirar la perilla: mantiene un peso
que no hace nada, que es justo lo que el apunte de S10 avisa de no dejar en un sistema. Y el
decaimiento exponencial sobre `last_sale_at`, más denso (4.021 filas no nulas frente a 1.424)
según el mismo apunte — su `date.today()` es la trampa que C22 ya cerró, y sigue sin tener gancho
en la rúbrica.

### D10b · El peso de disponibilidad decide su signo, no su valor

Medido en el barrido de la fase C: con un único término binario el score de negocio toma **dos
valores**, así que el orden es **invariante al valor del peso**. Siete puntos de rejilla —0,25,
0,5, 0,75, 1,0, 1,5, 2,0— dan cifras idénticas hasta el último decimal.

*Consecuencia:* lo que la calibración decide es **encender o apagar** la señal, y `1,0` queda como
**unidad declarada** y no como cifra ajustada. El informe lo dice así en lugar de publicar un
«peso calibrado» que no calibra nada. El peso sigue siendo un `float` configurable porque el cero
es la marcha atrás, que es lo que la spec de `pos-projection` exige.

### D11 · La abstención se diseña después de medir, y la medición es otra

C24 midió el solape **por documento** (grado 2 hasta 0,8008, grado 0 desde 0,3268, hueco
**−0,4739**) y concluyó que un escalar no sirve. Cierto, y **no es la cantidad que decide**: la
abstención la decide el **mejor acierto por consulta**, y esa cantidad **no está en ningún
artefacto** — el JSONL por consulta guarda métricas, no distancias. C23 separó limpiamente con
exactamente esa cantidad: 0,5062 contra 0,5145, ocho milésimas.

**Se adopta la opción por defecto de la pregunta abierta 1: la forma la dicta la medición M1**, y
el diseño fija las dos ramas y el criterio de elección **antes** de mirarla:

> **Pre-registro, escrito el 2026-09-11 antes de mirar la distribución de M1** (tarea 1.4). El
> criterio que elige la forma de la regla es **la separabilidad de las dos poblaciones por un
> solo valor**, evaluada así y no de otra manera:
>
> Sea `A` el conjunto de los `min(distancia)` de las **43 contestables** y `F` el de las **5 de
> fuera de dominio**. Se adopta la forma **escalar (fase A)** si y sólo si
> **`máx(A) < mín(F)`** — es decir, si existe un valor que las separa **sin cortar ni una sola
> contestable**. En cualquier otro caso se adopta la **regla relativa por consulta (fase D)**.
>
> **El empate se resuelve hacia la relativa**: `máx(A) = mín(F)` **no** separa, porque el umbral
> tendría que caer exactamente sobre una contestable. Y un solape de una sola consulta ya manda
> a la fase D: la asimetría es deliberada y su razón está en D12 —asignar mal la fase es un
> **fallo silencioso**, y el error de mandar a la fase D algo que cabía en la A sólo cuesta
> trabajo, mientras que el inverso invalida todas las ventanas capturadas sin avisar.
>
> **Ninguna otra cantidad decide la forma.** Ni el tamaño del hueco, ni la distribución por
> documento de C24, ni el resultado de ninguna configuración: si la regla se eligiera por lo
> bien que sale, sería un ajuste *post hoc* con otro nombre. El margen de C23 —ocho milésimas—
> se cita como precedente de que la forma escalar **puede** salir limpia, nunca como umbral
> mínimo de hueco exigido.

| Resultado de M1 | Forma adoptada | Fase |
|---|---|---|
| Existe un valor que separa las contestables de las de fuera de dominio | **Escalar** sobre `min(distancia)`, como C23 | **A** — está en el `WHERE`, **mueve la ventana** |
| Las dos poblaciones se solapan | **Regla relativa por consulta** (`d ≤ d_min·(1+α)`), combinable con el `low_confidence` que ya existe | **D** — post-recuperación, **no mueve la ventana** |

`fuera-de-dominio` pasa de **5 a 15-20** consultas: por la rúbrica todo es grado 0 ahí, así que no
hay etiquetado documento a documento, y con n=5 la única cifra de aceptación alcanzable no es
creíble. El lado difícil es subir la abstención **sin** empezar a callar en las contestables.

> **Resuelto el 2026-09-11, midiendo sobre las 20.** La forma la eligió M1 —contención total, así
> que un escalar no separa— y M9 la afinó: lo que discrimina no es el nivel sino la **forma del
> perfil**, porque una consulta imposible es **plana**. La regla queda
> `abstenerse si |{d ≤ d_min·(1+α)}| ≥ N`, con **`α = 0,03`, `N = 15`**, fijados contra la
> categoría **ya ampliada** y nunca contra las cinco originales.
>
> **Caza 2 de las 20 y no silencia ninguna de las 43 contestables.** Sólo hay otros dos puntos
> con coste cero y cazan menos. El objetivo de **0,80** de la ficha cuesta silenciar **21 de las
> 43** — la mitad del conjunto— y se declara como brecha, igual que la del §11.2.
>
> La regla **no es redundante**: `low_confidence` marca 1 de 20 imposibles y 10 de 43
> contestables, o sea que está anticorrelada con lo que la abstención necesita. Y se puede
> apagar sin desplegar.

### D12 · La medición M1 gobierna la secuencia, no sólo la forma

Asignar mal la fase es un fallo silencioso: el barrido corre y da números. Si el umbral es un
escalar en el `WHERE`, cambia el conjunto de candidatos e **invalida todas las ventanas
capturadas**, así que va antes de capturarlas.

### D13 · Barrido en dos fases

```
  fase A — FIJAR LA FUSIÓN   con proveedor · la ventana SE MUEVE
              ↓ congelada
  fase B — CAPTURAR          1 recuperación por consulta; se persiste la ventana de 60
                             con qty_bucket, sales_30d, family_id, score y ramas
              ↓ ventana INMÓVIL
  fase C — FIJAR LAS SEÑALES re-puntuado en memoria · cero proveedor · cero base
```

*Razón:* las señales no cambian **qué** se recupera, sólo el orden —`demote()` es un `sorted`
estable que no elimina nada—, así que cientos de combinaciones se recorren en segundos y
`test_calibration_sweep_is_reproducible` pasa de promesa sobre semillas a **propiedad
estructural**. **El orden es una restricción, no una preferencia.**

### D14 · La regla de decisión se reformula, con argumento y fecha, antes de re-medir

> **Escrito el 2026-09-11, antes de ejecutar ningún barrido** (tarea 1.3). La lectura que decide
> es **`new`** (40 consultas, nunca vistas por ninguna calibración). `tuning` se reporta como
> **diagnóstico de contaminación** y no veta. El margen sigue en 0,05 y ninguna categoría medida
> puede caer más.
>
> **Procedimiento, fijado aquí y aplicado sin excepciones.** Un candidato desplaza al titular si
> y sólo si cumple las dos condiciones:
>
> 1. **Mejora material en la lectura que decide.** `nDCG@5(candidato, new) − nDCG@5(titular, new)
>    > 0,05`. Estrictamente mayor: un empate en el margen no mueve un default.
> 2. **Ninguna categoría paga más que el margen.** Para **toda** categoría medida con `n ≥ 1` en
>    la lectura `new`, `ΔnDCG@5 ≥ −0,05`. Una sola categoría por debajo de **−0,05** veta la
>    adopción, y el informe **nombra la categoría que pagó**.
>
> `tuning` (8 consultas) se publica siempre junto a las otras dos lecturas, con su **recuento de
> saturación** —cuántas están en el techo de la métrica que decide—, y **no entra en ninguna de
> las dos condiciones**. Cuando `tuning` discrepa de `new`, el informe lo declara como
> desacuerdo y lo nombra contaminación, en lugar de resolverlo a favor de `tuning`.
>
> **Lo que esta regla no puede hacer.** No se re-pondera, no se exime ninguna categoría *ad hoc*,
> y **no se retoca después de ver un resultado**. Si el barrido produce un ganador que esta regla
> veta, el veto se publica con sus cifras y el default **no se mueve**.
>
> **Corrección del 2026-09-11, antes de medir:** una redacción anterior de este bloque añadía que
> «la partición de ajuste **crece** en la sesión de etiquetado». **Se retira**, por la misma razón
> que cierra la pregunta abierta 3: `in_tuning_set` registra un **hecho histórico** —qué consultas
> calibraron qué— y no una elección, así que no se «hace crecer» sin falsear el conjunto. Lo que
> sí ocurre, y está en la tarea 12.2, es lo simétrico: el barrido de este change corre sobre las
> 48, de modo que al fijar `ρ` las 40 hoy limpias dejan de serlo **aguas abajo**.

*Razón, y es la que la separa de un ajuste posterior.* Dos propiedades de la partición, ambas
visibles **sin mirar el resultado del barrido**: **6 de 8** consultas están en el techo del
nDCG@5 y **las 8** en el de Recall@5, P@3 y MRR —una lectura saturada no puede mejorar, sólo
empatar o caer—; y **7 de 8 salen de la lista curada de C20/C21**, con 10/10 en la rama léxica
según el informe de C21. La condición veta subir el peso vectorial **con las consultas elegidas
para que la léxica ganase**: el mismo error estructural que C24 diagnosticó en la rúbrica de C21,
reproducido dentro de su propia regla.

Y C24 ya publicó la evidencia: 0,942 en ajuste contra 0,535 en nuevas, que llamó *«la
contaminación del conjunto de ajuste, cuantificada»*. **Una partición contaminada es evidencia de
sobreajuste del titular, no un grupo de control.** Usarla como control es validar un modelo sobre
su conjunto de entrenamiento y rechazar todo cambio que baje el acierto en entrenamiento.

*Alternativa descartada:* eximir *ad hoc* las lecturas en techo. Funciona, pero define
«uninformativo» a medida del caso que estorba; el argumento de contaminación es más fuerte y no
depende del resultado.

### D15 · Tabla de seis filas, y la fusión plana se conserva

| fila | qué aísla |
|---|---|
| `v0-nombre` · `v0-fts` · `v0-cag` · `v1-vectorial` | sin cambios; se re-corren por procedencia |
| `v2-hibrido` | la fusión **plana** viva — línea base publicada |
| **`v2b-fusion`** | la fusión **por rama** con adaptativa, **sin** señales |
| **`v3-senales`** | `v2b` + disponibilidad + rotación |

**Sin `v2b`, un `v3` que mejorase sería inatribuible.** Y la fusión plana se conserva como modo
seleccionable (pregunta abierta 5, opción por defecto): si se sustituye, `v2-hibrido` deja de
reproducir la línea base y la tabla pierde su fila de referencia. Su retirada es el change
posterior `clean-plain-fusion`.

Al profundizar el *pool* se mueve `golden_set_version`, así que **las seis se re-corren**.
`v0-cag` son 12 consultas a $0,002673 = **tres céntimos**, luego se re-corre para que la tabla
comparta una sola procedencia. El barrido **decide** sobre la versión vieja —legítimo: titular y
candidatos se comparan contra los mismos juicios, y `unjudged@5` marca la incomparabilidad— pero
se **publica** sobre la nueva, así que el ganador se **re-confirma**: un punto de rejilla, no la
rejilla.

### D16 · La penalización de variante ambigua se retira, refutada por medición

*Tres hechos.* **(a)** Reparto real de familias (C18a): 44 de dos miembros, 55 de tres, 55 de
cuatro, **una de cinco y una de ocho** — sólo **2 de 156** pueden llenar cinco huecos, y 99 no
llenan ni cuatro; y el operador ve **10** filas, no 5. **(b)** El panel ya pinta
`Talla {variantLabel}` por fila, así que cuatro tallas no aparecen como cuatro filas idénticas;
lo que falta es que **sepa que son hermanas**, y `family_id` no se usa en el panel del operador.
**(c)** Con talla nombrada la rúbrica ya ordena bien —hermana correcta grado 2, las demás grado
1— y `variante-talla` es la **mejor categoría** (0,830); sin talla nombrada las hermanas son
legítimamente grado 2 y **diversificar baja el nDCG@5**.

La presentación **domina estrictamente** al ranking: un hueco de página, todas las tallas
visibles, cero coste de relevancia. Y penalizar convierte un problema de maquetación en **pérdida
de información**, porque si se hunden las hermanas el operador no puede saber que existen.
`groups[]` es el §7.7 del diseño y pertenece a **C30/C36**.

**Condición, para no refutarlo por argumento como ya pasó una vez en este proyecto:** la medición
M3 cuenta hermanas en el top-10 por consulta. Si son muchas, la respuesta **sigue siendo
presentación**, pero `groups[]` sube de prioridad en C30/C36.

### D17 · El binario de `qty_bucket` se conserva, refutado por construcción

`QtyBucket.From(quantity)`: `≤0 → "0"`, `1-2 → "1-2"`, `≥3 → "3+"`. Con `g_efectivo` de D3, los dos
buckets no nulos caen en la misma rama, ninguno pierde grado y **no existe función objetivo que
pueda ordenarlos**. Se suma que la lectura de negocio tiene **signo ambiguo** —«quedan una o dos:
que se venda» y «quedan una o dos: puede que ya no estén» son las dos defendibles en un
mostrador—, y cuando dos lecturas legítimas se cancelan el peso honesto es cero.

Se enseñan en todo caso; el desfase con la caja es un problema de sincronización, no de ranking.
La medición **M4** publica el reparto de `1-2` frente a `3+` para que el MUST heredado pase de
conservado por inercia a **respaldado por una cifra**.

### D18 · Sin cambio de contrato

No se emite señal de familia a `RetrievalResult` (pregunta abierta 6, opción por defecto): el
consumidor (C30/C36) no existe y mover el `openapi.json` congelado sin consumidor es deuda.
`signal_pos_id` es parámetro **interno del orquestador**, nunca campo del cuerpo — no puede llegar
del navegador, y el `pos_id` sigue saliendo del token.

## Risks / Trade-offs

- **La regla adaptativa podía no aportar nada** → Medido con un brazo de control que el barrido
  original no tenía: aporta **+0,128** donde fue diseñada y **cero exacto** en las otras siete
  categorías, y además hace robusta la elección de `rho` (recorrido 0,070 → 0,007). El riesgo
  queda cerrado con cifra en lugar de con argumento.
- **El denominador de la cobertura es el riesgo número uno** → Con el ingenuo, la regla degrada
  las categorías que existe para proteger **y lo hace pareciendo que funciona**, porque el
  agregado global podría subir igual. Mitigación: **M2 antes de implementar**, y el test
  `test_full_coverage_leaves_the_lexical_weight_untouched`, que convierte la predicción en gate.
- **Invertir el orden de las fases** → Fallo silencioso: el barrido de señales corre y da números,
  pero medidos sobre una fusión que ya no es la vigente. Mitigación: la captura registra la
  configuración de fusión con la que se tomó, y el re-puntuado **rechaza** ventanas cuya fusión no
  coincida con la congelada.
- **Reformular la regla de decisión después de que vetara algo** es indistinguible de un ajuste
  *post hoc* si no se escribe antes → Mitigación: D14 está escrita y fechada en este documento,
  **antes** de ejecutar el barrido, y su argumento —saturación y contaminación— es verificable sin
  mirar el resultado.
- **Perder la reproducibilidad de la línea base** si la fusión plana no se conserva → La tabla se
  quedaría sin fila de referencia y el change sin forma de demostrar su propia mejora. Mitigación:
  D15, más `test_flat_fusion_mode_reproduces_the_published_baseline`.
- **El *pooling* nuevo no se puede dimensionar por adelantado** → No se sabe cuánto promoverán
  `v2b` y `v3` hasta cerrar la fase A. Mitigación (pregunta abierta 2, opción por defecto): se
  estima al congelar `v2b`; si pasa de dos horas, se prioriza por categoría, con el precedente del
  tope de C24.
- **La abstención tiene dos lados y sólo uno es fácil** → Subir la tasa sobre fuera-de-dominio es
  trivial bajando el umbral; hacerlo sin callar en las 43 contestables es el trabajo. Mitigación:
  ampliar la categoría a 15-20 y el test `test_abstention_does_not_fire_on_answerable_queries`.
- **`ρ = 1,0` está cerca de una discontinuidad** de la fórmula → Un cambio de `k` o de `depth`
  movería el comportamiento. Mitigación: `k` y `depth` se barren **juntos** con `ρ`, y la rejilla
  cubre la banda con cuatro puntos en lugar de uno.
- **Aplanamiento del consenso intra-léxico** por la etapa 1 → Coste aceptado y declarado; el orden
  se conserva íntegro y sólo se pierde la magnitud.
- **Dependencia dura del entorno** → Sin base levantada, sin la proyección de los 11 POS y sin
  clave de *embeddings* no hay fase 0 ni barrido. C23 se exploró con el contenedor apagado y tuvo
  que corregir cifras después: la tarea 1 es verificar el entorno y **parar** si falla.
- **Zona compartida** con C26 en `retrieval/` y con C38 en el runner → Acotada: C26 construye
  sobre este ranking en vez de modificarlo.

## Migration Plan

No hay migración de datos ni de esquema. El despliegue es de configuración y código:

1. **Fase 0** — las cuatro mediciones (M1-M4), sin tocar código de ranking. M1 decide la fase del
   trabajo de umbral.
2. **Fase A** — fusión por rama con el modo plano conservado; barrido; congelar `v2b`.
3. **Fase B** — capturar ventanas con la fusión congelada.
4. **Fase C** — señales por re-puntuado; congelar `v3`.
5. **Fase D** — abstención, si M1 la situó aquí.
6. **Fase E** — ampliar el golden set, profundizar el *pool*, re-correr las seis filas y
   re-confirmar los ganadores.

**Rollback:** los tres mecanismos nuevos son perillas con valor por defecto. `fusion=flat`
restaura la fusión de C21 exactamente; pesos de negocio a cero restauran el orden anterior a las
señales; el umbral vuelve a 0,65. Ninguna requiere despliegue de código para revertirse, y la
fusión plana sigue en el binario por D15.

## Open Questions

Las seis del ticket quedan **resueltas por su opción por defecto** y reflejadas arriba como
decisión. Lo que queda abierto es lo que sólo una medición puede cerrar:

| # | Abierta | Cuándo se cierra |
|---|---|---|
| 1 | Forma de la regla de abstención: escalar o relativa por consulta | **M1**, primera tarea. Las dos ramas y el criterio están fijados en D11 antes de mirar |
| 2 | Tamaño del *pooling* incremental | Al congelar `v2b` (fin de la fase A) |
| 3 | ¿Qué lectura queda sin contaminar para C26 y C38? | Al cerrar la fase E. **Corregido el 2026-09-11:** la pregunta original —*«cuánto crece la partición de ajuste»*— estaba mal planteada, porque `in_tuning_set` registra un **hecho histórico** (qué consultas calibraron qué) y no una elección, así que no se «hace crecer» sin falsear el conjunto. El problema real es el simétrico y lo **crea este change**: su barrido corre sobre las 48, de modo que al fijar `ρ` las 40 hoy limpias dejan de serlo aguas abajo. Las consultas nuevas de la tarea 12.1 no entran en ningún barrido de este change, así que nacen limpias y se conservan como esa lectura |
| 4 | Adaptativa continua o binaria con `α` | **Cerrada el 2026-09-11 por medición.** La binaria resultó **indistinguible** de la continua en los 16 puntos, así que pierde por coste —un parámetro más para el mismo efecto— y se retira. La pregunta además estaba mal planteada: comparaba dos formas de la misma idea sin preguntar si la idea sirve. El **brazo de control** que faltaba la contesta: **+0,128** en `descripcion-sin-anclaje`, **cero** en las otras siete, y el recorrido del barrido sobre `rho` cae de 0,070 a 0,007 (D7) |
| 5 | ¿Se mueve `ρ` del arranque 0,5/0,5? | Barrido de la fase A bajo la regla de D14 |
| 6 | ¿Se mueve el reparto interno léxico? | **No en este change** (D5). Queda anotado como candidato a barrido futuro, con hipótesis previa |
