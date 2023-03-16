![trappist logo](trappist.svg)

Trappist is a tool for computing _minimal trap spaces_ of a Boolean model.

# Install

You can install trappist with `pip` directly from the Package Index:

``` sh
$ python3 -m pip install trappist
```

or grab the very latest version from the source:

``` sh
$ python3 -m pip install -e git+https://github.com/soli/trap-spaces-as-siphons.git
```

You will also need the `clingo` ASP solver in your PATH for the `asp` method of computing the trap spaces (default). Instructions are provided directly on the [Potassco pages](https://github.com/potassco/clingo/releases/).

Note that Trappist does install the [PySAT](https://pysathq.github.io/docs/html/index.html) module so that the `sat` method is always available even if you do not have `clingo`.

# Run trappist in a Binder image

Submitted version: [![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/soli/trap-spaces-as-siphons/camera-ready)

Latest version, with _2022-12-01_ colomoto-docker image: [![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/soli/trap-spaces-as-siphons/main)

# Read about trappist

The first article describing trappist is [here](cmsb22.pdf)

# Run trappist from the command line

After installing `trappist` (and maybe `clingo`), just run

``` sh
$ trappist [-m maximum number of solutions] [-t maximum time to use in seconds] [-s solver (asp|sat)] <PNML input file>
```
