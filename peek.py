import osmium

PBF = "south-korea-251127.osm.pbf"   # <-- change to your exact filename

class Peek(osmium.SimpleHandler):
    def __init__(self, limit=30):
        super().__init__()
        self.limit = limit
        self.count = 0

    def _show(self, kind, obj):
        if self.count >= self.limit:
            return
        print(f"{kind} id={obj.id} tags={dict(obj.tags)}")
        self.count += 1

    def node(self, n): self._show("node", n)
    def way(self, w): self._show("way ", w)
    def relation(self, r): self._show("rel ", r)

Peek().apply_file(PBF, locations=False)
print("DONE")
