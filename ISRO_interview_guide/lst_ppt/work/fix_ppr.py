import sys, zipfile, shutil
from lxml import etree
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
src = sys.argv[1]; tmp = src + ".tmp"
zin = zipfile.ZipFile(src); zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
removed = 0
for item in zin.infolist():
    data = zin.read(item.filename)
    if item.filename.startswith("ppt/slides/slide") and item.filename.endswith(".xml"):
        root = etree.fromstring(data)
        for p in root.iter("{%s}p" % A):
            pprs = p.findall("{%s}pPr" % A)
            for extra in pprs[1:]:
                p.remove(extra); removed += 1
            if pprs and p.index(pprs[0]) != 0:
                p.remove(pprs[0]); p.insert(0, pprs[0])
        data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    zout.writestr(item, data)
zout.close(); shutil.move(tmp, src); print("removed duplicate pPr:", removed)
