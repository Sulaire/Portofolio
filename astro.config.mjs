// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import icon from 'astro-icon';
import { fontProviders } from 'astro/config';

// `site` y `base` son los que hacen que funcione en GitHub Pages.
// Si algún día conectas un dominio propio (ej. jordi.dev), cambia `site`
// por ese dominio y pon `base: '/'`.
export default defineConfig({
  site: 'https://sulaire.github.io',
  base: '/Portofolio',
  trailingSlash: 'ignore',
  // Los iconos son de Phosphor y se incrustan en el HTML al construir:
  // no hay ninguna petición extra ni JavaScript por su culpa.
  integrations: [icon({ include: { ph: ['*'] } })],

  // Astro sirve las tipografías desde el propio sitio y, sobre todo, genera
  // una fuente de reserva con las métricas corregidas. Sin eso, el texto se
  // pinta primero con la tipografía del sistema y al llegar Geist todo salta
  // hacia abajo: es lo que penalizaba la nota de móvil.
  // Las tipografías viven dentro del repo (src/assets/fuentes), no se
  // descargan de ningún CDN. Así el sitio se construye igual aunque no haya
  // red, y ningún tercero ve quién visita la web.
  //
  // Lo importante de dejarlo en manos de Astro: además de servirlas, calcula
  // una fuente de reserva con las métricas corregidas. Sin eso, el texto se
  // pinta con la del sistema y al llegar Geist todo salta hacia abajo.
  fonts: [
    {
      provider: fontProviders.local(),
      name: 'Geist',
      cssVariable: '--fuente-texto',
      fallbacks: ['system-ui', 'sans-serif'],
      options: {
        variants: [
          {
            weight: '100 900',
            style: 'normal',
            src: [
              './src/assets/fuentes/geist-latin.woff2',
              './src/assets/fuentes/geist-latin-ext.woff2',
            ],
          },
        ],
      },
    },
    {
      provider: fontProviders.local(),
      name: 'Geist Mono',
      cssVariable: '--fuente-mono',
      fallbacks: ['ui-monospace', 'monospace'],
      options: {
        variants: [
          { weight: '100 900', style: 'normal', src: ['./src/assets/fuentes/geist-mono-latin.woff2'] },
        ],
      },
    },
  ],
  vite: {
    plugins: [tailwindcss()],
  },
});
