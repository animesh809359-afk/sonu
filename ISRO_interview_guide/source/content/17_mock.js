module.exports = [
{ h1: "17. Mock interview: long-form model answers and programme timeline" },
{ fig: "timeline", cap: "Milestones of space technology applications for Indian agriculture (1988–2026)." },
{ p: "Use the **PREP structure** for every long answer: **P**oint (one-line definition), **R**eason (the physics or principle), **E**xample (Indian programme or paper), **P**ath forward (limitation and your contribution). Aim for 90–120 seconds per answer." },

{ h2: "17.1 Insurance and yield (expected main focus)" },
{ qa: [
  ["You have to estimate paddy yield for 500 gram panchayats in Odisha for Kharif 2026 under YES-TECH. How will you do it?",
   "**Point:** I would build a GP-level ensemble yield system calibrated with CCEs. **Steps:** (1) A rice mask from Sentinel-1 and NISAR 12-day VH/HH time series, which work through monsoon clouds, with transplanting dates taken from the flooding minimum. (2) Features: SAR backscatter trajectories, cloud-free Sentinel-2 NDVI/NDRE where available, TROPOMI SIF (FLEX when operational), IMD gridded rainfall, heat-stress days, NISAR soil moisture and soil properties. (3) Five base models: an LUE semi-physical model, WOFOST or ORYZA with LAI assimilation, XGBoost, LSTM and a weather-index regression. (4) Train on 5 years of geotagged CCEs with leave-one-year-out validation. (5) Stack the models, and use the spread between members as uncertainty. (6) Validate on holdout CCEs, targeting MAPE below 12 %. (7) Deliver GP yields with the 30 % blending, and flag high-uncertainty GPs for additional CCEs. **Caveats:** cloud cover, cyclone and flood years (which need SAR inundation layers), and CCE quality."],
  ["What are the weaknesses of CCE-based yield estimation, and how does technology help?",
   "CCEs are expensive and labour-intensive (lakhs per season). They can be biased by non-random plot selection and manipulation. Measurement and driage errors occur, results arrive late (which delays claims), and a few points per GP may not represent heterogeneous fields. Technology helps in two ways. **Smart sampling** stratifies by RS vigour so CCEs are fewer and more representative. **Direct estimation** produces wall-to-wall model yields. CROPIC photos and the CCE-Agri app add transparency through geotagging and video."],
  ["Design an insurance product for a horticulture belt where CCEs are not feasible.",
   "A **hybrid weather and satellite index**. Weather triggers (from WINDS or AWS) cover frost, high temperature at flowering and excess rain. A satellite layer (Sentinel-2 or FLEX canopy stress, LST from Sentinel-3 or TRISHNA, NISAR soil moisture) reduces basis risk by confirming crop-level impact. Payouts are tiered from strike to exit. The product is priced from 20+ years of reanalysis weather and RS anomaly history, and parametric settlement could happen within 15 days. A localised-loss window covers hail, verified with CROPIC photos and SAR change detection."],
  ["Why is basis risk a problem and how would you reduce it?",
   "Basis risk is the mismatch between the index payout and a farmer's actual loss. A farmer who loses the crop but gets no payout loses trust, and adoption falls. It can be reduced with **smaller units** (GP rather than block), **better indices** (field-level RS yield instead of station weather), **multi-index triggers** and **gap-filling** of weather data with satellite rainfall and soil moisture. Audits and grievance channels that use satellite evidence also help."],
] },

{ h2: "17.2 Residue burning" },
{ qa: [
  ["The Ministry says fire counts in Punjab fell 90 % but Delhi's AQI is still poor in November. Explain.",
   "(1) **Detection gaps:** polar orbiters pass at about 10:30 and 13:30, and farmers have shifted burning to the late afternoon, so many fires are missed. Small, short fires and fires under smoke or cloud are also missed. (2) **Burnt area** from Sentinel-2 dNBR shows a smaller decline than counts, so actual burning fell less than the counts suggest. (3) **Meteorology:** low November boundary-layer height, calm winds and inversions trap pollutants regardless of the source. (4) **Other sources:** vehicles, construction dust, industry, biomass for heating and firecrackers. (5) **Long-range transport** depends on the wind direction (north-westerlies carry smoke to Delhi). **Solution:** combine VIIRS counts, GEO fire detection, Sentinel-2 burnt area and FRP-based emission inventories, and attribute sources with chemical transport models."],
  ["Explain how you would map burnt area for the 2026 paddy season and validate it.",
   "Start with a paddy mask (Sentinel-1). Build 5-day Sentinel-2 composites from 1 October to 30 November and compute NBR, NBR2, MIRBI and BAIS2. Detect the transition from harvested stubble to burnt as a dNBR increase, plus NBR2 and MIRBI thresholds, refined with a Random Forest trained on VIIRS-guided and field samples. Validate with stratified random points interpreted on PlanetScope imagery and field photos, and report the error-adjusted area (Olofsson 2014) by district."],
] },

{ h2: "17.3 ET, SIF and NISAR" },
{ qa: [
  ["You have only a Landsat image and one weather station. How do you get daily ET for wheat fields?",
   "Run METRIC. Compute albedo, NDVI, LAI and emissivity, and LST from TIRS. Calculate Rn, then G, then select hot and cold pixels, with the cold pixel set to ET = 1.05 ETr from the station's hourly data. Iterate H with Monin–Obukhov stability to get instantaneous λET, then ETrF. Daily ET = ETrF × ETr,24 from the same station. For the season, interpolate ETrF between cloud-free images and multiply by daily ETr."],
  ["How does FLEX help Indian agriculture specifically?",
   "(1) **Early stress detection** for heat waves in March during wheat grain filling and for dry spells in rainfed kharif crops. (2) **GPP and yield** at 300 m, closer to the GP scale than TROPOMI. (3) **Separating structure from physiology** using both fluorescence peaks, PRI and LST. (4) **Inputs to yield models and insurance.** (5) **Science:** C3/C4 differences and irrigation effects on photosynthesis. India can contribute ground cal/val super-sites (FloX instruments next to EC towers at IARI and NRSC sites) and help develop algorithms for heterogeneous smallholder landscapes."],
  ["Compare optical and SAR for kharif crop mapping.",
   "Optical sensors give spectral and biochemical detail (chlorophyll, water) but clouds block them in July–September. SAR is all-weather and sensitive to structure, moisture and flooding, which suits rice, but it is affected by speckle and roughness. In practice, SAR (Sentinel-1, EOS-04 and now NISAR L/S) forms the backbone of kharif mapping and optical data are fused in where available."],
] },

{ h2: "17.4 Carbon, CA and precision agriculture" },
{ qa: [
  ["Can a Punjab farmer earn carbon credits for not burning straw? What would MRV look like?",
   "Yes, under methodologies such as VM0042, through avoided CH₄ and N₂O from burning, SOC gains from residue retention and zero tillage, and reduced diesel. **MRV:** baseline burning history from 5+ years of VIIRS and Sentinel-2 data; project-period monitoring showing no fires or burn scars, a ZT signature (NDTI, early green-up) and wheat sowing; soil sampling stratified by remote sensing; a calibrated model (DayCent or RothC) for SOC; then verification by a VVB. Credits are small per hectare (about 1–1.5 tCO₂e), so **aggregation** and **low-cost digital MRV** are essential. IARI's CREAMS fire and ZT mapping already supplies the practice-verification layer."],
  ["What is your view on precision agriculture for small farms?",
   "Precision should be **knowledge-intensive, not capital-intensive**. Satellite-based field and village zoning, LCC and GreenSeeker-based N management, laser levelling, sensor-based irrigation and drone spraying through CHCs give most of the benefit. ICAR-NePPA (led by IARI) and AgriStack data integration can scale these approaches."],
] },

{ h2: "17.5 Opening and closing questions" },
{ qa: [
  ["Why ISRO and not academia?", "ISRO turns science into operational national services (FASAL, NADAMS, fire bulletins, NISAR products). I want my retrieval and modelling research to reach millions of farmers through such services, with the scale, data and mission discipline that only ISRO offers."],
  ["What is one limitation of your own research?", "Say it honestly, then give a remedy. For example: my model was validated over two seasons in one agro-climatic zone. To make it operational I would test leave-one-year-out across zones, add SAR for cloud-prone years and quantify uncertainty."],
  ["Where do you see agricultural remote sensing in 10 years?", "Field-scale, daily, multi-sensor (optical, SAR including NISAR, thermal including TRISHNA, SIF including FLEX, hyperspectral) data fused by foundation models and assimilated into digital twins. It will provide GP-level yield, water and carbon accounting that directly drives insurance, advisories and carbon markets, with India building sovereign AI capability through bodies such as IAIRO."],
] },
];
