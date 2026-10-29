#!/usr/bin/env python
"""
Genera el documento técnico consolidado de la Parte 1 (HTML intermedio + PDF).

Fuente de verdad: los Markdown temáticos y los ADR de la Parte 1.
Salida:
  herramientas/.tmp_doc_tecnico/documento_tecnico.html   (intermedio, no versionable)
  docs/entregables/documento_tecnico.pdf (entregable)

Uso:
  python herramientas/generar_documento_tecnico.py
  (el PDF se produce con Chrome headless sobre el HTML intermedio)

Nota: no es parte de la plataforma de apuestas; es soporte documental.
"""

import html
import pathlib
import re
import sys

import markdown

RAIZ = pathlib.Path(__file__).resolve().parents[1]
ORIGEN = RAIZ / "docs"
CARPETA_ADR = ORIGEN / "08_diagramas_y_adrs"
EXPORTADOS = CARPETA_ADR / "exportados"
TMP = RAIZ / "herramientas" / ".tmp_doc_tecnico"
SALIDA_HTML = TMP / "documento_tecnico.html"
PDF_ENTREGABLE = ORIGEN / "entregables" / "documento_tecnico.pdf"

DOCS_TEMATICOS = [
    "01_requisitos_y_negocio.md",
    "02_arquitectura_y_componentes.md",
    "03_flujo_critico_y_comunicacion.md",
    "04_mensajeria_y_eventos.md",
    "05_datos_e_idempotencia.md",
    "06_escalabilidad_y_fallos.md",
    "07_seguridad_y_costos.md",
]

ADRS = [
    "ADR-001_estilo_arquitectonico.md",
    "ADR-002_mensajeria.md",
    "ADR-003_consistencia_billetera.md",
]

DIAGRAMAS = [
    "diagrama_general.md",
    "diagrama_secuencia_apuesta.md",
    "topologia_mensajeria.md",
    "ciclo_carrera.md",
]

CSS = """
@page { size: A4; margin: 16mm 15mm 18mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Arial, Helvetica, sans-serif; color: #241016; margin: 0; line-height: 1.5; font-size: 11.5pt; }
.portada { page-break-after: always; break-after: page; padding-top: 42mm; text-align: center; }
.portada .eyebrow { color: #A82336; letter-spacing: 4px; text-transform: uppercase; font-size: 10.5pt; }
.portada h1 { font-size: 30pt; color: #6B0F1A; margin: 10px 0 6px; line-height: 1.15; }
.portada h2 { font-size: 16pt; color: #540B13; font-weight: 600; margin: 0 0 4px; }
.portada .org { font-size: 13pt; color: #8B1E2D; margin-top: 14px; }
.portada .barra { width: 210px; height: 5px; margin: 20px auto; background: linear-gradient(90deg, #6B0F1A, #E8B4B8); }
.portada .meta { margin-top: 30px; font-size: 10.5pt; color: #5C3038; }
.portada .lista { text-align: left; display: inline-block; margin-top: 26px; font-size: 10.5pt; color: #3A1A20; }
.portada .lista li { margin: 3px 0; }
.indice { page-break-after: always; break-after: page; }
h1 { font-size: 17.5pt; color: #6B0F1A; border-left: 7px solid #A82336; padding-left: 12px; margin: 0 0 12px; page-break-after: avoid; break-after: avoid; }
h2 { font-size: 13.5pt; color: #540B13; margin: 20px 0 8px; border-bottom: 2px solid #E8D5D8; padding-bottom: 3px; page-break-after: avoid; break-after: avoid; }
h3 { font-size: 11.8pt; color: #8B1E2D; margin: 14px 0 6px; page-break-after: avoid; break-after: avoid; }
.doc { page-break-before: always; break-before: page; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 14px; font-size: 9.3pt; }
th { background: #6B0F1A; color: #F4ECE4; padding: 6px 8px; text-align: left; border: 1px solid #7C1622; }
td { padding: 5px 8px; border: 1px solid #C9A9AE; vertical-align: top; background: #FBF5F5; }
tr:nth-child(even) td { background: #F4E9EA; }
code { font-family: Consolas, "Courier New", monospace; background: #F2E6E8; padding: 1px 4px; border-radius: 3px; font-size: 0.92em; }
pre { background: #241016; color: #F4ECE4; padding: 10px 12px; border-radius: 6px; overflow-x: auto; font-size: 8.6pt; line-height: 1.35; page-break-inside: avoid; break-inside: avoid; }
pre code { background: none; color: inherit; padding: 0; }
blockquote { border-left: 4px solid #C6A66B; background: #FBF3EE; margin: 10px 0; padding: 8px 14px; color: #4A2028; }
.formula { font-family: Consolas, "Courier New", monospace; background: #F7ECEE; padding: 1px 5px; border-radius: 3px; font-size: 0.95em; }
p.formula { display: block; text-align: center; padding: 8px; margin: 10px 0; font-size: 10.5pt; }
figure { margin: 12px 0 16px; text-align: center; page-break-inside: avoid; break-inside: avoid; }
figure img { max-width: 100%; max-height: 205mm; border: 1px solid #C9A9AE; border-radius: 6px; background: #fff; }
figcaption { font-size: 9pt; color: #6C4048; margin-top: 5px; }
footer.doc { margin-top: 26px; font-size: 8.6pt; color: #8A6068; border-top: 1px solid #E0CBCE; padding-top: 6px; }
"""


def extraer_mermaid(texto: str) -> str | None:
    m = re.search(r"```mermaid\r?\n(.*?)```", texto, re.S)
    return m.group(1) if m else None


def md_a_html(texto: str) -> str:
    # Fórmulas: $$display$$ -> bloque centrado; $inline$ -> span (sin render LaTeX)
    texto = re.sub(r"\$\$(.+?)\$\$", lambda m: f"\n\n<p class='formula'>{m.group(1).strip()}</p>\n\n", texto, flags=re.S)
    texto = re.sub(r"\$([^$\n]+?)\$", lambda m: f"<span class='formula'>{m.group(1)}</span>", texto)
    return markdown.markdown(texto, extensions=["tables", "fenced_code", "sane_lists"])


def titulo_de(texto: str) -> str:
    m = re.search(r"^#\s+(.+)$", texto, re.M)
    return m.group(1).strip() if m else "(sin título)"


def construir() -> pathlib.Path:
    TMP.mkdir(parents=True, exist_ok=True)
    secciones = []  # (titulo, html)
    entradas_indice = []

    def cargar(ruta: pathlib.Path, sangria: str = "") -> str:
        texto = ruta.read_text(encoding="utf-8")
        cuerpo = md_a_html(texto)
        nombre_png = EXPORTADOS / (ruta.stem + ".png")
        if extraer_mermaid(texto) and nombre_png.exists():
            rel = pathlib.Path("..", "..", "docs", "08_diagramas_y_adrs", "exportados", nombre_png.name)
            render = (
                "<figure>"
                f"<img src='{rel.as_posix()}' alt='Render del diagrama {ruta.stem}'>"
                f"<figcaption>Render generado desde la fuente canónica <code>08_diagramas_y_adrs/{ruta.name}</code> "
                "(Mermaid; regenerable con <code>node herramientas/generar_diagramas.mjs</code>).</figcaption>"
                "</figure>"
            )
            cuerpo += "<h2>Render del diagrama</h2>" + render
        return cuerpo

    for nombre in DOCS_TEMATICOS:
        ruta = ORIGEN / nombre
        texto = ruta.read_text(encoding="utf-8")
        titulo = titulo_de(texto)
        entradas_indice.append((titulo, ""))
        secciones.append((titulo, f"<section class='doc'>{cargar(ruta)}</section>"))

    entradas_indice.append(("Registros de Decisión Arquitectónica (ADR)", None))
    for nombre in ADRS:
        ruta = CARPETA_ADR / nombre
        texto = ruta.read_text(encoding="utf-8")
        titulo = titulo_de(texto)
        entradas_indice.append((titulo, "adr"))
        secciones.append((titulo, f"<section class='doc'>{cargar(ruta)}</section>"))

    entradas_indice.append(("Anexo A · Fuentes y renders de los diagramas", None))
    anexo = []
    for nombre in DIAGRAMAS:
        ruta = CARPETA_ADR / nombre
        texto = ruta.read_text(encoding="utf-8")
        titulo = titulo_de(texto)
        entradas_indice.append((titulo, "adr"))
        anexo.append(f"<section class='doc'><h1>{html.escape(titulo)}</h1>{cargar(ruta)}</section>")
    secciones.append(("Anexo A · Fuentes y renders de los diagramas", "".join(anexo)))

    filas_indice = []
    for titulo, sangria in entradas_indice:
        if sangria is None:
            filas_indice.append(f"<li style='list-style:none;margin:10px 0 2px'><b>{html.escape(titulo)}</b></li>")
        else:
            filas_indice.append(f"<li style='margin-left:18px'>{html.escape(titulo)}</li>")

    hoy = "27 de octubre de 2026"
    portada = f"""
<section class="portada">
  <div class="eyebrow">Documento técnico consolidado · Parte 1</div>
  <h1>La Gran Liga de Apuestas de Medianos EIA</h1>
  <div class="barra"></div>
  <h2>Arquitectura de la plataforma de apuestas mutuas (Pari-Mutuel)</h2>
  <div class="org">Salchipapa Maker Racing S.A.S.</div>
  <div class="meta">
    Versión v1.0 · {hoy}<br>
    Consolidado de los artefactos P1-ART-002 a P1-ART-010 y los ADR-001 a ADR-003<br>
    Documento de análisis y diseño — no contiene implementación de la plataforma
  </div>
  <ul class="lista">
    <li>Análisis de negocio, requisitos e invariantes</li>
    <li>Arquitectura y componentes (Decisión 1 y descartes)</li>
    <li>Flujo crítico y comunicaciones síncronas</li>
    <li>Mensajería y eventos con Apache Kafka (Decisión 2)</li>
    <li>Datos, persistencia e idempotencia (Decisión 3)</li>
    <li>Escalabilidad, dimensionamiento y manejo de fallos</li>
    <li>Seguridad, RBAC y gobernanza de costos</li>
    <li>ADR-001, ADR-002 y ADR-003</li>
    <li>Anexo A: fuentes y renders de los cuatro diagramas</li>
  </ul>
</section>
"""

    indice = f"""
<section class="indice">
  <h1>Índice de contenidos</h1>
  <ul style="line-height:1.7">{"".join(filas_indice)}</ul>
</section>
"""

    html_final = (
        "<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>"
        "<title>Documento Técnico — Liga de Apuestas de Medianos EIA (Parte 1)</title>"
        f"<style>{CSS}</style></head><body>"
        + portada
        + indice
        + "".join(seccion for _, seccion in secciones)
        + "</body></html>"
    )
    SALIDA_HTML.write_text(html_final, encoding="utf-8")
    return SALIDA_HTML


if __name__ == "__main__":
    ruta = construir()
    print("HTML intermedio generado:", ruta)
    print("Para el PDF (Chrome headless):")
    print(f'  chrome --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="{PDF_ENTREGABLE}" "{ruta}"')
    sys.exit(0)
