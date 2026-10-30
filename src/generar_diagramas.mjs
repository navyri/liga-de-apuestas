#!/usr/bin/env node
/**
 * Genera las exportaciones de diagramas (SVG y PNG) a partir de las fuentes
 * canónicas en Mermaid dentro de los Markdown de la Parte 1.
 *
 * Fuentes canónicas (no editar las exportaciones a mano):
 *   docs/08_diagramas_y_adrs/diagrama_general.md
 *   docs/08_diagramas_y_adrs/diagrama_secuencia_apuesta.md
 *   docs/08_diagramas_y_adrs/topologia_mensajeria.md
 *   docs/08_diagramas_y_adrs/ciclo_carrera.md
 *
 * Salida:
 *   docs/08_diagramas_y_adrs/exportados/<nombre>.svg
 *   docs/08_diagramas_y_adrs/exportados/<nombre>.png
 *
 * Uso:
 *   node src/generar_diagramas.mjs
 *
 * Requisitos (una sola vez):
 *   npm install @mermaid-js/mermaid-cli
 * El tema y el navegador se configuran en src/tema_diagramas.json y
 * src/puppeteer-config.json.
 */

import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const carpetaSrc = dirname(fileURLToPath(import.meta.url));
const raiz = resolve(carpetaSrc, '..');

// Resuelve el binario mmdc instalado localmente (src/node_modules/.bin).
function resolverMmdc() {
  const nombres = process.platform === 'win32' ? ['mmdc.cmd', 'mmdc'] : ['mmdc'];
  const bases = [
    join(carpetaSrc, 'node_modules', '.bin'),
    join(raiz, 'node_modules', '.bin'),
  ];
  for (const base of bases) {
    for (const nombre of nombres) {
      const ruta = join(base, nombre);
      if (existsSync(ruta)) return ruta;
    }
  }
  throw new Error(
    'No se encontró mmdc. Ejecute "npm install" dentro de la carpeta src/ antes de regenerar.'
  );
}
const mmdcBin = resolverMmdc();
const carpetaFuentes = join(raiz, 'docs', '08_diagramas_y_adrs');
const carpetaSalida = join(carpetaFuentes, 'exportados');
const carpetaTmp = join(raiz, 'src', '.tmp_mermaid');

const fuentes = [
  { md: 'diagrama_general.md', nombre: 'diagrama_general' },
  { md: 'diagrama_secuencia_apuesta.md', nombre: 'diagrama_secuencia_apuesta' },
  { md: 'topologia_mensajeria.md', nombre: 'topologia_mensajeria' },
  { md: 'ciclo_carrera.md', nombre: 'ciclo_carrera' },
];

const tema = join(raiz, 'src', 'tema_diagramas.json');
const puppeteerCfg = join(raiz, 'src', 'puppeteer-config.json');

function extraerMermaid(contenido) {
  const bloques = [...contenido.matchAll(/```mermaid\r?\n([\s\S]*?)```/g)];
  if (bloques.length === 0) return null;
  // Se usa el primer bloque Mermaid del documento como diagrama canónico.
  return bloques[0][1];
}

function mmdc(entrada, salida, ancho) {
  const args = [
    '-i', entrada,
    '-o', salida,
    '-c', tema,
    '-p', puppeteerCfg,
    '-b', 'transparent',
    '-w', String(ancho),
    '-s', '2',
  ];
  const opciones = process.platform === 'win32' && mmdcBin.endsWith('.cmd')
    ? { stdio: 'inherit', cwd: raiz, shell: true }
    : { stdio: 'inherit', cwd: raiz };
  execFileSync(mmdcBin, args, opciones);
}

mkdirSync(carpetaSalida, { recursive: true });
mkdirSync(carpetaTmp, { recursive: true });

for (const { md, nombre } of fuentes) {
  const rutaMd = join(carpetaFuentes, md);
  if (!existsSync(rutaMd)) {
    console.error(`[AVISO] No existe la fuente: ${rutaMd}. Se omite.`);
    continue;
  }
  const bloque = extraerMermaid(readFileSync(rutaMd, 'utf8'));
  if (!bloque) {
    console.error(`[AVISO] Sin bloque Mermaid en ${md}. Se omite.`);
    continue;
  }
  const rutaMmd = join(carpetaTmp, `${nombre}.mmd`);
  writeFileSync(rutaMmd, bloque, 'utf8');
  console.log(`\n=== ${nombre} ===`);
  mmdc(rutaMmd, join(carpetaSalida, `${nombre}.svg`), 1600);
  mmdc(rutaMmd, join(carpetaSalida, `${nombre}.png`), 1600);
}

console.log('\nExportaciones generadas en:', carpetaSalida);
