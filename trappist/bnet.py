"""Compute minimal trap-spaces of a Petri-net encoded Boolean model.

Copyright (C) 2022 Sylvain.Soliman@inria.fr

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from sys import setrecursionlimit
from typing import IO

import networkx as nx  # TODO maybe replace with lists/dicts
from pyeda.boolalg.bdd import bddvar, expr2bdd
from pyeda.boolalg.expr import expr


def add_edges(net: nx.DiGraph, tname: str, things: expr, source: str):
    """Add all edges from things to tname and back in net except for source."""
    if source.startswith("-"):
        nsource = source[1:]
    else:
        nsource = "-" + source

    for i, t in enumerate(things.satisfy_all()):
        name = f"{tname}_{i}"
        net.add_node(name, kind="transition")
        for p, v in t.items():
            if v == 0:
                pname = "-" + str(p)
            else:
                pname = str(p)
            net.add_edge(pname, name)
            if (
                pname == source
            ):  # don't add an edge back to "source" but add to Not(source)
                net.add_edge(name, nsource)
            else:
                net.add_edge(name, pname)


def read_bnet(fileobj: IO, method: str) -> nx.DiGraph:
    """Parse a BoolNet .bnet file and build the corresponding Petri net."""
    net = nx.DiGraph()

    # big bnets…
    setrecursionlimit(204800)
    for line in fileobj.readlines():
        if line.startswith("#") or line.startswith("targets, factors"):
            continue
        line = line.split("#")[0]
        try:
            x, fx = line.replace(" ", "").replace("!", "~").split(",", maxsplit=1)
        except ValueError:  # not enough values to unpack
            continue
        net.add_node(x, kind="place")
        net.add_node(
            "-" + x, kind="place"
        )  # convention in PNML files obtained from bnet
        if method in ("asp", "sat", "cp", "ilp"):
            vx = bddvar(x)
            fx = expr2bdd(expr(fx))
            # print(x, fx)
            activate = fx & ~vx
            inactivate = ~fx & vx
            # print(activate, inactivate, sep="\n")

            add_edges(net, f"tp_{x}", activate, "-" + x)
            add_edges(net, f"tn_{x}", inactivate, x)
        else:
            # delay expr parsing to parallel jobs (for pickling)
            net.nodes[x]["function"] = fx
            net.nodes[x]["var"] = x
            net.nodes["-" + x]["function"] = "~(" + fx + ")"
            net.nodes["-" + x]["var"] = "~(" + x + ")"

    return net
