# Figura Suplementaria S1: diseño de las ventanas de DiabetIA.
#
# Esquema (sin datos de pacientes) de las ventanas sucesivas de un paciente: dos años de seguimiento
# (x_start–x_end), en los que se resumen diagnósticos, mediciones, recetas y visitas, y el año siguiente de
# desenlace (y_start–y_end), en el que se registran los diagnósticos de DM2 (E11, E11.0–E11.9). Las ventanas
# empiezan con un año de diferencia, así que dos ventanas consecutivas se traslapan un año.
#
# Uso: Rscript diabetia/figure_windows.R
# Genera results/supplementary/figure_windows.{pdf,png}

suppressPackageStartupMessages({
  library(data.table)
  library(ggplot2)
})

args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
root <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
figure_dir <- file.path(root, "results", "supplementary")
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)
pdf(NULL)  # dispositivo nulo: evita que R cree Rplots.pdf al construir las figuras

# Colores: mismos tonos que las figuras del artículo (azul oscuro de la Figura Suplementaria S2 y naranja de
# la paleta FantasticFox1).
follow_col <- "#1B5E78"
outcome_col <- as.character(wesanderson::wes_palette("FantasticFox1"))[1]
ink <- "grey15"

n_windows <- 4
windows <- rbindlist(lapply(seq_len(n_windows), function(k) data.table(
  window = k,
  part = c("Follow-up period (2 years): x_start to x_end", "Outcome period (1 year): y_start to y_end"),
  start = c(k - 1, k + 1), end = c(k + 1, k + 2))))
windows[, part := factor(part, levels = unique(part))]
windows[, label := fifelse(grepl("^Follow", part), paste("Window", window), "")]

fig <- ggplot(windows) +
  geom_rect(aes(xmin = start + 0.03, xmax = end - 0.03, ymin = -window - 0.34, ymax = -window + 0.34, fill = part)) +
  geom_text(aes(x = (start + end) / 2, y = -window, label = label), size = 2.6, colour = "white", fontface = "bold") +
  # Traslape entre las ventanas 1 y 2.
  annotate("segment", x = 1, xend = 2, y = -1.55, yend = -1.55, colour = ink, linewidth = 0.3,
           arrow = arrow(ends = "both", length = unit(2, "pt"))) +
  annotate("text", x = 1.5, y = -1.55, label = "1-year overlap", vjust = -0.5, size = 2.3, colour = ink) +
  annotate("text", x = n_windows + 2.25, y = -(n_windows + 1) / 2, hjust = 0, size = 2.5, colour = ink,
           lineheight = 1.15,
           label = paste("Each row of the tabular release is one window.",
                         "Follow-up: diagnoses (ICD-10), measurements,",
                         "laboratory results, prescriptions and visits,",
                         "summarized by mean, median, minimum, maximum,",
                         "count, standard deviation and slope.",
                         "Outcome: T2D diagnoses (E11, E11.0–E11.9)",
                         "recorded in the following year.",
                         "Successive windows start one year apart.", sep = "\n")) +
  scale_fill_manual(values = setNames(c(follow_col, outcome_col), levels(windows$part)), name = NULL) +
  scale_x_continuous(breaks = 0:(n_windows + 1) + 0.5, labels = paste("Year", 1:(n_windows + 2)),
                     limits = c(0, n_windows + 6.6), expand = expansion(0)) +
  scale_y_continuous(expand = expansion(add = 0.3)) +
  labs(x = NULL, y = NULL) +
  theme_minimal(base_size = 8) +
  theme(panel.grid = element_blank(), axis.text.y = element_blank(),
        axis.text.x = element_text(colour = "grey35", size = 6.5),
        legend.position = "bottom", legend.justification = "left",
        legend.text = element_text(size = 7, colour = ink), legend.key.size = unit(8, "pt"),
        plot.margin = margin(6, 6, 6, 6))

for (ext in c("pdf", "png")) {
  out <- file.path(figure_dir, paste0("figure_windows.", ext))
  if (ext == "pdf") {
    ggsave(out, fig, width = 180, height = 70, units = "mm", device = "pdf", encoding = "WinAnsi.enc")
  } else {
    ggsave(out, fig, width = 180, height = 70, units = "mm", dpi = 300, bg = "white")
  }
  message("Generado: ", sub(paste0(root, "/"), "", out))
}
