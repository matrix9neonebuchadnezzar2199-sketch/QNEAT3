from pathlib import Path

dup = (
    "        link_length_field = self.parameterAsString(parameters, self.LINK_LENGTH_FIELD, context) #float\n"
    "        link_length_field = self.parameterAsString(parameters, self.LINK_LENGTH_FIELD, context)\n"
)
fix = "        link_length_field = self.parameterAsString(parameters, self.LINK_LENGTH_FIELD, context)\n"

for p in Path(__file__).resolve().parent.parent.joinpath("algs").glob("*.py"):
    t = p.read_text(encoding="utf-8")
    if dup in t:
        p.write_text(t.replace(dup, fix), encoding="utf-8")
        print(p.name)
