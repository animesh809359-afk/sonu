import json, subprocess, re
heads = json.load(open("headings.json"))
n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", "test.pdf"], capture_output=True, text=True).stdout).group(1))
norm = lambda x: re.sub(r"\W+", "", x).lower()
pages = [norm(subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "test.pdf", "-"], capture_output=True, text=True).stdout) for p in range(1, n+1)]
res, start, miss = {}, 2, []
for lvl, t in heads:
    key = norm(t)[:45]
    for p in range(start, n):
        if p >= 2 and key in pages[p] and not (p < 5 and "contents" in pages[p][:80]):
            res[t] = p + 1; start = p; break
    else: miss.append(t)
json.dump(res, open("tocpages.json", "w")); print("mapped", len(res), "missing", miss)
