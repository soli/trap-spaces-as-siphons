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

from dataclasses import asdict
from datetime import timedelta
from time import perf_counter
from typing import Generator, List

from minizinc import Instance, Model, Result, Solver, Status

import networkx as nx  # TODO maybe replace with lists/dicts


def create_cp(petri_net: nx.DiGraph) -> Model:
    """Create the CP program for the max conflict-free siphons of petri_net."""
    model = Model()
    model.add_string('include "globals.mzn";\n')
    variables = []
    for node in (n for n, k in petri_net.nodes(data="kind") if k == "place"):
        v = zincify(node)
        variables.append(v)
        model.add_string(f"var bool: {v};\n")
    for node, kind in petri_net.nodes(data="kind"):
        if kind == "place":
            if not node.startswith("-"):
                # conflict-freeness
                model.add_string(f"constraint not {node} \\/ not not_{node};\n")
        else:
            # it's a transition, apply siphon
            # (if one succ is true, one pred must be true)
            or_preds = [zincify(p) for p in petri_net.predecessors(node)]
            for succ in petri_net.successors(node):
                zsucc = zincify(succ)
                if zsucc not in or_preds:  # optimize obvious tautologies
                    or_string = " \\/ ".join(or_preds)
                    model.add_string(f"constraint {zsucc} -> {or_string};\n")
    model.add_string(
        f"solve :: bool_search([{', '.join(variables)}], input_order, indomain_max) satisfy;\n"
    )
    return model


def zincify(variable: str) -> str:
    """Return the name of the corresponding CP variable."""
    if variable.startswith("-"):
        return f"not_{variable[1:]}"
    return variable


def solve_cp(
    model: Model,
    max_output: int,
    time_limit: int,
    nprocs: int,
) -> Generator[List[int], None, None]:
    """Run an CP solver on given WCNF and get the solutions."""
    solver = Solver.lookup("gecode")
    inst = Instance(solver, model)
    nsol = 0
    if time_limit > 0:
        remaining = timedelta(seconds=time_limit)
    else:
        remaining = None
    # TODO handle time limit?
    while (remaining is None or remaining > timedelta()) and \
          (max_output == 0 or nsol < max_output):
        start = perf_counter()
        result = inst.solve(timeout=remaining, processes=nprocs)
        end = perf_counter()
        if remaining is not None:
            remaining -= timedelta(seconds=(end - start))
            # print(f"{remaining} remaining")
        if result.status == Status.SATISFIED:
            nsol += 1
            # print(result.solution)
            yield result
            d = asdict(result.solution)
            del d["_checker"]
            # lexicographic constraint to restart from last solution
            # first remove old one if there was already a solution found
            if nsol > 1:
                with model._lock:
                    del model._code_fragments[-2]
            model.add_string(
                f"constraint lex_less([{', '.join(d.keys())}], "
                f" [{', '.join(map(str, map(int, d.values())))}]);"
            )
            # non subset constrait for maximality
            non_sub = []
            for k, v in d.items():
                if not v:
                    non_sub.append(k)
            or_string = " \\/ ".join(non_sub)
            model.add_string(f"constraint {or_string};")
            inst = Instance(solver, model)
        else:
            print(result.status)
            break


def cp_to_bool(places: List[str], res: Result) -> List[str]:
    """Transform a Result to a list of 0/1/- strings."""
    result = []
    for place in places:
        if res[place]:
            result.append("0")
        elif res["not_" + place]:
            result.append("1")
        else:
            result.append("-")
    return result


def get_cp_solutions(
    petri_net: nx.DiGraph,
    max_output: int,
    time_limit: int,
    places: List[str],
    nprocs: int,
) -> Generator[List[str], None, None]:
    """Print the solutions."""
    for result in solve_cp(create_cp(petri_net), max_output, time_limit, nprocs):
        yield cp_to_bool(places, result)
