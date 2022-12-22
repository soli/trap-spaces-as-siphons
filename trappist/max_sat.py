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

from itertools import islice
from typing import Generator, List

import networkx as nx  # TODO maybe replace with lists/dicts

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF


def create_maxsat(petri_net: nx.DiGraph) -> WCNF:
    """Create the MaxSAT program for the maximal conflict-free siphons of petri_net."""
    variables = {}
    wcnf = WCNF()
    for i, node in enumerate(
        (n for n, k in petri_net.nodes(data="kind") if k == "place"), start=1
    ):
        variables[node] = i
        wcnf.append([i], weight=1)
    for node, kind in petri_net.nodes(data="kind"):
        if kind == "place":
            if not node.startswith("-"):
                wcnf.append(
                    [-variables[node], -variables["-" + node]]
                )  # conflict-freeness
        else:  # it's a transition, apply siphon (if one succ is true, one pred must be true)
            or_preds = [variables[p] for p in petri_net.predecessors(node)]
            for succ in petri_net.successors(node):
                vsucc = variables[succ]
                if vsucc not in or_preds:  # optimize obvious tautologies
                    wcnf.append(or_preds + [-vsucc])
    return wcnf


def solve_maxsat(
    cnf: WCNF, max_output: int, time_limit: int
) -> Generator[List[int], None, None]:
    """Run an MaxSAT solver on given WCNF and get the solutions."""
    # print(cnf.hard)
    rc2 = RC2(cnf)
    sol = rc2.enumerate(block=-1)  # minimal correction subsets
    yield from islice(sol, None if max_output == 0 else max_output)


def sat_to_bool(
    places: List[str], all_places: List[str], model: List[int]
) -> List[str]:
    """Transform a model to a list of 0/1/- strings."""
    result = []
    for place in places:
        if all_places.index(place) + 1 in model:
            result.append("0")
        elif all_places.index("-" + place) + 1 in model:
            result.append("1")
        else:
            result.append("-")
    return result


def get_sat_solutions(
    petri_net: nx.DiGraph, max_output: int, time_limit: int, places: List[str]
) -> Generator[List[str], None, None]:
    """Print the solutions."""
    all_places = [
        node for node, kind in petri_net.nodes(data="kind") if kind == "place"
    ]
    for model in solve_maxsat(create_maxsat(petri_net), max_output, time_limit):
        yield sat_to_bool(places, all_places, model)
