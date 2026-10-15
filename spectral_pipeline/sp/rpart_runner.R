# Fits rpart classification trees for a batch of jobs written by sp/cart.py.
# Usage: Rscript rpart_runner.R <job_dir>
suppressPackageStartupMessages({ library(rpart); library(jsonlite) })

args <- commandArgs(trailingOnly = TRUE)
jd <- args[1]
meta <- fromJSON(file.path(jd, "meta.json"), simplifyVector = TRUE)
n <- meta$n; p <- meta$p
con <- file(file.path(jd, "X.bin"), "rb")
X <- matrix(readBin(con, "double", n * p, size = 8), nrow = n, ncol = p)
close(con)
vn <- paste0("f", seq_len(p))
colnames(X) <- vn
yf <- factor(ifelse(meta$y == 1, "D", "H"), levels = c("H", "D"))
s <- meta$settings
ctrl0 <- rpart.control(minsplit = s$minsplit, minbucket = s$minbucket, cp = s$cp,
                       maxcompete = s$maxcompete, maxsurrogate = s$maxsurrogate,
                       xval = 0)

vars_in_order <- function(fit) {
  fr <- fit$frame
  nodes <- as.integer(rownames(fr))
  v <- as.character(fr$var)
  o <- order(nodes)
  v <- v[o]; v <- v[v != "<leaf>"]
  unique(v)
}

frame_table <- function(fit, df) {
  fr <- fit$frame
  nodes <- as.integer(rownames(fr))
  lab <- labels(fit, minlength = 0)
  depth <- floor(log2(nodes))
  yp <- fr$yval2
  ncls <- ncol(yp)
  data.frame(node = nodes, depth = depth, var = as.character(fr$var),
             n = fr$n, nH = yp[, 2], nD = yp[, 3],
             pred = ifelse(fr$yval == 1, "H", "D"), label = lab,
             stringsAsFactors = FALSE)
}

jobs <- fromJSON(file.path(jd, "jobs.json"), simplifyVector = FALSE)
iv <- function(x) as.integer(unlist(x))
out <- vector("list", length(jobs))
for (j in seq_along(out)) {
  job <- jobs[[j]]
  tr <- iv(job$train)
  te <- iv(job$test)
  full <- isTRUE(job$full)
  cols <- iv(job$cols)
  if (length(cols) == 0) cols <- seq_len(p)
  df <- data.frame(cls = yf[tr], X[tr, cols, drop = FALSE])
  ctrl <- ctrl0
  if (full) {
    xv <- iv(job$xval)
    # a vector = plot-grouped fold assignment of the training rows
    ctrl$xval <- if (length(xv) == length(tr)) as.integer(xv) else s$xval_folds
  }
  set.seed(1)
  fit <- rpart(cls ~ ., data = df, method = "class",
               parms = list(prior = s$prior, split = s$split), control = ctrl)
  res <- list(vars = vars_in_order(fit))
  if (length(te) > 0) {
    nd <- as.data.frame(X[te, cols, drop = FALSE])
    pr <- predict(fit, nd, type = "prob")
    res$prob <- as.numeric(pr[, "D"])
    res$pred <- as.integer(predict(fit, nd, type = "class") == "D")
  }
  if (full) {
    res$frame <- frame_table(fit, df)
    cpt <- fit$cptable
    res$cptable <- as.data.frame(cpt)
    if ("xerror" %in% colnames(cpt)) {
      i_min <- which.min(cpt[, "xerror"])
      lim <- cpt[i_min, "xerror"] + cpt[i_min, "xstd"]
      i_1se <- min(which(cpt[, "xerror"] <= lim))
      pf <- prune(fit, cp = cpt[i_1se, "CP"] + 1e-12)
      res$vars_1se <- vars_in_order(pf)
      res$nsplit_1se <- cpt[i_1se, "nsplit"]
      res$frame_1se <- frame_table(pf, df)
    }
    res$prob_train <- as.numeric(predict(fit, df, type = "prob")[, "D"])
  }
  out[[j]] <- res
}
writeLines(toJSON(out, auto_unbox = TRUE, digits = NA, null = "null"),
           file.path(jd, "result.json"))
