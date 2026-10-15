# Random-intercept mixed model per feature: v ~ Disease + (1 | plot), REML (nlme).
# Usage: Rscript lme_runner.R <job_dir>   (X.bin column-major n x p, meta.json)
suppressPackageStartupMessages({ library(nlme); library(jsonlite) })
jd <- commandArgs(trailingOnly = TRUE)[1]
meta <- fromJSON(file.path(jd, "meta.json"))
n <- meta$n; p <- meta$p
con <- file(file.path(jd, "X.bin"), "rb"); X <- matrix(readBin(con, "double", n * p, size = 8), n, p); close(con)
D <- meta$y; g <- factor(meta$g)
out <- matrix(NA_real_, p, 4)
for (j in seq_len(p)) {
  x <- X[, j]; s <- sd(x)
  if (!is.finite(s) || s == 0) next
  d <- data.frame(v = (x - mean(x)) / s, D = D, g = g)
  r <- tryCatch({
    m <- lme(v ~ D, random = ~ 1 | g, data = d, method = "REML", control = lmeControl(returnObject = TRUE, opt = "optim"))
    tt <- summary(m)$tTable
    vc <- as.numeric(VarCorr(m)[, "Variance"])
    c(tt["D", "Value"] * s, tt["D", "p-value"], vc[1] / sum(vc), tt["D", "DF"])
  }, error = function(e) rep(NA_real_, 4))
  out[j, ] <- r
}
write.table(out, file.path(jd, "out.txt"), row.names = FALSE, col.names = FALSE)
