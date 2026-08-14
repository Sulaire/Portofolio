// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// `site` y `base` son los que hacen que funcione en GitHub Pages.
// Si algún día conectas un dominio propio (ej. jordi.dev), cambia `site`
// por ese dominio y pon `base: '/'`.
export default defineConfig({
  site: 'https://sulaire.github.io',
  base: '/Portofolio',
  trailingSlash: 'ignore',
  vite: {
    plugins: [tailwindcss()],
  },
});
