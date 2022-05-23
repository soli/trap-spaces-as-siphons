![trappist logo](trappist.svg)

Trappist is a tool for computing _minimal trap spaces_ of a Boolean model.

# Install

You can install trappist with `pip`:

``` sh
$ python3 -m pip install -e git+https://github.com/soli/trap-spaces-as-siphons.git
```

You will also need the `clingo` ASP solver in your PATH. Instructions are provided directly on the [Potassco pages](https://github.com/potassco/clingo/releases/).
`
# Run trappist in a Binder image

Submitted version: [![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/soli/trap-spaces-as-siphons/submitted)

Latest version: [![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/soli/trap-spaces-as-siphons/main)

# Read about trappist

The article describing trappist is [here](cmsb22.pdf)

# Run trappist from the command line

After installing `trappist` (and `clingo`), just run

``` sh
$ trappist [-m maximum number of solutions] [-t maximum time to use in seconds] <PNML input file>
```
