# Figura 1, diagrama de atrición: selección de la cohorte de DiabetIA desde la base SIMF.
#
# Los conteos de los primeros pasos vienen de la extracción (diagrama de elegibilidad del material
# suplementario de Tripp et al., 2023, y sección 2.2 del manuscrito); no se pueden reproducir desde la
# versión tabular. Los dos últimos (137,131 y 136,674) coinciden con process.py. El script verifica que
# cada paso reste exactamente sus exclusiones.
#
# Uso: Rscript diabetia/figure_attrition.R
# Genera results/manuscript/figure_1_attrition.{pdf,png}

suppressPackageStartupMessages({
  library(data.table)
  library(ggplot2)
  library(scales)
})

args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
root <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
figure_dir <- file.path(root, "results", "manuscript")
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

pdf(NULL)  # dispositivo nulo: evita que R cree Rplots.pdf al construir las figuras

# --- Pasos: pacientes que quedan, texto del recuadro y exclusiones ---------------------------
# En el diagrama original, el tercer paso dice 879,891 excluidos, pero sus dos causas suman 915,891,
# que es la diferencia 1,305,390 − 389,499.
steps <- data.table(
  n = c(2255994, 1729070, 1305390, 389499, 341933, 137690, 137131, 136674),
  text = c(
    "patients in the SIMF database",
    "distinct patients",
    "adults",
    "patients with at least one visit\nin a participating unit",
    "patients without\npregnancy-related conditions",
    "patients with at least\ntwo years of follow-up",
    "patients without T2D diagnosed\nbefore 18 years of age",
    "patients in DiabetIA"
  )
)
exclusions <- list(
  list(c("Duplicated patient identifiers", 526924)),
  list(c("Birth date outside 1920–2022", 9108),
       c("Younger than 18 years on 31 December 2018", 414559),
       c("Missing sex", 13)),
  list(c("Fewer than two visits in 2005–2020", 531026),
       c("No visit in the six participating units", 384865)),
  list(c("Pregnancy-related conditions\n(ICD-10 O00–O7A)", 47566)),
  list(c("Less than two years between the\nfirst and the last visit", 204243)),
  list(c("T2D diagnosed before 18 years of age", 559)),
  list(c("No visit in any two-year window", 457))
)
excluded <- sapply(exclusions, function(e) sum(as.numeric(sapply(e, `[`, 2))))
stopifnot(head(steps$n, -1) - excluded == tail(steps$n, -1))

# Texto de cada recuadro de exclusión: total en la primera línea y, si hay varias causas, una por línea.
exclusion_text <- sapply(seq_along(exclusions), function(i) {
  e <- exclusions[[i]]
  if (length(e) == 1) return(e[[1]][1])
  paste(sapply(e, function(r) sprintf("%s: %s", r[1], comma(as.numeric(r[2])))), collapse = "\n")
})

# --- Disposición en milímetros (1 unidad = 1 mm) ------------------------------------------
font <- 2.5                 # tamaño del texto (mm), unos 7 pt
line <- 1.2 * font          # altura de línea
pad <- 2                    # margen vertical dentro de cada recuadro
main_x <- c(0, 62)          # columna principal
excl_x <- c(72, 141)        # columna de exclusiones
gap_min <- 9                # separación mínima entre recuadros principales
n_lines <- function(s) lengths(strsplit(s, "\n", fixed = TRUE))

steps[, label := sprintf("%s %s", comma(n), text)]
# El número va en la primera línea: "2,255,994 patients in..." se parte donde indica el texto.
steps[, height := n_lines(label) * line + 2 * pad]
excl <- data.table(head = sprintf("%s excluded", comma(excluded)), body = exclusion_text)
excl[, height := (1 + n_lines(body)) * line + 2 * pad]

y <- 0
for (i in seq_len(nrow(steps))) {
  steps[i, `:=`(top = y, bottom = y - height)]
  y <- y - steps$height[i]
  if (i <= nrow(excl)) {
    gap <- max(excl$height[i] + 4, gap_min)
    excl[i, `:=`(top = y - (gap - height) / 2, bottom = y - (gap + height) / 2, mid = y - gap / 2)]
    y <- y - gap
  }
}
bottom <- y
centre <- mean(main_x)

arrows_down <- data.table(y = head(steps$bottom, -1), yend = tail(steps$top, -1))
steps[, final := .I == .N]

fig <- ggplot() +
  geom_segment(data = arrows_down, aes(x = centre, xend = centre, y = y, yend = yend),
               colour = "grey40", linewidth = 0.3, arrow = arrow(length = unit(1.4, "mm"), type = "closed")) +
  geom_segment(data = excl, aes(x = centre, xend = excl_x[1], y = mid, yend = mid),
               colour = "grey40", linewidth = 0.3, arrow = arrow(length = unit(1.4, "mm"), type = "closed")) +
  geom_rect(data = steps, aes(xmin = main_x[1], xmax = main_x[2], ymin = bottom, ymax = top, fill = final),
            colour = "grey40", linewidth = 0.3) +
  geom_rect(data = excl, aes(xmin = excl_x[1], xmax = excl_x[2], ymin = bottom, ymax = top),
            fill = "white", colour = "grey40", linewidth = 0.3) +
  geom_text(data = steps, aes(x = centre, y = (top + bottom) / 2, label = label),
            size = font, lineheight = 1.2, colour = "grey10") +
  geom_text(data = excl, aes(x = excl_x[1] + 2.5, y = top - pad, label = head),
            size = font, lineheight = 1.2, hjust = 0, vjust = 1, fontface = "bold", colour = "grey10") +
  geom_text(data = excl, aes(x = excl_x[1] + 2.5, y = top - pad - line, label = body),
            size = font, lineheight = 1.2, hjust = 0, vjust = 1, colour = "grey10") +
  scale_fill_manual(values = c(`FALSE` = "white", `TRUE` = "#D6EEF4"), guide = "none") +
  coord_cartesian(xlim = c(-1, excl_x[2] + 1), ylim = c(bottom - 1, 1), expand = FALSE) +
  theme_void() +
  theme(plot.margin = margin(0, 0, 0, 0))

width <- excl_x[2] + 2
height <- 2 - bottom
for (ext in c("pdf", "png")) {
  out <- file.path(figure_dir, paste0("figure_1_attrition.", ext))
  if (ext == "pdf") {
    ggsave(out, fig, width = width, height = height, units = "mm", device = cairo_pdf)
  } else {
    ggsave(out, fig, width = width, height = height, units = "mm", dpi = 300, bg = "white")
  }
  message("Generado: ", sub(paste0(root, "/"), "", out))
}
