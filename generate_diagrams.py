# -*- coding: utf-8 -*-
"""Regenera los dos diagramas de modelo conceptual (Paso 1 y Paso 2) con el
contenido corregido: 7 perspectivas (sin "Habitantes") y los 4 indicadores
vigentes (sin Promedio, sin % Participación renovable s/Demanda, sin
Cantidad Total de Centrales; con Cantidad de Centrales Nuevas).
Cada caja calcula su propia altura según la cantidad de líneas de texto
que tiene, para que el título y la fórmula/función no se superpongan."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Ellipse, FancyArrowPatch

PERSPECTIVAS = [
    ("Provincia", None),
    ("Región", None),
    ("Fuentes de Energía\nRenovable", None),
    ("Tiempo\n(Año, Mes y Estación)", None),
    ("Central", None),
    ("Máquina", None),
    ("Programa / Contrato", None),
]

PERSPECTIVAS_COLS = [
    ("Provincia", "PROVINCIA"),
    ("Región", "REGIÓN"),
    ("Fuentes de Energía\nRenovable", "FUENTE DE ENERGÍA"),
    ("Tiempo\n(Año, Mes y Estación)", "AÑO, MES\n(estación derivada de MES)"),
    ("Central", "CENTRAL,\nCENTRAL DESCRIPCIÓN"),
    ("Máquina", "MAQUINA"),
    ("Programa / Contrato", "Nueva Generación"),
]

INDICADORES_SIMPLE = [
    ("Suma Total de\nEnergía Generada", "SUM", False),
    ("% Variación de la Generación\nentre Años (interanual)", "", True),
    ("% Participación sobre\nel Total Generado", "", True),
    ("Cantidad de\nCentrales Nuevas", "COUNT DISTINCT", True),
]

INDICADORES_FORMULA = [
    ("Suma Total de\nEnergía Generada", "SUM(ENERGÍA GENERADA [GWh])", False),
    ("% Variación de la Generación\nentre Años (interanual)",
     "(SUM año B − SUM año A)\n/ SUM año A × 100", True),
    ("% Participación sobre\nel Total Generado",
     "SUM(grupo) / SUM(total\nde referencia) × 100", True),
    ("Cantidad de\nCentrales Nuevas",
     "COUNT(DISTINCT CENTRAL) cuyo\nprimer año con ENERGÍA > 0\nes el año analizado", True),
]

GRIS_CLARO = "#C9CDD2"
GRIS_BORDE = "#4B5563"
OSCURO = "#1F2937"
BLANCO = "#FFFFFF"

TITLE_LINE_H = 0.30
SUB_LINE_H = 0.23
PAD_TOP = 0.18
PAD_BOTTOM = 0.18
GAP_MID = 0.14
GAP_BOXES = 0.40


def box_height(title, subtext):
    title_lines = title.count("\n") + 1
    h = PAD_TOP + title_lines * TITLE_LINE_H + PAD_BOTTOM
    if subtext:
        sub_lines = subtext.count("\n") + 1
        h += GAP_MID + sub_lines * SUB_LINE_H
    return h


def draw_box(ax, x, y, w, h, title, subtext, facecolor, edgecolor, textcolor,
             fontsize=12.5, subfontsize=10, dashed=False):
    style = "round,pad=0.02,rounding_size=0.02"
    box = FancyBboxPatch((x, y), w, h, boxstyle=style, linewidth=1.6,
                          facecolor=facecolor, edgecolor=edgecolor,
                          linestyle="dashed" if dashed else "solid")
    ax.add_patch(box)

    title_lines = title.count("\n") + 1
    title_block_h = title_lines * TITLE_LINE_H
    title_center_y = y + h - PAD_TOP - title_block_h / 2
    ax.text(x + w / 2, title_center_y, title, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=textcolor, linespacing=1.35)

    if subtext:
        sub_lines = subtext.count("\n") + 1
        sub_block_h = sub_lines * SUB_LINE_H
        sub_top = y + h - PAD_TOP - title_block_h - GAP_MID
        sub_center_y = sub_top - sub_block_h / 2
        ax.text(x + w / 2, sub_center_y, subtext, ha="center", va="center",
                fontsize=subfontsize, color=textcolor, linespacing=1.35)


def draw_diagram(perspectivas, indicadores, title, out_path, total_w=16.5, box_w=3.5):
    persp_heights = [box_height(t, s) for t, s in perspectivas]
    ind_heights = [box_height(t, (s if s else None)) for t, s, _ in indicadores]

    persp_total = sum(persp_heights) + GAP_BOXES * (len(persp_heights) - 1)
    ind_total = sum(ind_heights) + GAP_BOXES * (len(ind_heights) - 1)

    top_margin, bottom_margin, title_margin = 0.5, 0.55, 1.1
    fig_h = max(persp_total, ind_total) + top_margin + bottom_margin + title_margin

    fig, ax = plt.subplots(figsize=(total_w, fig_h))
    ax.set_xlim(0, total_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    ax.set_title(title, fontsize=19, fontweight="bold", pad=18, loc="center")

    left_x = 0.4
    right_x = total_w - 0.4 - box_w
    center_x = total_w / 2

    content_top = fig_h - title_margin
    content_bottom = bottom_margin

    # Perspectivas (izquierda) — centradas verticalmente en el área de contenido
    persp_start_y = content_bottom + (content_top - content_bottom - persp_total) / 2
    y = persp_start_y + persp_total
    persp_centers = []
    for (t, s), h in zip(perspectivas, persp_heights):
        y -= h
        draw_box(ax, left_x, y, box_w, h, t, s, GRIS_CLARO, GRIS_BORDE, OSCURO)
        persp_centers.append((left_x + box_w, y + h / 2))
        y -= GAP_BOXES

    # Indicadores (derecha)
    ind_start_y = content_bottom + (content_top - content_bottom - ind_total) / 2
    y = ind_start_y + ind_total
    ind_centers = []
    for (t, s, derivado), h in zip(indicadores, ind_heights):
        y -= h
        draw_box(ax, right_x, y, box_w, h, t, s if s else None, OSCURO, OSCURO, BLANCO,
                  dashed=derivado)
        ind_centers.append((right_x, y + h / 2))
        y -= GAP_BOXES

    # Óvalo central
    center_y = (content_top + content_bottom) / 2
    oval_w, oval_h = 2.1, 1.35
    oval = Ellipse((center_x, center_y), oval_w, oval_h, facecolor="#EDEEF0",
                    edgecolor=GRIS_BORDE, linewidth=1.8)
    ax.add_patch(oval)
    ax.text(center_x, center_y, "GENERACIÓN\nDE ENERGÍA\nRENOVABLE\nEN EL MEM",
            ha="center", va="center", fontsize=11.5, fontweight="bold", color=OSCURO,
            linespacing=1.25)

    oval_left = center_x - oval_w / 2
    oval_right = center_x + oval_w / 2

    for (px, py) in persp_centers:
        ax.add_patch(FancyArrowPatch((px, py), (oval_left, center_y),
                                      arrowstyle="-|>", mutation_scale=16,
                                      color=GRIS_BORDE, linewidth=1.3,
                                      connectionstyle="arc3,rad=0.0"))
    for (ix, iy) in ind_centers:
        ax.add_patch(FancyArrowPatch((oval_right, center_y), (ix, iy),
                                      arrowstyle="-|>", mutation_scale=16,
                                      color=GRIS_BORDE, linewidth=1.3,
                                      connectionstyle="arc3,rad=0.0"))

    ax.text(total_w - 0.4, 0.15,
            "* indicador derivado (se calcula en la consulta, no se almacena como columna del hecho)",
            ha="right", va="bottom", fontsize=9.5, style="italic", color="#4B5563")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Guardado: {out_path}")


draw_diagram(
    PERSPECTIVAS,
    [(t, s, d) for t, s, d in INDICADORES_SIMPLE],
    "Modelo Conceptual — Generación de Energía Renovable (CAMMESA)",
    "modelo_conceptual_hefesto.png",
    total_w=15.5, box_w=3.2,
)

draw_diagram(
    PERSPECTIVAS_COLS,
    INDICADORES_FORMULA,
    "Modelo Conceptual Ampliado — Generación de Energía Renovable (CAMMESA)",
    "modelo_conceptual_hefesto_v2.png",
    total_w=17.5, box_w=3.9,
)
