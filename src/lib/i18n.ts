import es from '../content/es.json';
import en from '../content/en.json';
import zh from '../content/zh.json';

export const idiomas = ['es', 'en', 'zh'] as const;
export type Idioma = (typeof idiomas)[number];

/** Los textos de cada idioma. Para editarlos, ve a src/content/<idioma>.json */
export const contenido = { es, en, zh } as const;

/** Cómo se ve cada idioma en el selector de la barra superior. */
export const etiquetasIdioma: Record<Idioma, string> = {
  es: 'ES',
  en: 'EN',
  zh: '中文',
};

/** '/Portofolio' en GitHub Pages, '' si algún día usas un dominio propio. */
const base = import.meta.env.BASE_URL.replace(/\/$/, '');

/** Dirección de la home de un idioma. */
export function inicio(lang: Idioma): string {
  return lang === 'es' ? `${base}/` : `${base}/${lang}/`;
}

/** Enlace a una sección dentro de la página del idioma actual. */
export function seccion(lang: Idioma, id: string): string {
  return `${inicio(lang)}#${id}`;
}

/** Dirección de un archivo de la carpeta public/ (imágenes, CV, favicon...). */
export function recurso(ruta: string): string {
  return `${base}/${ruta.replace(/^\//, '')}`;
}

/**
 * Los textos que empiezan por "TODO:" son los que aún tienes que escribir tú.
 * Se pintan con un recuadro naranja discontinuo para que no se te pase ninguno.
 * En cuanto borras la palabra TODO, el recuadro desaparece.
 */
export function pendiente(texto: unknown): boolean {
  return typeof texto === 'string' && /^\s*TODO/i.test(texto);
}
