# Figura de Technical Validation: cobertura temporal de DiabetIA.
#
# Mapa de calor del % de ventanas con visita que tienen cada variable, por año de inicio de la
# ventana (x_start). El renglón superior muestra cuántas ventanas con visita hay en cada año.
# Lee results/auxiliary/temporal_coverage.csv (generado por diabetia/temporal.py); no vuelve a leer la base.
#
# Uso: Rscript diabetia/figure_temporal.R
# Genera results/supplementary/figure_temporal.{pdf,png} (Figura Suplementaria S1)

suppressPackageStartupMessages({
  library(data.table)
  library(ggplot2)
  library(scales)
})

args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
root <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
results_dir <- file.path(root, "results")
input_file <- file.path(results_dir, "auxiliary", "temporal_coverage.csv")
figure_dir <- file.path(results_dir, "supplementary")
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)
if (!file.exists(input_file)) stop("Falta ", input_file, ": corre antes python3 diabetia/temporal.py")
pdf(NULL)  # dispositivo nulo: evita que R cree Rplots.pdf al construir las figuras

coverage <- fread(input_file, encoding = "UTF-8")
coverage <- coverage[group != "Demographics"]  # sexo y edad están completos en todas las ventanas
groups <- c("Windows", unique(coverage$group))
var_levels <- unique(coverage$variable)

# Escala secuencial de un solo tono: azul de la paleta FantasticFox1 de Wes Anderson (#46ACC8),
# de casi blanco a una versión oscura del mismo tono para que el texto blanco se lea en las celdas altas.
low_color <- "#F1F8FA"
mid_color <- as.character(wesanderson::wes_palette("FantasticFox1"))[3]  # #46ACC8
high_color <- "#1B5E78"

cells <- coverage[, .(year, group, variable, pct)]
counts <- unique(coverage[, .(year, windows_with_visit)])
counts[, `:=`(group = "Windows", variable = "Windows with a visit (×1,000)")]

cells[, `:=`(group = factor(group, levels = groups), variable = factor(variable, levels = rev(var_levels)))]
counts[, group := factor(group, levels = groups)]

fig <- ggplot() +
  geom_tile(data = cells, aes(x = year, y = variable, fill = pct), colour = "white", linewidth = 0.4) +
  geom_text(data = cells, aes(x = year, y = variable, label = round(pct),
                              colour = pct > 60), size = 1.9, show.legend = FALSE) +
  geom_text(data = counts, aes(x = year, y = variable, label = round(windows_with_visit / 1000)),
            size = 2, colour = "grey20") +
  facet_grid(group ~ ., scales = "free_y", space = "free_y", switch = "y") +
  scale_fill_gradientn(colours = c(low_color, mid_color, high_color), values = c(0, 0.55, 1), limits = c(0, 100),
                       name = "Windows with a value (%)", labels = function(x) paste0(x, "%")) +
  scale_colour_manual(values = c(`FALSE` = "grey20", `TRUE` = "white")) +
  scale_x_continuous(breaks = sort(unique(coverage$year)), expand = c(0, 0)) +
  labs(x = "Year of window start", y = NULL) +
  theme_minimal(base_size = 8) +
  theme(
    panel.grid = element_blank(),
    strip.placement = "outside",
    strip.text.y.left = element_text(angle = 0, face = "bold", hjust = 1, size = 7),
    axis.text.x = element_text(angle = 90, vjust = 0.5, colour = "grey40", size = 6),
    axis.text.y = element_text(colour = "grey20", size = 6.5),
    legend.position = "bottom",
    legend.key.width = unit(1.2, "cm"),
    legend.key.height = unit(0.25, "cm"),
    legend.title = element_text(vjust = 0.9),
    panel.spacing = unit(0.3, "lines")
  )

height <- 40 + 5 * length(var_levels)
for (ext in c("pdf", "png")) {
  out <- file.path(figure_dir, paste0("figure_temporal.", ext))
  if (ext == "pdf") {
    ggsave(out, fig, width = 180, height = height, units = "mm", device = "pdf", encoding = "WinAnsi.enc")
  } else {
    ggsave(out, fig, width = 180, height = height, units = "mm", dpi = 300, bg = "white")
  }
  message("Generado: ", sub(paste0(root, "/"), "", out))
}
