// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import icon from 'astro-icon';

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
  vite: {
    plugins: [tailwindcss()],
  },
});
