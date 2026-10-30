import pymupdf as fitz, re, sys, os, json
U = "/root/.claude/uploads/37774611-8df8-5142-9e75-802c40299a43/"
PAPERS = {
    "parihar": "dcedde94-ed-mausam8JAISINGHPARIHAR93-104", "ray": "9ecd560e-ed-mausam24SHIBENDUS.RAY289-296",
    "prosail": "cdaf8211-1-s2.0-S0034425709000765-main", "dt": "080cad6f-DT", "dt1": "ac364d08-DT1",
    "fasal2": "5dd725df-fasakl", "giglio": "49fde553-Giglio2016_C6_Fire", "isprs14": "8f1678a6-isprsarchives-XL-8-977-2014",
    "isprs19": "aee63141-isprs-archives-XLII-3-W6-499-2019", "hess": "b56f3cf7-hess-18-1885-2014",
    "life": "468f2c10-life-12-01377", "qt": "44380043-qt7059k61t", "fei": "ce052e54-reference_to_texture_of_tempFei_et_al._2023",
    "pst": "33d76506-PST-ePrint-9444-article", "yestech": "820ae047-YESTYECH"}
CAP = re.compile(r"^\s*(Fig\.?|Figure|FIG\.?|Figs\.)\s*(\d+)", re.I)
os.makedirs("shots", exist_ok=True)
index = {}
for key, fn in PAPERS.items():
    doc = fitz.open(U + fn + ".pdf"); seen = set(); index[key] = []
    for pno, page in enumerate(doc):
        W, H = page.rect.width, page.rect.height
        blocks = [b for b in page.get_text("blocks") if b[6] == 0]
        graphics = [fitz.Rect(i["bbox"]) for i in page.get_image_info() if fitz.Rect(i["bbox"]).width > 40 and fitz.Rect(i["bbox"]).height > 30]
        try:
            graphics += [d["rect"] for d in page.get_drawings() if d["rect"].width > 3 or d["rect"].height > 3]
        except Exception:
            pass
        graphics = [g for g in graphics if g.width < W * 0.98 and g.height < H * 0.9]
        for b in blocks:
            txt = b[4].strip(); m = CAP.match(txt)
            if not m: continue
            n = int(m.group(2))
            if n in seen: continue
            cap = fitz.Rect(b[:4])
            if cap.height > 160: cap.y1 = cap.y0 + 160
            # column range
            full = cap.width > W * 0.55
            x0, x1 = (36, W - 36) if full else (cap.x0 - 15, cap.x1 + 15)
            cand = [g for g in graphics if g.y1 <= cap.y0 + 4 and g.y1 > cap.y0 - 520 and g.x1 > x0 and g.x0 < x1]
            if not cand: continue
            # keep contiguous graphics: walk upward from caption
            cand.sort(key=lambda g: -g.y1)
            region = fitz.Rect(cand[0]); bottom = cap.y0
            if bottom - region.y1 > 60: continue
            for g in cand[1:]:
                if g.y1 >= region.y0 - 40: region |= g
            # include text labels within region
            for tb in blocks:
                r = fitz.Rect(tb[:4])
                if r.y0 >= region.y0 - 2 and r.y1 <= cap.y0 + 2 and r.x0 >= x0 - 5 and r.x1 <= x1 + 5 and len(tb[4]) < 300:
                    region |= r
            if region.height < 60 or region.width < 100: continue
            clip = (region | cap) + (-6, -6, 6, 6)
            clip &= page.rect
            pix = page.get_pixmap(clip=clip, dpi=170)
            out = f"shots/{key}_fig{n}.png"; pix.save(out); seen.add(n)
            index[key].append({"fig": n, "page": pno + 1, "file": out, "caption": " ".join(txt.split())[:400], "w": pix.width, "h": pix.height})
    print(key, [f["fig"] for f in index[key]])
json.dump(index, open("shots/index.json", "w"), indent=1)
