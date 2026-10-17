import pickle, json, numpy as np
R = pickle.load(open("results/results.pkl", "rb"))
wl = R["wl"]
def m(d): return {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in d.items()}
fl = R["flags"]
out = dict(
    analysis=R["analysis_set"],
    removed=fl.loc[~fl.kept_for_analysis, ["class", "endmember_no", "NDVI", "SR_800_670", "NDWI", "remove_reason"]].round(3).to_dict("records"),
    neg_spectra={c: int(((fl["class"] == c) & (fl.n_negative_bands > 0)).sum()) for c in ("healthy", "diseased")},
    tier1_regions=R["tier1_regions"].to_dict("records"),
    tier1=dict(n=int(len(R["tier1"])), sig=int(R["sig"].sum()), fdr=int((R["tier1"].FDR_q_BH < 0.05).sum()),
               bonf=int((R["tier1"].Bonferroni_p < 0.05).sum()), large_d=int((R["tier1"].Cohen_d_D_minus_H.abs() >= 0.8).sum()),
               max_abs_d=float(R["tier1"].Cohen_d_D_minus_H.abs().max()),
               maxF=float(R["tier1"].F.max()), maxF_wl=float(wl[R["tier1"].F.idxmax()])),
    cart=R["cart_summary"], cart_imp=R["treeA_importance"][["wavelength_nm", "importance_pct"]].round(2).to_dict("records"),
    cp=R["cp_table"].round(4).to_dict("records"),
    tier3=R["tier3"], jm_cum=R["jm_cumulative"][["n_bands", "added_band_nm", "JM_0to2"]].round(4).to_dict("records"),
    jm_band_max=dict(wl=float(R["jm_band"].wavelength_nm[R["jm_band"].JM_0to2.idxmax()]), jm=float(R["jm_band"].JM_0to2.max())),
    qda=dict(m(R["qda"]["metrics"]), rep_mean=float(R["qda"]["rep_acc"].mean()), rep_sd=float(R["qda"]["rep_acc"].std(ddof=1)),
             fold=R["qda"]["fold_acc_rep1"].tolist()),
    rf={k: dict(m(v["metrics"]), oob=float(v["oob"]), n_bands=v["n_bands"]) for k, v in R["rf"].items()},
    rf_top=R["rf_importance"].nlargest(10, "MDI_importance").round(4).to_dict("records"),
    nested={k: m(v) for k, v in R["nested"].items() if k in ("qda", "rf_sel", "rf_all")},
    nested_freq=R["nested"]["band_frequency"].head(8).to_dict(), nested_nb=R["nested"]["n_bands_per_fold"],
    spatial={k: m(v) for k, v in R["spatial"].items() if k in ("qda", "rf_sel", "rf_all")},
    spatial_folds=R["spatial"]["per_fold"],
    location=R["location_control"].to_dict("records"),
    perm=dict(n=R["permutation"]["n"], observed=float(R["permutation"]["observed"]), p=float(R["permutation"]["p"]),
              null_mean=float(R["permutation"]["acc"].mean()), null_max=float(R["permutation"]["acc"].max())),
    sens=R["sensitivity"].to_dict("records"),
    checks=R["checks"].to_dict("records"),
)
json.dump(out, open("results/deck_data.json", "w"), indent=1, default=float)
print("ok")
