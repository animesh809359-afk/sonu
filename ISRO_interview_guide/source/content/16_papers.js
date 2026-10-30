const P = (title, cite, items) => [{ h3: title }, { p: `*${cite}*` }, { ul: items }];
module.exports = [
{ h1: "16. Research-paper summaries (concepts and evidence)" },
{ p: "Each summary gives the **objective**, the **data and method**, the **key finding** and **how to use it in the interview**. Mentioning one or two of these by author and year shows depth." },

{ h2: "16.1 Evapotranspiration" },
...P("SEBAL: the original energy-balance algorithm", "Bastiaanssen, Menenti, Feddes & Holtslag (1998), J. Hydrology 212–213", [
  "**Objective:** estimate regional ET from satellite data with minimal ground data.",
  "**Method:** residual SEB; dT linearly related to Ts and calibrated with hot and cold pixels; Monin–Obukhov iteration for rah.",
  "**Finding:** ET within about 10–20 % (instantaneous) and 5 % (seasonal) of field measurements in Egypt, Spain and Niger.",
  "**Use:** the ‘internal calibration’ idea removes most of the absolute Ts bias, which is why SEBAL spread worldwide.",
]),
...P("METRIC", "Allen, Tasumi & Trezza (2007), J. Irrig. Drain. Eng. 133(4)", [
  "**Objective:** an operational, high-resolution ET model for water-rights management.",
  "**Method:** SEBAL-based, but the cold pixel is calibrated to 1.05 ETr (alfalfa reference) from weather stations, and the ETrF method is used for daily and seasonal scaling.",
  "**Finding:** seasonal ET within about 4–7 % of lysimeters in Idaho.",
  "**Use:** explains why ETrF (AET/ET₀) scaling beats EF scaling under advection.",
]),
...P("ALEXI two-source time-integrated model", "Anderson, Norman, Diak, Kustas & Mecikalski (1997), Remote Sens. Environ. 60", [
  "**Objective:** remove the need for air temperature and accurate absolute Ts.",
  "**Method:** TSEB coupled with an ABL growth model using the morning rise in GOES Ts.",
  "**Finding:** robust continental-scale fluxes; the basis of the ESI drought product.",
  "**Use:** cite it when asked how to estimate ET without ground meteorology, for example with INSAT data.",
]),
...P("Evaporative fraction self-preservation", "Crago (1996), J. Hydrology 180", [
  "**Finding:** EF is approximately constant during daytime under fair weather, with small concave-up deviations (lower at mid-day).",
  "**Use:** the theoretical basis for instantaneous-to-daily scaling and its known 5–10 % underestimation.",
]),

{ h2: "16.2 SIF and FLEX" },
...P("Global crop photosynthesis from SIF", "Guanter et al. (2014), PNAS 111(14)", [
  "**Objective:** test whether satellite SIF captures cropland photosynthesis better than models.",
  "**Data:** GOME-2 SIF compared with flux-tower GPP in the US Corn Belt.",
  "**Finding:** SIF-based GPP peaks were 40–60 % higher than those of carbon-cycle models, which underestimate agricultural productivity.",
  "**Use:** SIF captures the high intensity of irrigated, high-input crops (relevant to Punjab and Haryana).",
]),
...P("SIF improves crop productivity monitoring", "Guan et al. (2016), Global Change Biology 22", [
  "**Finding:** GOME-2 SIF explained US county maize and soybean yield and GPP better than EVI and NDVI. C4 vs C3 LUE differences must be accounted for.",
  "**Use:** supports SIF as a yield predictor in YES-TECH-type models once FLEX data are available.",
]),
...P("Drought onset detected by SIF", "Sun et al. (2015), J. Geophys. Res. Biogeosci. 120", [
  "**Finding:** during the 2012 US flash drought, GOME-2 SIF declined earlier and more strongly than NDVI or EVI, tracking the GPP drop.",
  "**Use:** early-warning and mid-season adversity triggers for PMFBY.",
]),
...P("50 years of SIF remote sensing (review)", "Mohammed et al. (2019), Remote Sens. Environ. 231", [
  "**Content:** physiology, the leaf-to-canopy scaling (fesc), retrieval methods (FLD, SFM, SVD), instruments and missions, and open challenges.",
  "**Use:** the go-to reference for explaining why SIF ≠ GPP everywhere (APAR dominance, structural effects).",
]),
...P("FLEX mission concept", "Drusch et al. (2017), IEEE TGRS 55(3)", [
  "**Content:** FLORIS design (500–780 nm, 0.3 nm in the O₂ bands), tandem with Sentinel-3, 300 m resolution and the products (full SIF spectrum, PRI and NPQ, photosynthesis).",
  "**Use:** cite it for mission specifications; FLEX launched on 15 Sep 2026.",
]),

{ h2: "16.3 SAR and soil moisture" },
...P("Water Cloud Model", "Attema & Ulaby (1978), Radio Science 13", [
  "**Idea:** the canopy is modelled as a cloud of identical water droplets held in place by the vegetation. Backscatter = volume term + attenuated soil term.",
  "**Use:** the standard vegetation correction for SAR soil moisture (Sentinel-1, NISAR).",
]),
...P("Change detection soil moisture", "Wagner, Lemoine & Rott (1999), Remote Sens. Environ. 70", [
  "**Idea:** normalise backscatter between the historical dry and wet references to get relative soil moisture; roughness is assumed static.",
  "**Use:** the basis of the ASCAT and Copernicus SSM products and one of the NISAR algorithms.",
]),
...P("Topp's equation", "Topp, Davis & Annan (1980), Water Resour. Res. 16", [
  "**Idea:** an empirical polynomial between the dielectric constant and volumetric water content, valid across mineral soils.",
  "**Use:** the basis of TDR probes and dielectric-to-moisture conversion in radar retrievals.",
]),

{ h2: "16.4 Fire and burnt area" },
...P("MODIS Collection 6 active fire algorithm", "Giglio, Schroeder & Justice (2016), Remote Sens. Environ. 178", [
  "**Method:** a contextual algorithm using the 4 µm and 11 µm brightness temperatures, a background characterisation window and false-alarm rejection. FRP is computed from MIR radiance.",
  "**Use:** describes the algorithm behind FIRMS data used in the IARI bulletin.",
]),
...P("FRP to biomass combustion", "Wooster, Roberts, Perry & Kaufman (2005), J. Geophys. Res. 110", [
  "**Finding:** laboratory burns gave a combustion factor of **0.368 ± 0.015 kg MJ⁻¹**, independent of fuel type.",
  "**Use:** converts FRE to biomass burnt and emissions (see the Chapter 15 example).",
]),
...P("Normalised Burn Ratio and CBI", "Key & Benson (2006), USDA FIREMON RMRS-GTR-164", [
  "**Method:** NBR from Landsat NIR and SWIR2; dNBR calibrated against the field Composite Burn Index.",
  "**Use:** gives the dNBR severity thresholds; adapt them for stubble (low pre-fire biomass) using RdNBR or RBR.",
]),
...P("MODIS fire characteristics in north India", "Vadrevu, Ellicott, Badarinath & Vermote (2011), Environmental Pollution 159", [
  "**Finding:** strong seasonal peaks of paddy-residue fires in Punjab in Oct–Nov, linked to rises in aerosol optical depth over the IGP.",
  "**Use:** early evidence of the regional air-quality link to burning.",
]),
...P("Missing emissions from post-monsoon fires", "Liu, Marlier et al. (2020), Environ. Res. Commun. 2", [
  "**Finding:** MODIS burned-area and active-fire products miss a large share of small agricultural fires in NW India, so emissions are underestimated. Finer sensors (VIIRS, Sentinel-2) detect much more.",
  "**Use:** supports your argument for combining VIIRS counts with Sentinel-2 burnt area, and with GEO data for late-afternoon fires.",
]),

{ h2: "16.5 Crop yield and parameter retrieval" },
...P("Monteith light-use efficiency", "Monteith (1972), J. Appl. Ecol. 9", [
  "**Idea:** crop dry matter is proportional to intercepted (absorbed) solar radiation; ε is fairly conservative for a given crop type.",
  "**Use:** the foundation of the semi-physical yield model in FASAL and YES-TECH.",
]),
...P("Scalable Crop Yield Mapper (SCYM)", "Lobell et al. (2015), Remote Sens. Environ. 164", [
  "**Method:** run a crop model (APSIM) many times with varied weather, soil and management; fit a regression of simulated yield on simulated VIs and weather; apply the regression to satellite VIs.",
  "**Finding:** field-level maize and soybean yield without any ground calibration.",
  "**Use:** a model for calibration-free GP-level yield in data-poor areas, a hybrid of crop model and ML.",
]),
...P("Smallholder wheat yields and sowing dates in India", "Jain et al. (2016), Remote Sensing 8(10), 860", [
  "**Data:** SkySat and Landsat micro-satellite data with crop-cut data in Bihar.",
  "**Finding:** field-scale yield and sowing-date mapping is feasible for smallholders. Late sowing reduces yield, consistent with terminal heat.",
  "**Use:** evidence that field-level remote sensing works in Indian smallholder systems.",
]),
...P("Assimilating remote sensing into crop models (review)", "Huang et al. (2019), Agric. For. Meteorol. 276–277", [
  "**Content:** forcing, calibration and updating (EnKF, PF, 4D-Var) strategies; variables (LAI, SM, ET); gains in yield accuracy.",
  "**Use:** cite it when explaining the crop-model-to-digital-twin link.",
]),
...P("Retrieval of vegetation properties (review)", "Verrelst et al. (2015), ISPRS J. Photogramm. 108", [
  "**Content:** parametric, non-parametric, physical and hybrid retrieval methods compared, with their strengths and weaknesses.",
  "**Use:** the framework in Chapter 5.1 comes from this review.",
]),
...P("PROSPECT + SAIL review", "Jacquemoud et al. (2009), Remote Sens. Environ. 113", [
  "**Content:** 20 years of PROSAIL use, inversion approaches and the ill-posed problem.",
  "**Use:** cite it for RTM basics.",
]),
...P("Optical-sensor-based N management", "Raun et al. (2002), Agron. J. 94", [
  "**Finding:** GreenSeeker NDVI-based in-season N (the INSEY algorithm) increased NUE by more than 15 % in winter wheat compared with uniform rates.",
  "**Use:** the standard example of sensor-based VRT.",
]),

{ h2: "16.6 Soil, carbon and conservation agriculture" },
...P("On digital soil mapping", "McBratney, Mendonça Santos & Minasny (2003), Geoderma 117", [
  "**Idea:** the scorpan framework S = f(s, c, o, r, p, a, n) + spatially autocorrelated residuals.",
  "**Use:** the conceptual basis of DSM (Dr. Bappa Das's line of work).",
]),
...P("The contentious nature of soil organic matter", "Lehmann & Kleber (2015), Nature 528", [
  "**Idea:** SOM is a continuum of progressively decomposed compounds. Persistence depends on accessibility and mineral protection rather than intrinsic ‘humic’ recalcitrance.",
  "**Use:** explains why MAOM and aggregation (helped by zero tillage) matter for permanence in carbon credits.",
]),
...P("Tillage mapping with Sentinel-2 in the IGP", "Zhou et al. (2021), Remote Sensing 13(24), 5108", [
  "**Method:** Sentinel-2 time series, tillage indices (NDTI and related), Random Forest on Google Earth Engine across the Indo-Gangetic Plains.",
  "**Finding:** field-level ZT and CT discrimination is feasible at regional scale in smallholder systems.",
  "**Use:** the same principle as the IARI CREAMS Zero-Tillage Mapper (Dhakar & Sehgal).",
]),
...P("CA eligibility for carbon credits", "Cariappa et al. (2024), Scientific Reports", [
  "**Method:** farmer surveys and remote sensing to assess whether CA practices in the IGP meet Verra VM0042 requirements (additionality, baseline, practice change).",
  "**Use:** shows that remote-sensing-based practice verification is central to agricultural MRV in India.",
]),
...P("Area estimation and accuracy assessment good practice", "Olofsson et al. (2014), Remote Sens. Environ. 148", [
  "**Idea:** pixel counting is biased. Use a stratified sample of reference data to estimate class area with confidence intervals (error-adjusted area).",
  "**Use:** the right way to report crop area (FASAL) and burnt area.",
]),
];
