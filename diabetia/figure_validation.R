# Figura de Technical Validation: distribución de las mediciones y laboratorios de DiabetIA.
#
# Un panel por variable (grid), con el histograma de un valor por paciente: la mediana de su primera
# ventana con valor registrado de esa variable (las ventanas se traslapan un año y los pacientes con
# más ventanas pesarían más), como número de pacientes en cada barra. Un texto en la esquina superior
# derecha da la mediana (P25–P75). Las variables salen de diabetia/limits.csv, igual que la Tabla S2.
#
# Uso: Rscript diabetia/figure_validation.R
# Genera results/manuscript/figure_3_validation.{pdf,png} (Figura 3)
# y results/auxiliary/figure_3_validation_stats.csv

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


limits <- fread(limits_file, encoding = "UTF-8")
limits[, order := .I]

# --- Datos: un valor por paciente, con el mismo filtro de cohorte que process.py ------------
measured <- setdiff(limits$column, "bmi")
columns <- unique(c("cx_curp", "x_start", "careunit", "fn_weight_median", "fn_height_median",
                    paste0(measured, "_median")))
message("Leyendo ", input_file)
df <- fread(input_file, select = columns, na.strings = c("", "NA"), showProgress = TRUE)
df <- df[, if (any(!is.na(careunit))) .SD, by = cx_curp]  # 136,674 pacientes
df[, bmi_median := fn_weight_median / fn_height_median^2]

long <- melt(
  df[, c("cx_curp", "x_start", paste0(limits$column, "_median")), with = FALSE],
  id.vars = c("cx_curp", "x_start"),
  measure.vars = paste0(limits$column, "_median"),
  variable.name = "column", value.name = "value", na.rm = TRUE
)
long[, column := sub("_median$", "", column)]
# Primera ventana con valor de cada variable por paciente: un renglón por paciente y variable.
setorder(long, cx_curp, x_start)
long <- unique(long, by = c("cx_curp", "column"))[, .(column, value)]

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
limits[, label := sprintf("%s\nn = %s", name, comma(n_total))]

# --- Histogramas por variable (ancho de barra propio de cada panel) ------------------------
# Resolución de registro: la menor potencia de 10 de la que son múltiplos al menos el 95% de los
# valores (las medianas de un número par de mediciones pueden tener un decimal más).
resolution <- function(value) {
  for (step in 10^(2:-3)) {
    if (mean(abs(value / step - round(value / step)) < 1e-6) >= 0.95) return(step)
  }
  10^-3
}
bars <- long[, {
  range <- quantile(value, display_quantiles, names = FALSE)
  discrete <- .BY$column %in% c(integer_vars, decimal_vars)
  width <- if (.BY$column %in% integer_vars) 1 else if (discrete) 0.1 else diff(range) / n_bins
  # Continuas: el ancho es múltiplo de la resolución con que se registra la variable (p. ej. 0.01 m
  # de la talla, 0.1 % de la HbA1c), para que cada barra abarque el mismo número de valores posibles
  # y no aparezcan dientes de sierra.
  if (!discrete) {
    step <- resolution(value)
    width <- max(step, round(width / step) * step)
  }
  shown <- value[value >= range[1] & value <= range[2]]
  # Discretas: barra centrada en el valor registrado. Continuas: intervalos [bin, bin + width).
  # El 1e-9 evita que un valor exacto caiga en la barra anterior por error de punto flotante.
  bin <- if (discrete) round(shown / width) * width else floor(shown / width + 1e-9) * width
  counts <- data.table(bin = bin)[, .N, by = bin]
  offset <- if (discrete) width / 2 else 0
  counts[, `:=`(xmin = bin - offset, xmax = bin - offset + width,
                n_hidden = length(value) - length(shown))]
  counts
}, by = column]

panels <- merge(limits, bars[, .(n_hidden = n_hidden[1], x_lo = min(xmin), x_hi = max(xmax), n_max = max(N)),
                             by = column], by = "column")
# Máximo del eje y de cada panel: un número redondo (10,000, 80,000, ...) que deja espacio arriba
# para el texto (45% sobre la barra más alta); el eje termina en una línea de la cuadrícula.
panels[, y_top := max(pretty(c(0, 1.45 * n_max))), by = column]
# Texto con la mediana y el IQR (P25–P75) en todas las variables, en dos renglones: vale para distribuciones sesgadas
# (bioquímicos) y discretas (signos vitales). Sin decimales, salvo las variables de esta lista.
decimals <- c(fn_weight = 1, fn_height = 2, bmi = 1, fn_temperature = 1,
              fn_hemoglobin = 1, fn_creatinine = 2, fn_urea = 1, fn_aurico = 1)
fmt <- function(x, d) formatC(x, format = "f", digits = d, big.mark = ",")
panels[, stats_text := {
  d <- if (column %in% names(decimals)) decimals[[column]] else 0
  sprintf("median = %s\nIQR = (%s–%s)", fmt(median, d), fmt(p25, d), fmt(p75, d))
}, by = column]

levels_order <- limits$label
bars <- merge(bars, limits[, .(column, group, label)], by = "column")
bars[, label := factor(label, levels = levels_order)]
panels[, label := factor(label, levels = levels_order)]
bars[, group := factor(group, levels = names(group_colors))]

# --- Figura -------------------------------------------------------------------------------
# Marcas de x por omisión, salvo en la temperatura (el único panel entre 34 y 39): sin pasos de 0.25,
# para que las etiquetas tengan un decimal (36.0, 36.2, ...) y no se empalmen.
x_breaks <- function(l) {
  if (l[1] > 34 && l[2] < 39) breaks_extended(n = 5, Q = c(1, 5, 2, 4, 3))(l) else breaks_extended()(l)
}
fig <- ggplot() +
  geom_rect(data = bars, aes(xmin = xmin, xmax = xmax, ymin = 0, ymax = N, fill = group),
            colour = "white", linewidth = 0.1) +
  geom_blank(data = panels, aes(x = x_hi, y = y_top)) +
  geom_text(data = panels, aes(x = x_hi, y = y_top, label = stats_text), hjust = 1, vjust = 1.3,
            size = 2.1, lineheight = 1, colour = "grey20") +
  facet_wrap(~label, scales = "free", ncol = 4) +
  scale_fill_manual(values = group_colors, name = NULL) +
  scale_x_continuous(breaks = x_breaks, labels = label_number(big.mark = ",")) +
  scale_y_continuous(labels = label_comma(), breaks = function(l) pretty(c(0, l[2])), expand = c(0, 0)) +
  labs(x = NULL, y = "Patients") +
  theme_minimal(base_size = 8) +
  theme(
    legend.position = "bottom",
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank(),
    panel.grid.major.y = element_line(colour = "grey92", linewidth = 0.3),
    strip.text = element_text(face = "bold", hjust = 0, size = 7, lineheight = 1.1),
    axis.text = element_text(colour = "grey40", size = 6),
    panel.spacing = unit(0.8, "lines"),
    plot.margin = margin(5.5, 10, 5.5, 5.5)  # deja espacio a la última etiqueta del eje x
  )

for (ext in c("pdf", "png")) {
  out <- file.path(figure_dir, paste0("figure_3_validation.", ext))
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
fwrite(summary_table, file.path(auxiliary_dir, "figure_3_validation_stats.csv"))
message("Generado: results/auxiliary/figure_3_validation_stats.csv")
