# Portfolio

Web de portfolio en tres idiomas (español, inglés y chino) para captar clientes freelance.
Hecha con [Astro](https://astro.build) y publicada gratis en GitHub Pages.

---

## Lo único que necesitas saber para editarla

**Todos los textos de la web están en tres archivos.** No hace falta tocar nada más:

| Archivo | Idioma |
| --- | --- |
| `src/content/es.json` | Español |
| `src/content/en.json` | Inglés |
| `src/content/zh.json` | Chino |

Son archivos de texto. Abres uno, buscas la frase que quieres cambiar entre comillas, la
reescribes, guardas, y en un par de minutos la web se actualiza sola.

### Las reglas del formato (importantes)

1. **Cambia solo lo que está a la derecha de los dos puntos, entre comillas.**
   `"titulo": "Cambia esto"` → lo de la izquierda (`titulo`) es la etiqueta, no la toques.
2. **No borres las comillas ni las comas.** Si al final de una línea hay una coma, déjala.
3. **Si tu texto lleva comillas dobles**, escríbelas así: `\"` (con la barra delante).
4. Los tres archivos tienen exactamente la misma estructura. Si añades un proyecto a uno,
   añádelo también a los otros dos.

Si algo se rompe, el sitio te avisará al construirlo y siempre puedes deshacer el cambio.

---

## Lo que tienes que rellenar

Busca en los archivos la palabra **`TODO`**. Cada `TODO` es un hueco que solo puedes
rellenar tú. Mientras estén sin rellenar **se ven en la web dentro de un recuadro naranja
discontinuo**, para que no se te escape ninguno. En cuanto borras la palabra `TODO` y
escribes tu texto, el recuadro desaparece solo.

Lo que falta ahora mismo:

- [ ] **AVPINOX**: problema, solución y resultado. Comprueba también que la dirección web
      (`enlace`) sea la correcta.
- [ ] **Tu segunda web**: nombre, resumen, problema, solución, resultado y enlace.
- [ ] **Gestor de facturas**: el resultado (horas ahorradas por trimestre, facturas
      gestionadas... cualquier número real).
- [ ] **Sobre mí**: dos o tres frases tuyas.
- [ ] Tu nombre, si no es "Jordi" (aparece en `src/components/Nav.astro` y
      `src/components/Footer.astro`).

### Consejo para escribir los proyectos

La parte que te consigue clientes es **el resultado**, y los resultados se cuentan con
números. Compara:

> ❌ "Automaticé la gestión de facturas con n8n."
>
> ✅ "Eliminé unas 6 horas de trabajo manual cada trimestre y desde entonces no se ha
> retrasado ni un envío a la gestoría."

No necesitas datos exactos ni auditados. Una estimación honesta ("unas 6 horas") vale
muchísimo más que una descripción técnica sin cifras.

---

## Ver la web en tu ordenador

Necesitas [Node.js](https://nodejs.org) instalado (versión 20 o superior). Después, en una
terminal dentro de esta carpeta:

```bash
npm install     # solo la primera vez
npm run dev     # arranca la web en http://localhost:4321
```

Mientras `npm run dev` está funcionando, cada vez que guardes un cambio en un archivo lo
verás reflejado en el navegador al instante.

Para parar el servidor: `Ctrl + C`.

---

## Publicarla

Cada vez que subes cambios a la rama `main`, GitHub construye y publica la web
automáticamente (lo hace el archivo `.github/workflows/deploy.yml`).

**Configuración inicial, una sola vez:**

1. En GitHub, ve a `Settings` → `Pages`.
2. En **Source**, elige **GitHub Actions**.
3. Listo. La web quedará en `https://sulaire.github.io/Portofolio/`.

### Si más adelante compras un dominio propio

Vale mucho la pena para vender servicios: `tunombre.com` da bastante más confianza que
una dirección de github.io.

1. En `astro.config.mjs`, cambia `site` por tu dominio y pon `base: '/'`.
2. Crea un archivo `public/CNAME` cuyo contenido sea solo tu dominio (`tunombre.com`).
3. En GitHub, `Settings` → `Pages` → **Custom domain**, escribe el dominio.

---

## Conectar el formulario de contacto a n8n

Ahora mismo el formulario funciona sin configurar nada: si no hay webhook, abre el correo
del visitante con el mensaje ya escrito. Pero conectarlo a n8n es mejor por dos motivos:
recibes los mensajes de forma fiable, y **puedes decir en una reunión que el formulario de
tu propia web corre en n8n**, que es justo lo que vendes.

**En n8n:**

1. Crea un flujo nuevo con un nodo **Webhook** (método `POST`).
2. Añade detrás lo que quieras: enviarte un email, guardar en Google Sheets, avisarte por
   Telegram...
3. Activa el flujo y copia la **Production URL** del webhook.
4. En el nodo Webhook, en *Response*, deja que responda inmediatamente (código 200).

El formulario envía un JSON con estos campos:

```json
{
  "nombre": "...",
  "email": "...",
  "mensaje": "...",
  "idioma": "es",
  "origen": "https://...",
  "fecha": "2026-08-14T22:00:00.000Z"
}
```

**En tu ordenador**, para probarlo: copia `.env.example` a `.env` y pega la URL:

```
PUBLIC_N8N_WEBHOOK_URL=https://tu-n8n.com/webhook/contacto
```

**En GitHub**, para que funcione en la web publicada:
`Settings` → `Secrets and variables` → `Actions` → pestaña **Variables** → `New variable`

- Nombre: `PUBLIC_N8N_WEBHOOK_URL`
- Valor: la URL del webhook

> Ojo: esta URL acaba siendo visible en el código de la página (es inevitable en una web
> estática). Por eso va como *variable* y no como *secret*. Para evitar sustos, en n8n
> valida los datos que llegan y no dejes ese webhook haciendo nada peligroso: que solo
> reciba mensajes de contacto.

El formulario ya lleva una **trampa antispam** invisible: un campo oculto que los robots
rellenan y las personas no. Si llega relleno, el mensaje se descarta sin avisar al bot.

---

## Cambiar el aspecto

Todos los colores están en un solo sitio: `src/styles/global.css`, arriba del todo.
Si cambias `--color-acento` (ahora naranja `#ff7a45`), cambian a la vez los botones,
enlaces, iconos y detalles de toda la web.

---

## Cómo está organizado

```
src/
├── content/          ← LOS TEXTOS. Es lo único que necesitas tocar.
│   ├── es.json
│   ├── en.json
│   └── zh.json
├── components/       ← Cada bloque de la página
│   ├── Nav.astro         (barra superior y selector de idioma)
│   ├── Hero.astro        (la portada)
│   ├── Servicios.astro
│   ├── Proyectos.astro
│   ├── SobreMi.astro
│   ├── Contacto.astro    (formulario + conexión con n8n)
│   └── Footer.astro
├── layouts/Base.astro    (estructura común: título, SEO, idiomas)
├── lib/i18n.ts           (carga los textos del idioma correcto)
├── styles/global.css     ← LOS COLORES
└── pages/                (una página por idioma)
```

---

## Siguientes pasos, cuando tengas tiempo

En orden de lo que más te va a servir:

1. Rellenar todos los `TODO` con datos reales, sobre todo los resultados con números.
2. Conectar el formulario a n8n.
3. Añadir capturas de pantalla de AVPINOX y de tu segunda web (las imágenes van en
   `public/` y se referencian desde el JSON).
4. Comprar un dominio propio.
5. Añadir un testimonio del cliente de AVPINOX, aunque sean dos frases por WhatsApp. Es
   lo que más convence a un cliente nuevo.
