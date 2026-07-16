# Springer Nature LaTeX manuscript

This repository contains a Springer Nature manuscript based on template
version 3.1 (December 2024).

## Requirements

- A TeX distribution with `latexmk`, `pdflatex`, and BibTeX (for example,
  TeX Live or MacTeX)
- GNU Make (optional; the equivalent `latexmk` command is shown below)

## Build

Run:

```sh
make
```

Or invoke `latexmk` directly:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error sn-article.tex
```

The output is `sn-article.pdf`. The `.latexmkrc` file adds the local `bst/`
directory to BibTeX's search path so the Springer Nature bibliography styles
are found automatically.

For continuous preview while editing, run `make watch`. To remove intermediate
files while keeping the PDF, run `make clean`. To remove intermediate files and
the generated PDF, run `make distclean`.

## Main files

- `sn-article.tex`: manuscript source
- `sn-bibliography.bib`: bibliography database
- `sn-jnl.cls`: Springer Nature document class
- `bst/`: Springer Nature BibTeX styles
- `user-manual.pdf`: template user manual

