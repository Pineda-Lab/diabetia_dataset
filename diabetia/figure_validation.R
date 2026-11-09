# Figura de Technical Validation: distribución de las mediciones y laboratorios de DiabetIA.
#
# Un panel por variable (grid), con el histograma de la mediana de cada ventana de dos años,
# como % de las ventanas con valor. La línea continua marca la mediana y las punteadas el
# rango intercuartílico (o la media ± DE, ver summary_stat). Las variables salen de
# diabetia/limits.csv, igual que la Tabla S2.
#
# Uso: Rscript diabetia/figure_validation.R
# Genera results/manuscript/figure_validation.{pdf,png} (Figura 3)
# y results/auxiliary/figure_validation_stats.csv

suppressPackageStartupMessages({
  library(data.table)
  library(ggplot2)
  library(scales)
})
if (!requireNamespace("wesanderson", quietly = TRUE)) {
  stop('Falta el paquete wesanderson: install.packages("wesanderson")')
}

args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
root <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
input_file <- file.path(root, "data", "diabetia", "hk_database.csv")
limits_file <- file.path(root, "diabetia", "limits.csv")
results_dir <- file.path(root, "results")
figure_dir <- file.path(results_dir, "manuscript")
auxiliary_dir <- file.path(results_dir, "auxiliary")
for (d in c(figure_dir, auxiliary_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

pdf(NULL)  # dispositivo nulo: evita que R cree Rplots.pdf al construir las figuras

# Un color por grupo de variables: paleta FantasticFox1 de Wes Anderson.
group_colors <- setNames(
  as.character(wesanderson::wes_palette("FantasticFox1"))[c(3, 1, 5)],
  c("Anthropometry", "Vital signs", "Biochemical")
)

# Variables que se registran en enteros (o en décimas): histograma con una barra centrada en
# cada valor, para que se vea la preferencia de dígitos (p. ej. presión arterial en 120/80).
integer_vars <- c("fn_ta_systolic", "fn_ta_diastolic", "in_heart_rate", "in_respiratory_frequency")
decimal_vars <- c("fn_temperature")
n_bins <- 40
display_quantiles <- c(0.005, 0.995)

# Resumen que se marca en cada panel: "median" (mediana y P25–P75, como la Tabla 1)
# o "mean" (media ± DE). La mediana es más fiel en las variables sesgadas (glucosa, TG).
summary_stat <- "median"

limits <- fread(limits_file, encoding = "UTF-8")
limits[, order := .I]

# --- Datos: medianas por ventana, con el mismo filtro de cohorte que process.py ------------
measured <- setdiff(limits$column, "bmi")
columns <- unique(c("cx_curp", "careunit", "fn_weight_median", "fn_height_median", paste0(measured, "_median")))
message("Leyendo ", input_file)
df <- fread(input_file, select = columns, na.strings = c("", "NA"), showProgress = TRUE)
df <- df[, if (any(!is.na(careunit))) .SD, by = cx_curp]  # 136,674 pacientes
df[, bmi_median := fn_weight_median / fn_height_median^2]

long <- melt(
  df[, paste0(limits$column, "_median"), with = FALSE],
  measure.vars = paste0(limits$column, "_median"),
  variable.name = "column", value.name = "value", na.rm = TRUE
)
long[, column := sub("_median$", "", column)]

# --- Resumen por variable (sobre todos los valores, no solo los mostrados) ------------------
stats <- long[, .(
  n_total = .N,
  mean = mean(value), sd = sd(value),
  p25 = quantile(value, 0.25, names = FALSE),
  median = median(value),
  p75 = quantile(value, 0.75, names = FALSE)
), by = column]

limits <- merge(limits, stats, by = "column")
setorder(limits, order)
limits[, label := sprintf("%s\n%s · n = %s", name, unit, comma(n_total))]

# --- Histogramas por variable (ancho de barra propio de cada panel) ------------------------
bars <- long[, {
  range <- quantile(value, display_quantiles, names = FALSE)
  discrete <- .BY$column %in% c(integer_vars, decimal_vars)
  width <- if (.BY$column %in% integer_vars) 1 else if (discrete) 0.1 else diff(range) / n_bins
  shown <- value[value >= range[1] & value <= range[2]]
  # Discretas: barra centrada en el valor registrado. Continuas: intervalos [bin, bin + width).
  bin <- if (discrete) round(shown / width) * width else floor(shown / width) * width
  counts <- data.table(bin = bin)[, .N, by = bin]
  offset <- if (discrete) width / 2 else 0
  counts[, `:=`(xmin = bin - offset, xmax = bin - offset + width, pct = 100 * N / length(value),
                n_hidden = length(value) - length(shown))]
  counts
}, by = column]

panels <- merge(limits, bars[, .(n_hidden = n_hidden[1], x_lo = min(xmin), x_hi = max(xmax)), by = column],
                by = "column")
if (summary_stat == "median") {
  panels[, `:=`(center = median, lo = p25, hi = p75)]
  stat_caption <- "Solid line: median; dashed lines: interquartile range (P25–P75)."
} else {
  panels[, `:=`(center = mean, lo = mean - sd, hi = mean + sd)]
  stat_caption <- "Solid line: mean; dashed lines: mean ± 1 SD."
}
# Las líneas punteadas que caen fuera del intervalo mostrado no se dibujan.
spread <- melt(panels[, .(label, x_lo, x_hi, lo, hi)], measure.vars = c("lo", "hi"), value.name = "x")
spread <- spread[x >= x_lo & x <= x_hi]

levels_order <- limits$label
bars <- merge(bars, limits[, .(column, group, label)], by = "column")
bars[, label := factor(label, levels = levels_order)]
panels[, label := factor(label, levels = levels_order)]
spread[, label := factor(label, levels = levels_order)]
bars[, group := factor(group, levels = names(group_colors))]

# --- Figura -------------------------------------------------------------------------------
fig <- ggplot() +
  geom_rect(data = bars, aes(xmin = xmin, xmax = xmax, ymin = 0, ymax = pct, fill = group),
            colour = "white", linewidth = 0.1) +
  geom_vline(data = spread, aes(xintercept = x), colour = "grey20", linewidth = 0.3, linetype = "22") +
  geom_vline(data = panels, aes(xintercept = center), colour = "grey20", linewidth = 0.45) +
  facet_wrap(~label, scales = "free", ncol = 4) +
  scale_fill_manual(values = group_colors, name = NULL) +
  scale_x_continuous(labels = label_number(big.mark = ",")) +
  scale_y_continuous(labels = function(y) paste0(y, "%"), expand = expansion(mult = c(0, 0.05))) +
  labs(x = NULL, y = "Windows with a recorded value (%)", caption = stat_caption) +
  theme_minimal(base_size = 8) +
  theme(
    legend.position = "bottom",
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank(),
    panel.grid.major.y = element_line(colour = "grey92", linewidth = 0.3),
    strip.text = element_text(face = "bold", hjust = 0, size = 7, lineheight = 1.1),
    axis.text = element_text(colour = "grey40", size = 6),
    plot.caption = element_text(colour = "grey30", size = 6.5, hjust = 0),
    panel.spacing = unit(0.8, "lines"),
    plot.margin = margin(5.5, 10, 5.5, 5.5)  # deja espacio a la última etiqueta del eje x
  )

for (ext in c("pdf", "png")) {
  out <- file.path(figure_dir, paste0("figure_validation.", ext))
  if (ext == "pdf") {
    ggsave(out, fig, width = 180, height = 220, units = "mm", device = "pdf", encoding = "WinAnsi.enc")
  } else {
    ggsave(out, fig, width = 180, height = 220, units = "mm", dpi = 300, bg = "white")
  }
  message("Generado: ", sub(paste0(root, "/"), "", out))
}

# Resumen por variable y valores fuera del intervalo mostrado (percentiles 0.5–99.5),
# para la leyenda de la figura y el texto de Technical Validation.
summary_table <- panels[order(order), .(Variable = name, Unit = unit, n_total, n_hidden,
                                        mean, sd, p25, median, p75)]
fwrite(summary_table, file.path(auxiliary_dir, "figure_validation_stats.csv"))
message("Generado: results/auxiliary/figure_validation_stats.csv")
