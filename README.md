![trappist logo](trappist.svg | width=200)

Trappist is a tool for computing _minimal trap spaces_ of a Boolean model.

# Run trappist in a Binder image

Submitted version: [![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/soli/trap-spaces-as-siphons/submitted)

Latest version: [![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/soli/trap-spaces-as-siphons/main)

# Read about trappist

The article describing trappist is [here](trappist.pdf)

# Run trappist from the command line

After installing trappist (and the `clingo` ASP solver), just run

``` sh
$ trappist [-m maximum number of solutions] [-t maximum time to use in seconds] <PNML input file>
```
