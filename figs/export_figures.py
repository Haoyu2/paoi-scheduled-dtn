#!/usr/bin/env python3
"""Export every figure of paper/main.tex as a standalone PDF.

Journals (DCN among them) ask for each illustration as a separate file in
addition to the embedded manuscript.  This script extracts each
`tikzpicture` from `paper/main.tex` and `paper/figures_auto.tex`, wraps it
in a `standalone` document that reuses the manuscript's packages and
notation macros, and compiles it to `paper/figures/Fig-<n>.pdf` in figure
order.

    python3 figs/export_figures.py

Requires pdflatex on PATH.  Output is vector PDF, no rasterisation.
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAPER = os.path.join(ROOT, "paper")
OUT = os.path.join(PAPER, "figures")
MAIN = os.path.join(PAPER, "main.tex")
AUTO = os.path.join(PAPER, "figures_auto.tex")

# Packages/macros the figures need; kept in sync with main.tex's preamble.
PREAMBLE = r"""\usepackage{amsmath}% must precede txfonts (\iint clash)
\usepackage{txfonts}% Times text+math, matching elsarticle's [times]
\usepackage{bm}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usetikzlibrary{positioning,arrows.meta,calc,fit,backgrounds}
\newcommand{\AoI}{\Delta}
\newcommand{\PAoI}{\mathrm{PAoI}}
\newcommand{\OPAoI}{\mathrm{OPAoI}}
\newcommand{\PAoIper}{\mathrm{PAoI}^{\mathrm{per}}}
\newcommand{\E}{\mathbb{E}}
\newcommand{\Prob}{\mathbb{P}}
\newcommand{\ind}{\mathbb{1}}
\newcommand{\Rmin}{R_{\min}}
\newcommand{\Ymin}{Y_{\min}}
\newcommand{\peff}{p_e}
\newcommand{\kstar}{k^{\ast}}
\newcommand{\GEN}{\mathrm{GEN}}
"""


def figure_blocks(text):
    """Yield (label, tikz_source) for each figure environment, in order."""
    pattern = re.compile(
        r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}", re.S)
    for m in pattern.finditer(text):
        body = m.group(1)
        tikz = re.search(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}",
                         body, re.S)
        if not tikz:
            continue
        lab = re.search(r"\\label\{(fig:[^}]+)\}", body)
        yield (lab.group(1) if lab else "fig:unlabelled"), tikz.group(0)


def main():
    if shutil.which("pdflatex") is None:
        sys.exit("pdflatex not found on PATH")

    # figures_auto.tex opens with \definecolor / \pgfplotsset definitions the
    # generated figures rely on; reuse them so exports match the manuscript.
    auto_all = open(AUTO, encoding="utf8").read()
    cut = auto_all.find(r"\begin{figure}")
    auto_header = auto_all[:cut] if cut > 0 else ""
    auto_header = "\n".join(l for l in auto_header.splitlines()
                             if not l.startswith("%"))

    main_src = open(MAIN, encoding="utf8").read()
    body = main_src[main_src.index(r"\begin{document}"):]
    # figures_auto.tex is \input where the auto figures belong; splice it in
    # so the exported numbering matches the compiled manuscript.
    body = body.replace(r"\input{figures_auto}", auto_all)

    blocks = list(figure_blocks(body))
    if not blocks:
        sys.exit("no figures found")

    os.makedirs(OUT, exist_ok=True)
    build = os.path.join(OUT, ".build")
    os.makedirs(build, exist_ok=True)

    made = []
    for i, (label, tikz) in enumerate(blocks, start=1):
        # \resizebox to a text/column width has no meaning outside the
        # two-column manuscript: export at natural size instead.
        tikz = re.sub(r"\\resizebox\{\\(?:column|text)width\}\{!\}\{%?\s*",
                      "", tikz)
        name = "Fig-%d" % i
        tex = os.path.join(build, name + ".tex")
        with open(tex, "w", encoding="utf8") as fh:
            fh.write("\\documentclass[border=2pt]{standalone}\n")
            fh.write(PREAMBLE)
            fh.write(auto_header + "\n")
            fh.write("\\begin{document}\n")
            fh.write(tikz)
            fh.write("\n\\end{document}\n")
        r = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
             "-output-directory", build, tex],
            capture_output=True, text=True)
        pdf = os.path.join(build, name + ".pdf")
        if r.returncode != 0 or not os.path.exists(pdf):
            print("FAIL  %-8s (%s)" % (name, label))
            continue
        shutil.copy(pdf, os.path.join(OUT, name + ".pdf"))
        size = os.path.getsize(pdf)
        made.append(name)
        print("ok    %-8s %-18s %6.1f KB" % (name, label, size / 1024))

    shutil.rmtree(build, ignore_errors=True)
    print("\n%d/%d figures exported to %s"
          % (len(made), len(blocks), os.path.relpath(OUT, ROOT)))
    if len(made) != len(blocks):
        sys.exit(1)


if __name__ == "__main__":
    main()
