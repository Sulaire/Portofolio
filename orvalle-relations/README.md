# Orvalle — mapa de relaciones

Genera un mapa de relaciones navegable a partir del vault de la wiki. Un solo
archivo HTML, sin dependencias externas: se abre con doble clic, se envía por
correo y funciona desde `file://`.

```bash
python3 tools/build_map.py /ruta/al/orvalle-wiki
#   → map-data.json      los datos
#   → orvalle-map.html   el mapa, 131 KB, autocontenido

python3 tools/lint_relations.py /ruta/al/orvalle-wiki
#   qué falta por decidir en el vault. Sale con código 1 si hay algo.
```

Solo necesita `pyyaml`.

---

## Qué cambia respecto al mapa anterior

**Lee solo el vault.** `wiki_map.py` mezclaba la wiki con la capa de cards en
`/home/claude/project/content`. Desde el freeze las cards no se mantienen y
`Meta/CURRENT_STATE.md` dice que la wiki es la única superficie viva, así que
un generador que las necesita solo puede reproducir su desfase. Este lee
`Articles/**.md` y nada más, lo que además elimina la segunda fuente de verdad
que hacía que `value` y `note` vivieran donde la wiki no podía verlos.

**El layout se precalcula.** El anterior corría una simulación de fuerzas al
abrir: se asentaba en 1538×3138 px dentro de un lienzo de 1260×764, metía el
mundo entero en el 29% del ancho, y **se asentaba en un sitio distinto cada
vez**. Un mapa que se mueve no se puede memorizar. Ahora las coordenadas se
calculan una vez, con semilla fija y número de iteraciones fijo: dos builds del
mismo vault dan coordenadas idénticas byte a byte.

| | antes | ahora |
|---|---|---|
| Zoom inicial | 0.24 | 0.97 |
| Ancho del lienzo usado | 29% | ~95% |
| Proporción del grafo | 1:2 (vertical) | 1.48:1 |
| Cuña del anillo por reino | igual para todos | proporcional a la población |

**Las relaciones son bidireccionales por construcción.** El formato anterior
guardaba `type` más un `reverseType` opcional, lo que privilegiaba
estructuralmente la lectura del `source`. Ahora cada par lleva `aToB` y `bToA`
explícitos y la ficha muestra las dos: `→ aliado` / `← fought beside him`. Lo
no declarado sigue no declarado — reflejar una lectura sobre la otra inventa
una opinión que el personaje no tiene.

**Vocabulario cerrado, prosa conservada.** `kind` elige el color, `label`
guarda la frase que escribiste. `subordinate she cannot remove` es mejor
escritura que `rival`: el mapa muestra las dos cosas.

---

## Los tres ejes de conocimiento

La wiki ya define dos en `Meta/02 - Spoiler and Canon Policy`:

1. **Secretismo** — `Known to:` — quién *dentro del mundo* lo sabe.
2. **Canon** — `[!unresolved]` / `[!draft]` — cómo de asentado está.
3. **Revelación** — qué se le ha mostrado *al lector*. Este faltaba.

El tercero es el que resuelve el problema del spoiler. Y los ejes 1 y 3 son la
misma estructura: *un alcance de conocimiento sobre una afirmación*. Uno tiene
por audiencia a un personaje, el otro al lector.

El mapa implementa el eje 3 con el slider **Revelación**, y su comportamiento
sigue la regla que ya está escrita en la política de spoilers de la wiki:

> *"Si el mundo cree una versión falsa, registra la falsa en la prosa abierta y
> la verdadera en el callout."*

Por eso el mapa **no esconde la relación: la cambia**. En nivel 1 lees lo que
dice la prosa abierta. En nivel 3 se abre la lectura del `[!secret]` con su
lista de conocedores. Ocultar la arista dejaría un hueco visible, y un hueco es
en sí mismo un spoiler.

Ahora mismo se extraen **29 lecturas ocultas en 25 de las 95 relaciones**,
leyendo los `[!secret]` que ya están escritos. No hubo que anotar nada: el
parser asocia cada callout a la entrada de `## Relationships` que lo precede,
que es exactamente como el vault ya lo escribe.

### Cuando quieras control fino

El nivel derivado es el punto de partida honesto, no la respuesta final. Para
fijarlo a mano, `Data/reveals.yaml` en el vault:

```yaml
relations:
  "Vareth|Corian de la Marca": 2
  "Miren|Seravael": 3
```

---

## Cómo se lee el mapa

- **Rueda para acercar.** Lejos ves **reinos**, luego **facciones**, luego
  **personas**. Es la misma jerarquía que ya declara el campo `up:` de cada
  artículo: `Nations > Arvela > The Crown > Vareth`. No hubo que inventar una
  agrupación; estaba escrita.
- **Clic** en alguien abre su ficha y **atenúa el resto por distancia en
  saltos** — vecinos casi enteros, el otro lado del mundo casi ausente. Eso se
  lee como profundidad; atenuar todo por igual se lee como un filtro roto.
- **Arrastra** cualquier nodo para recolocarlo; sus aristas, gradientes y
  etiquetas lo siguen. *Reiniciar* los devuelve a su sitio.
- **Agrupar por reino / facción / pueblo**, con un slider de **separación**.
  A 0 es exactamente el mapa que produjo el build, así que la geografía que
  aprendiste sigue ahí; subiéndolo se exagera el agrupamiento sobre esa misma
  base en vez de recalcular un mapa distinto. Con *pueblo* al 70 la cohesión
  intra-grupo pasa de 0.53 a 0.26.
- **Inicial dentro del disco** porque no hay retratos y un círculo pelado no es
  una cara. **†** los fallecidos, y un glifo propio por cada `state` — `Meta/05`
  pide marca y no color, porque el color ya lleva el reino y recolorear a
  Rukhien costaría lo que más importa de él, que viene *del* Byway.
- **Saltos 1/2/3** acota el grafo a la vecindad del personaje seleccionado.
  Salto 1 = su gente (13 nodos). Salto 2 = su mundo (25). Salto 3 = ya es un
  mapa. Teclas `0`–`3`.
- **Anillo dorado punteado** = ese personaje guarda lecturas ocultas.
- **Línea discontinua** = la relación está declarada por un solo lado.
- **Color del nodo** = reino. **Color de la arista** = sentimiento, con un
  extremo por perspectiva, así que una relación asimétrica se ve asimétrica sin
  abrir nada.
- El estado vive en la URL: cualquier vista se comparte con un enlace.

---

## Legibilidad: el problema de fondo

Seleccionar a Ithanel dibujaba **once** etiquetas de arista a su alrededor,
**seis de ellas «sin declarar»**, superpuestas entre sí y sobre los nombres.
Tres errores distintos, y solo el tercero es de geometría:

1. **Etiquetaba la ausencia.** «Sin declarar» es el 46% de las aristas y no
   informa de nada; la ficha de la derecha ya lo dice, en lista y legible.
   Nunca gastes tinta del lienzo en la falta de un dato.
2. **No tenía presupuesto.** El recurso escaso es el espacio *de pantalla*, no
   los píxeles: una región admite cuatro o cinco etiquetas por mucho que
   quieras decir.
3. **Colocaba a ciegas.** La posición salía de la geometría, sin saber qué
   había ya dibujado ahí.

La solución es la colocación cartográfica de toda la vida — **voraz, con
rechazo**: ordena las candidatas por cuánto informan, ofrécele a cada una
doce posiciones (cuatro distancias por la arista × en la línea y a cada lado),
y quédate con las que caen libres de todo lo ya colocado.

Y tres piezas que lo hacen funcionar de verdad:

- **El texto vive en espacio de pantalla, la geometría en espacio de mundo.**
  Todo estaba dentro de un `<g>` transformado, así que un nombre de 11px se
  dibujaba a 24px con zoom 2.2: las letras crecían tan rápido como los huecos
  entre ellas y acercarse no creaba sitio. Contraescalando las fuentes por
  `1/k` el zoom pasa a ser la **válvula de escape** de la densidad — más lejos
  2 etiquetas, más cerca 5, y son las mismas.
- **Medir el texto, no estimarlo.** `longitud × 5.6` acierta lo bastante como
  para parecer bien al zoom por defecto y fallar justo cuando caben suficientes
  etiquetas para que importe.
- **Callar lo que no se ha preguntado.** Seleccionar a alguien es preguntar por
  *esa persona*: más allá de su propio círculo los nombres no son una
  respuesta, son decorado que hay que leer para atravesar — y cada uno es un
  obstáculo que echa fuera del lienzo a una etiqueta de relación.

Cuando aun así no cabe nada, el mapa **se acerca a la vecindad** en vez de
apretujarlas. La densidad es una razón para mover la cámara, no para rendirse.

Medido sobre 12 selecciones, incluidas las más densas del racimo de Arvela:
**34 etiquetas colocadas, 0 colisiones, 0 selecciones mudas.**

Nada de esto depende del tamaño del grafo: el presupuesto es por pantalla y no
crece con los datos. Es la parte que se lleva tal cual a la Coppermind.

---

## Lo que el linter quiere que decidas

Contra el vault de 2026-09-04:

| | |
|---|---|
| **5** valores fuera de vocabulario | `left him to die`, `future contact`, `his only defeat, unknowingly`, `cited as argument`, `twin` |
| **23** grafías heredadas | `sworn loyalty` vs `sworn-loyalty`, `old friendship`, `brother, mutual contempt`… |
| **1** `relations:` mal formado | `Yurael` lo escribe como lista de enlaces sin tipo |
| **13** destinos sin artículo | `Belarno de Quilmar`, `The Branch`, `A woman at the parley`… |
| **43** relaciones de un solo lado | el 46% del grafo sale «sin declarar» por un extremo |
| **6** secciones en prosa libre | Bastyr, Lartasez, Ponnler, Storm, Talassia, The Faalari Sown |
| **7** `died:` vacíos | Alamna, Baldric, Des Terrao, Don Enfadao, Miedo Miedin, Vareth, Yurael tienen el campo pero a `null`. Tu `Meta/05` dice que rellenarlo es lo que hace muerto a alguien en el mapa, así que salen 4 fallecidos y no 7 |

`--fix-spellings` reescribe las grafías heredadas en el frontmatter. Lo demás
necesita una decisión, que es justo por lo que el linter no la toma.

`vocab.py` tiene una tabla `LEGACY_SPELLINGS` que traduce las 23 grafías. **Es
una ayuda de migración y debería encogerse hasta desaparecer.** Mientras exista,
cada entrada es una regla que mantener en un archivo que no es el artículo.

---

## Por qué el vocabulario se cierra aquí y no en el renderer

El pipeline anterior normalizaba río abajo: `wiki_map.py` tenía una tabla
`SYNONYMS` y un `infer_type()` que casaba subcadenas contra la prosa. El
renderer no puede saber que `subordinate she cannot remove` significa `rival`,
así que adivinaba — y `hatred`, un valor que el vault llevaba semanas usando,
se pintaba gris neutro porque nadie lo había añadido a una segunda tabla en un
segundo archivo.

Cerrarlo en origen cuesta una palabra por artículo y elimina las conjeturas.

---

## Estructura

```
tools/
  vocab.py             vocabularios cerrados y colores. Fuente única.
  build_map.py         vault → map-data.json → orvalle-map.html
  lint_relations.py    qué falta por decidir en el vault
  template.html        el renderer (sin dependencias)
```

Los colores se emiten desde `vocab.py` al construir, no se repiten en el HTML.
Tener dos copias es lo que dejó que se separaran.

---

## Escalar esto a la Coppermind

Lo que aguanta tal cual y lo que no, con 45 personajes frente a ~2000:

**Aguanta.** El modelo de datos (par bidireccional + eje de revelación +
procedencia), la jerarquía de zoom desde el árbol `up:`, el dial de saltos, el
layout precalculado y las facetas de filtro.

**Hay que cambiar.** El renderer es SVG y dibuja cada nodo y cada arista: con
45 va sobrado, sobre unos 1500 elementos hay que pasar a canvas o WebGL
(`sigma.js` + `graphology`, o Cosmograph). El layout es O(n²) por iteración:
con miles de nodos toca ForceAtlas2 en el build. Y los filtros por chips
necesitan selectores de árbol con buscador — con 200 facciones una fila de
chips es inservible.

**Sigue igual de importante.** El presupuesto: **~150 nodos con etiqueta en
pantalla como máximo**. Por encima de eso se agrega, no se dibuja. Esa es una
restricción de diseño, no técnica, y es la que decide si el mapa se lee.
