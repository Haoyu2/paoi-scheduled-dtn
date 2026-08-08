#!/usr/bin/env python3
"""Install the Energy module into a dtnsim checkout and wire it in.

Idempotent. Run with the dtnsim src dir as arg (default ~/dtnsim/dtnsim/src).
Copies Energy.{h,cc,ned} into node/energy/, adds the submodule to Node.ned,
and gates Dtn.cc forwarding on battery (consume one copy per transmission).

    python3 apply_patch.py [/path/to/dtnsim/src]
"""
import os
import shutil
import sys

PATCH_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/dtnsim/dtnsim/src")


def main():
    edir = os.path.join(SRC, "node", "energy")
    os.makedirs(edir, exist_ok=True)
    for f in ("Energy.h", "Energy.cc", "Energy.ned"):
        shutil.copy(os.path.join(PATCH_DIR, f), os.path.join(edir, f))
    print("copied Energy module ->", edir)

    # --- Node.ned ---
    p = os.path.join(SRC, "node", "Node.ned")
    s = open(p).read()
    if "energy.Energy" not in s:
        s = s.replace("import src.node.com.Com;",
                      "import src.node.com.Com;\nimport src.node.energy.Energy;")
        s = s.replace(
            "    connections:",
            '        energy: Energy {\n'
            '            parameters:\n'
            '                @display("p=150,190");\n'
            '        }\n\n'
            '    connections:')
        open(p, "w").write(s)
        print("Node.ned patched")
    else:
        print("Node.ned already patched")

    # --- Dtn.cc ---
    p = os.path.join(SRC, "node", "dtn", "Dtn.cc")
    s = open(p).read()
    if "energy/Energy.h" not in s:
        s = s.replace("#include", '#include "src/node/energy/Energy.h"\n#include', 1)
        old = "if ((!neighborDtn->onFault) && (!this->onFault))"
        assert s.count(old) == 1, ("onFault gate count", s.count(old))
        new = ('Energy * energyMod = check_and_cast<Energy *>('
               'this->getParentModule()->getSubmodule("energy"));\n'
               '\t\t\tif ((!neighborDtn->onFault) && (!this->onFault) '
               '&& energyMod->available())')
        s = s.replace(old, new)
        snd = 'send(bundle, "gateToCom$o");'
        assert s.count(snd) == 1, ("send count", s.count(snd))
        s = s.replace(snd, 'energyMod->consume();\n\t\t\t\t\t' + snd)
        open(p, "w").write(s)
        print("Dtn.cc patched")
    else:
        print("Dtn.cc already patched")


if __name__ == "__main__":
    main()
