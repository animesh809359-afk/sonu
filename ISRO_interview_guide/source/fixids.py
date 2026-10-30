import sys, zipfile, re, shutil
src = sys.argv[1]; tmp = src + ".tmp"
zin = zipfile.ZipFile(src); zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data = zin.read(item.filename)
    if item.filename == "word/document.xml":
        s = data.decode("utf8"); n = [0]
        def rep(m):
            n[0] += 1; return f'{m.group(1)}id="{n[0]}"'
        s = re.sub(r'(<wp:docPr )id="\d+"', rep, s)
        s = re.sub(r'(<pic:cNvPr )id="\d+"', lambda m: m.group(1) + 'id="0"', s)
        data = s.encode("utf8"); print("renumbered", n[0], "drawings")
    zout.writestr(item, data)
zout.close(); shutil.move(tmp, src)
