# Figura 3: trayectoria longitudinal de un paciente de DiabetIA.
#
# Muestra, ventana por ventana, los diagnósticos registrados, el IMC, la presión arterial, la
# glucosa, los medicamentos prescritos y el número de visitas de un solo paciente. Ilustra la
# ventaja principal de la base: seguir a la misma persona durante años en atención primaria.
#
# Privacidad: la figura no muestra el identificador ni fechas de calendario; el eje es el tiempo
# desde el inicio del seguimiento y la edad se reporta en un intervalo de 5 años.
#
# Las complicaciones crónicas de la DM2 (foco del artículo) se resaltan en rojo. La aparición de la DM2
# se marca con una línea vertical en los paneles B–F y la de cada complicación en el panel F (visitas).
#
# Selección del paciente (si no se indica uno): seguimiento largo (≥ 8 ventanas), IMC en ≥ 80% de
# las ventanas, y la mayor puntuación de: complicaciones que aparecen durante el seguimiento, número
# de complicaciones, DM2 diagnosticada durante el seguimiento, número de ventanas, ventanas con
# glucosa y grupos de medicamentos.
#
# Uso:
#   Rscript diabetia/figure_patient.R                  mejor candidato -> results/manuscript/figure_3_patient.{pdf,png}
#   Rscript diabetia/figure_patient.R --top 3          3 mejores -> results/patients/figure_patient_<cx_curp>.{pdf,png}
#                                                      y results/patients/figure_patient_candidates.csv
#   Rscript diabetia/figure_patient.R --profiles       un paciente por perfil clínico (coronario, sin hipertensión,
#                                                      cada complicación, ...) -> results/patients/figure_patient_<perfil>_<cx_curp>
#   Rscript diabetia/figure_patient.R <cx_curp> [...]  pacientes indicados -> results/patients/figure_patient_<cx_curp>.{pdf,png}

suppressPackageStartupMessages({
  library(data.table)
  library(ggplot2)
  library(grid)
})

args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grep("^--file=", args)])
root <- if (length(script)) normalizePath(file.path(dirname(script), "..")) else getwd()
input_file <- file.path(root, "data", "diabetia", "hk_database.csv")
results_dir <- file.path(root, "results")
patients_dir <- file.path(results_dir, "patients")  # ejemplos para elegir; incluyen el cx_curp: no compartir
for (d in c("manuscript", "patients")) dir.create(file.path(results_dir, d), recursive = TRUE, showWarnings = FALSE)

pdf(NULL)  # dispositivo nulo: evita que R cree Rplots.pdf al construir las figuras
chosen <- commandArgs(trailingOnly = TRUE)

# Colores de la Figura 4 (FantasticFox1): antropometría, signos vitales y bioquímicos.
fox <- as.character(wesanderson::wes_palette("FantasticFox1"))
col_anthro <- fox[3]
col_vital <- fox[1]
col_bio <- fox[5]
# Atención (diagnósticos, recetas y visitas): verde azulado de Darjeeling1, validado junto con los tres
# colores anteriores (lightness, croma y separación para daltonismo).
col_care <- as.character(wesanderson::wes_palette("Darjeeling1"))[2]
col_care_dark <- "#00574B"  # mismo tono, más oscuro: extremo de la escala de recetas
col_absent <- "grey92"
col_complication <- col_bio  # rojo: validado frente al verde azulado (también para daltonismo)

# Diagnósticos (las columnas son acumuladas: una vez registrado, el diagnóstico se repite).
complications <- list(
  "Nephropathy (E11.2)" = "type_2_diabetes_mellitus_with_renal_complications",
  "Retinopathy (E11.3)" = "type_2_diabetes_mellitus_with_ophthalmic_complications",
  "Neuropathy (E11.4)" = "type_2_diabetes_mellitus_with_neurological_complications",
  "Peripheral circulatory complications (E11.5)" = "type_2_diabetes_mellitus_with_peripheral_circulatory_complications"
)
comorbidities <- list(
  "Type 2 diabetes (E11)" = "diabetes_mellitus_type_2",
  "Hypertension (I10)" = "essential_(primary)_hypertension",
  "Dyslipidemia (E78)" = "disorders_of_lipoprotein_metabolism_and_other_lipidemias",
  "Heart disease (I20–I25, I50)" = c(
    "angina_pectoris", "acute_myocardial_infarction", "subsequent_myocardial_infarction",
    "certain_complications_present_after_acute_myocardial_infarction",
    "other_acute_ischemic_heart_diseases", "chronic_ischemic_heart_disease", "heart_failure"
  )
)
diagnoses <- c(comorbidities, complications)
drug_labels <- c(
  antivertigious = "Antivertiginous", antiuricosuricos = "Antigout",
  anti_inflammatory_non_steroids = "NSAIDs", antiflamatory_steroids = "Corticosteroids",
  antiulcerous_and_protectors_of_the_gastric_mucosa = "Gastric protectors",
  bronchodilators_and_expectorants = "Bronchodilators", disease_modifiing_drugs = "Disease-modifying drugs",
  lipid_lowering = "Lipid-lowering", oral_electrolytes = "Oral electrolytes",
  ocular_drugs = "Ophthalmic drugs", hormonal = "Hormones", anti_allergic = "Antiallergics",
  drugs_used_in_nephrology = "Nephrology drugs", analgesics_urinary = "Urinary analgesics",
  systemic_and_topical_antifungals = "Antifungals", drugs_used_in_neurology = "Neurology drugs",
  drugs_used_in_psychiatry = "Psychiatric drugs", erectile_dysfunction = "Erectile dysfunction drugs",
  drugs_used_in_hypothyroidism = "Thyroid hormones", drugs_used_in_hyperthyroidism = "Antithyroid drugs",
  complete_nutritional_formulas = "Nutritional formulas", drugs_used_in_breast_cancer = "Breast cancer drugs",
  drugs_used_in_osteoporosis = "Osteoporosis drugs", alpha_blockers = "Alpha blockers"
)
measures <- c("fn_weight", "fn_height", "fn_ta_systolic", "fn_ta_diastolic", "in_glucose", "fn_fasting_glucose")

# --- Datos ----------------------------------------------------------------------------------------
header <- names(fread(input_file, nrows = 0))
drug_cols <- grep("_count$", header, value = TRUE)
drug_cols <- drug_cols[!grepl("^(fn_|in_)", drug_cols) & drug_cols != "count_cx_w"]
measure_cols <- c(paste0(measures, "_median"), paste0(c("fn_ta_systolic", "fn_ta_diastolic", "in_glucose"), c("_min")),
                  paste0(c("fn_ta_systolic", "fn_ta_diastolic", "in_glucose"), c("_max")))
columns <- unique(c("cx_curp", "window", "cs_sex", "birthdate", "careunit", "count_cx_w", "x_start",
                    unlist(diagnoses), measure_cols, drug_cols))
message("Leyendo ", input_file)
df <- fread(input_file, select = intersect(columns, header), na.strings = c("", "NA"), showProgress = TRUE)
df <- df[, if (any(!is.na(careunit))) .SD, by = cx_curp]  # mismo filtro de cohorte que process.py
setorder(df, cx_curp, window)
for (name in names(diagnoses)) set(df, j = name, value = rowSums(df[, diagnoses[[name]], with = FALSE] > 0, na.rm = TRUE) > 0)
df[, bmi := fn_weight_median / fn_height_median^2]
df[, n_drug_groups := rowSums(.SD > 0, na.rm = TRUE), .SDcols = drug_cols]
df[, n_complications := rowSums(.SD), .SDcols = names(complications)]
coronary_cols <- setdiff(comorbidities[["Heart disease (I20–I25, I50)"]], "heart_failure")
df[, coronary := rowSums(.SD > 0, na.rm = TRUE) > 0, .SDcols = coronary_cols]  # I20–I25

# --- Selección de pacientes ------------------------------------------------------------------
# Candidatos ordenados por puntuación; se guarda un resumen para que el equipo elija la figura.
rank_candidates <- function(min_windows = 8, min_bmi_share = 0.8) {
  scores <- df[, .(
    sex = cs_sex[1],
    windows = .N,
    bmi_share = mean(!is.na(bmi)),
    incident_t2d = !`Type 2 diabetes (E11)`[1] & any(`Type 2 diabetes (E11)`),
    complications = max(n_complications),
    incident_complications = max(n_complications) - n_complications[1],
    glucose_windows = sum(!is.na(in_glucose_median)),
    drug_groups = sum(colSums(.SD > 0, na.rm = TRUE) > 0),
    hypertension = any(`Hypertension (I10)`),
    dyslipidemia = any(`Dyslipidemia (E78)`),
    coronary = any(coronary),
    incident_nephropathy = !`Nephropathy (E11.2)`[1] & any(`Nephropathy (E11.2)`),
    incident_retinopathy = !`Retinopathy (E11.3)`[1] & any(`Retinopathy (E11.3)`),
    incident_neuropathy = !`Neuropathy (E11.4)`[1] & any(`Neuropathy (E11.4)`),
    incident_peripheral_circulatory = !`Peripheral circulatory complications (E11.5)`[1] &
      any(`Peripheral circulatory complications (E11.5)`)
  ), by = cx_curp, .SDcols = drug_cols]
  candidates <- scores[windows >= min_windows & bmi_share >= min_bmi_share]
  candidates[, score := 10 * incident_complications + 3 * complications + 5 * incident_t2d + windows +
                glucose_windows + drug_groups / 2]
  setorder(candidates, -score, cx_curp)
  candidates
}

# Perfiles clínicos para elegir ejemplos variados: el mejor candidato de cada perfil, sin repetir pacientes.
# En los perfiles de una complicación, esa es la única complicación crónica del paciente (así no salen
# siempre los mismos pacientes con las cuatro complicaciones).
# Si ningún paciente cumple el perfil con el seguimiento mínimo, se relaja a 5 ventanas e IMC en 60%.
profiles <- list(
  coronary = quote(coronary),
  no_hypertension = quote(!hypertension),
  nephropathy = quote(incident_nephropathy & complications == 1),
  retinopathy = quote(incident_retinopathy & complications == 1),
  neuropathy = quote(incident_neuropathy & complications == 1),
  peripheral_circulatory = quote(incident_peripheral_circulatory & complications == 1),
  multiple_complications = quote(complications >= 3),
  incident_t2d = quote(incident_t2d),
  man = quote(sex == "M")
)
pick_profiles <- function() {
  strict <- rank_candidates()
  relaxed <- rank_candidates(min_windows = 5, min_bmi_share = 0.6)
  picked <- list()
  for (name in names(profiles)) {
    used <- unlist(lapply(picked, `[[`, "cx_curp"))
    best <- strict[eval(profiles[[name]]) & !cx_curp %in% used][1]
    if (is.na(best$cx_curp)) best <- relaxed[eval(profiles[[name]]) & !cx_curp %in% used][1]
    if (is.na(best$cx_curp)) { message("Sin candidatos para el perfil ", name); next }
    picked[[name]] <- cbind(profile = name, best)
  }
  rbindlist(picked)
}

# --- Paneles ----------------------------------------------------------------------------------------
base_theme <- theme_minimal(base_size = 8) +
  theme(panel.grid.minor = element_blank(), panel.grid.major.x = element_line(colour = "grey93", linewidth = 0.3),
        panel.grid.major.y = element_line(colour = "grey93", linewidth = 0.3),
        plot.title = element_text(face = "bold", size = 8, hjust = 0),
        plot.title.position = "plot", axis.text = element_text(colour = "grey35", size = 6.5),
        axis.title.y = element_text(size = 7, colour = "grey25"), legend.position = "none",
        strip.placement = "outside", plot.margin = margin(4, 34, 2, 4))
no_x <- theme(axis.text.x = element_blank(), axis.title.x = element_blank())
# Faceta vacía en los paneles B–F: así todos tienen la columna de etiquetas del panel A y se alinean.
lane <- facet_grid(.blank ~ ., switch = "y")

# --- Figura de un paciente ----------------------------------------------------------------------
draw_patient <- function(id, stem) {
  p <- df[cx_curp == id]
  if (!nrow(p)) stop("No se encontró el paciente ", id)

  # Tiempo: centro de cada ventana de dos años, en años desde el inicio del seguimiento.
  start <- min(as.IDate(p$x_start))
  p[, t := as.numeric(as.IDate(x_start) - start) / 365.25 + 1]
  age0 <- floor(as.numeric(start - as.IDate(p$birthdate[1])) / 365.25)
  age_band <- sprintf("%d–%d", 5 * (age0 %/% 5), 5 * (age0 %/% 5) + 4)
  who <- sprintf("%s aged %s years at the start of follow-up; %d overlapping two-year windows (%.0f years of follow-up).",
                 ifelse(p$cs_sex[1] == "F", "Woman", "Man"), age_band, nrow(p), max(p$t) + 1)
  x_lim <- c(0, max(p$t) + 1)
  p[, .blank := ""]

  # Eje x en años desde el inicio del seguimiento (una marca por año); cada ventana se dibuja en su centro.
  # El panel A numera además las ventanas arriba, para que se lea qué columna es cada ventana de dos años.
  x_scale <- scale_x_continuous(limits = x_lim, breaks = seq(0, ceiling(x_lim[2]), 1), expand = c(0, 0))
  x_scale_windows <- scale_x_continuous(
    limits = x_lim, breaks = seq(0, ceiling(x_lim[2]), 1), expand = c(0, 0),
    sec.axis = dup_axis(breaks = p$t, labels = seq_len(nrow(p)),
                        name = "Two-year window (consecutive windows overlap by one year)"))
  label_last <- function(d, y, label, colour) {
    last <- d[!is.na(get(y))][.N]
    if (!nrow(last)) return(NULL)
    annotate("text", x = max(d$t) + 0.15, y = last[[y]], label = label, hjust = 0, size = 2.3, colour = colour)
  }

  dx <- melt(p[, c("t", names(diagnoses)), with = FALSE], id.vars = "t", variable.name = "diagnosis",
             value.name = "present", variable.factor = FALSE)
  dx <- rbind(dx, p[, .(t, diagnosis = "Obesity (BMI 30 or more)", present = !is.na(bmi) & bmi >= 30)])
  dx[, block := fifelse(diagnosis %in% names(complications), "T2D chronic\ncomplications", "Comorbidities")]
  dx[, block := factor(block, levels = c("Comorbidities", "T2D chronic\ncomplications"))]
  dx[, diagnosis := factor(diagnosis, levels = rev(c(names(comorbidities), "Obesity (BMI 30 or more)", names(complications))))]
  dx[, state := fifelse(!present, "absent", fifelse(block == "Comorbidities", "comorbidity", "complication"))]
  p_dx <- ggplot(dx, aes(x = t, y = diagnosis)) +
    geom_tile(aes(fill = state), width = 0.92, height = 0.75) +
    facet_grid(block ~ ., scales = "free_y", space = "free_y", switch = "y") +
    scale_fill_manual(values = c(absent = col_absent, comorbidity = col_care, complication = col_complication)) +
    x_scale_windows + labs(title = "A. Diagnoses recorded (chronic complications of T2D in red)", y = NULL) +
    base_theme +
    theme(axis.text.x.bottom = element_blank(), axis.title.x.bottom = element_blank(),
          axis.text.x.top = element_text(colour = "grey35", size = 6.5),
          axis.title.x.top = element_text(size = 7, colour = "grey25", margin = margin(b = 3)),
          panel.grid = element_blank(),
          strip.text.y.left = element_text(angle = 0, face = "bold", size = 6.5, hjust = 1,
                                           colour = "grey25"))

  # Aparición de la DM2 y de cada complicación durante el seguimiento (no en la primera ventana).
  onset <- function(col) {
    w <- which(p[[col]])
    if (length(w) && w[1] > 1) p$t[w[1]] else NA_real_
  }
  events <- data.table(label = c("T2D", sub(" \\(.*", "", names(complications))),
                       t = c(onset("Type 2 diabetes (E11)"), sapply(names(complications), onset)),
                       type = c("t2d", rep("complication", length(complications))))[!is.na(t)]
  event_colours <- c(t2d = col_care, complication = col_complication)
  # Líneas de aparición; `types` elige cuáles se dibujan (en B–D solo la DM2, para no saturar los paneles).
  event_lines <- function(with_labels = FALSE, types = c("t2d", "complication")) {
    events <- events[type %in% types,
                     .(label = paste(label, collapse = " + "), type = if (any(type == "complication")) "complication" else "t2d"),
                     by = t]
    if (!nrow(events)) return(NULL)
    layers <- list(geom_vline(data = events, aes(xintercept = t, colour = type), linewidth = 0.4,
                              linetype = "42", inherit.aes = FALSE),
                   scale_colour_manual(values = event_colours, guide = "none"))
    if (with_labels) {
      layers <- c(layers, list(geom_label(data = events, aes(x = t, y = Inf, label = label, colour = type),
                                          vjust = 1.1, hjust = 0.5, size = 2.2, fontface = "bold", fill = "white",
                                          label.size = 0, label.padding = unit(1, "pt"), inherit.aes = FALSE)))
    }
    layers
  }

  p_bmi <- ggplot(p, aes(x = t, y = bmi)) +
    lane +
    event_lines(with_labels = TRUE, types = "t2d") +
    geom_hline(yintercept = c(25, 30), colour = "grey80", linewidth = 0.3, linetype = "22") +
    geom_line(colour = col_anthro, linewidth = 0.6) + geom_point(colour = col_anthro, size = 1.4) +
    scale_y_continuous(expand = expansion(mult = c(0.05, 0.3))) +  # espacio para las etiquetas de aparición
    x_scale + labs(title = "B. Body mass index", y = "kg/m²") + base_theme + no_x

  p_bp <- ggplot(p, aes(x = t)) +
    lane +
    event_lines(types = "t2d") +
    geom_linerange(aes(ymin = fn_ta_systolic_min, ymax = fn_ta_systolic_max), colour = col_vital, alpha = 0.35, linewidth = 1.6) +
    geom_linerange(aes(ymin = fn_ta_diastolic_min, ymax = fn_ta_diastolic_max), colour = col_vital, alpha = 0.35, linewidth = 1.6) +
    geom_line(aes(y = fn_ta_systolic_median), colour = col_vital, linewidth = 0.6) +
    geom_line(aes(y = fn_ta_diastolic_median), colour = col_vital, linewidth = 0.6, linetype = "22") +
    geom_point(aes(y = fn_ta_systolic_median), colour = col_vital, size = 1.4) +
    geom_point(aes(y = fn_ta_diastolic_median), colour = col_vital, size = 1.4) +
    label_last(p, "fn_ta_systolic_median", "Systolic", "grey25") +
    label_last(p, "fn_ta_diastolic_median", "Diastolic", "grey25") +
    x_scale + coord_cartesian(clip = "off") + labs(title = "C. Blood pressure (median and range in each window)", y = "mmHg") + base_theme + no_x

  p_glu <- ggplot(p, aes(x = t)) +
    lane +
    event_lines(types = "t2d") +
    geom_hline(yintercept = c(100, 126), colour = "grey80", linewidth = 0.3, linetype = "22") +
    geom_linerange(aes(ymin = in_glucose_min, ymax = in_glucose_max), colour = col_bio, alpha = 0.35, linewidth = 1.6) +
    geom_line(data = p[!is.na(in_glucose_median)], aes(y = in_glucose_median), colour = col_bio, linewidth = 0.6) +
    geom_point(aes(y = in_glucose_median), colour = col_bio, size = 1.4) +
    geom_point(aes(y = fn_fasting_glucose_median), colour = col_bio, size = 1.6, shape = 21, fill = "white") +
    label_last(p, "in_glucose_median", "Blood glucose", "grey25") +
    label_last(p, "fn_fasting_glucose_median", "Fasting", "grey25") +
    x_scale + coord_cartesian(clip = "off") + labs(title = "D. Glucose (median and range in each window; open circles: fasting glucose)", y = "mg/dL") +
    base_theme + no_x

  drugs <- melt(p[, c("t", drug_cols), with = FALSE], id.vars = "t", variable.name = "drug", value.name = "n")
  drugs[, drug := sub("_count$", "", drug)]
  top <- drugs[, .(total = sum(n, na.rm = TRUE)), by = drug][total > 0][order(-total)][seq_len(min(.N, 8))]$drug
  drugs <- drugs[drug %in% top]
  drugs[, .blank := ""]
  drugs[n == 0, n := NA]
  drugs[, label := fifelse(drug %in% names(drug_labels), drug_labels[drug], tools::toTitleCase(gsub("_", " ", drug)))]
  drugs[, label := factor(label, levels = rev(unique(label[match(top, drug)])))]
  p_drug <- ggplot(drugs, aes(x = t, y = label)) +
    lane +
    geom_tile(aes(fill = n), width = 0.92, height = 0.75) +
    geom_text(aes(label = ifelse(n > 0, round(n), ""), colour = n > max(n, na.rm = TRUE) / 2), size = 2) +
    scale_colour_manual(values = c(`TRUE` = "white", `FALSE` = "grey20"), guide = "none") +
    scale_fill_gradient(low = "#E3F3EF", high = col_care_dark, na.value = col_absent) +
    x_scale + labs(title = "E. Prescriptions per window (most prescribed drug groups)", y = NULL) +
    base_theme + no_x + theme(panel.grid = element_blank())

  p_visits <- ggplot(p, aes(x = t, y = count_cx_w)) +
    lane +
    event_lines() +
    geom_col(fill = col_care, width = 0.6) +
    x_scale + labs(title = "F. Primary care visits per window", y = "Visits",
                   x = "Years since the start of follow-up") +
    base_theme

  # --- Composición: paneles alineados con gtable (incluido en ggplot2) --------------------------------
  plots <- list(p_dx, p_bmi, p_bp, p_glu, p_drug, p_visits)
  # El panel A tiene dos facetas (comorbilidades y complicaciones): una altura por renglón.
  rel_heights <- c(length(comorbidities) + 1, length(complications), 3, 3.5, 3.5, max(2, length(top)), 2)
  grobs <- lapply(plots, ggplotGrob)
  fig <- do.call(rbind, c(grobs, size = "max"))
  panel_rows <- sort(fig$layout$t[grepl("^panel", fig$layout$name)])
  fig$heights[panel_rows] <- unit(rel_heights, "null")
  caption <- textGrob(who, x = unit(0.5, "npc"), hjust = 0.5, gp = gpar(fontsize = 7, col = "grey30"))
  fig <- gtable::gtable_add_rows(fig, unit(14, "pt"), pos = 0)
  fig <- gtable::gtable_add_grob(fig, caption, t = 1, l = 1, r = ncol(fig))

  height <- 230
  for (ext in c("pdf", "png")) {
    out <- file.path(results_dir, paste0(stem, ".", ext))
    if (ext == "pdf") {
      ggsave(out, fig, width = 180, height = height, units = "mm", device = "pdf", encoding = "WinAnsi.enc")
    } else {
      ggsave(out, fig, width = 180, height = height, units = "mm", dpi = 300, bg = "white")
    }
    message("Generado: ", sub(paste0(root, "/"), "", out))
  }
}

# --- Uso -----------------------------------------------------------------------------------------
if (length(chosen) && chosen[1] == "--profiles") {
  candidates <- pick_profiles()
  fwrite(candidates, file.path(patients_dir, "figure_patient_candidates.csv"))
  message("Generado: results/patients/figure_patient_candidates.csv")
  for (i in seq_len(nrow(candidates))) {
    draw_patient(candidates$cx_curp[i], paste0("patients/figure_patient_", candidates$profile[i], "_", candidates$cx_curp[i]))
  }
} else if (length(chosen) && chosen[1] == "--top") {
  n <- if (length(chosen) > 1) as.integer(chosen[2]) else 3L
  candidates <- head(rank_candidates(), n)
  fwrite(candidates, file.path(patients_dir, "figure_patient_candidates.csv"))
  message("Generado: results/patients/figure_patient_candidates.csv")
  for (id in candidates$cx_curp) draw_patient(id, paste0("patients/figure_patient_", id))
} else if (length(chosen)) {
  for (id in chosen) draw_patient(id, paste0("patients/figure_patient_", id))
} else {
  candidates <- rank_candidates()
  message(sprintf(paste("Paciente seleccionado (no se muestra en la figura): %s; %d ventanas, DM2 incidente = %s,",
                        "complicaciones = %d (%d durante el seguimiento)"),
                  candidates$cx_curp[1], candidates$windows[1], candidates$incident_t2d[1],
                  candidates$complications[1], candidates$incident_complications[1]))
  draw_patient(candidates$cx_curp[1], "manuscript/figure_3_patient")
}
