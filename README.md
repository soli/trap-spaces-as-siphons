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

CMSB 2022 Submitted version: [![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/soli/trap-spaces-as-siphons/camera-ready)

Latest version, with _2022-12-01_ colomoto-docker image: [![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/soli/trap-spaces-as-siphons/main)

# Read about trappist

You can find articles describing trappist [here](https://hal.science/hal-03721508), [here](https://hal.science/hal-04167028/) and [here](https://hal.science/hal-04523118/) (`tsconj`'s improvements have been backported to `trappist` with `conj` and `conj-c` solvers).

# Run trappist from the command line

After installing `trappist` (and maybe `clingo`), just run

```
$ trappist -h
usage: trappist [-h] [-d] [-v] [-m MAX] [-p PARALLEL] [-t TIME] [-c {min,max,fix}] [-s {asp,cp,ilp,sat,naive,conj,conj-c}] [infile]

Compute minimal trap-spaces of a Petri-net encoded Boolean model. Copyright (C) Sylvain.Soliman@inria.fr and
giang.trinh91@gmail.com GPLv3

positional arguments:
  infile                Boolnet (.bnet) file of the model or Petri-net (PNML) file of its Petri net encoding. 'naive' and
                        'conj(-c)' solvers only handle .bnet input.

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Print debugging information.
  -v, --version         show program's version number and exit
  -m MAX, --max MAX     Maximum number of solutions (0 for all).
  -p PARALLEL, --parallel PARALLEL
                        Maximum number of cores to use [only for naive and conj(-c) method] (0 for no-limit).
  -t TIME, --time TIME  Maximum number of seconds for search (0 for no-limit).
  -c {min,max,fix}, --computation {min,max,fix}
                        Computation option.
  -s {asp,cp,ilp,sat,naive,conj,conj-c}, --solver {asp,cp,ilp,sat,naive,conj,conj-c}
                        Solver to compute the Maximal conflict-free siphons. 'asp', 'naive' and 'conj(-c)' require `clingo`, 'cp'
                        requires `minizinc`.
```
