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

from asyncio import get_running_loop, run
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import timedelta
from time import perf_counter
from typing import Generator, List

import networkx as nx  # TODO maybe replace with lists/dicts
from minizinc import Instance, Model, Solver, Status

from .cp import cp_to_bool, zincify


def create_ilp(petri_net: nx.DiGraph) -> Model:
    """Create the ILP program for the max conflict-free siphons of petri net."""
    model = Model()
    variables = []
    for node in (n for n, k in petri_net.nodes(data="kind") if k == "place"):
        v = zincify(node)
        variables.append(v)
        model.add_string(f"var bool: {v};\n")
    for node, kind in petri_net.nodes(data="kind"):
        if kind == "place":
            if not node.startswith("-"):
                # conflict-freeness
                model.add_string(f"constraint {node} + not_{node} <= 1;\n")
        else:
            # it's a transition, apply siphon
            # (if one succ is true, one pred must be true)
            or_preds = [zincify(p) for p in petri_net.predecessors(node)]
            for succ in petri_net.successors(node):
                zsucc = zincify(succ)
                if zsucc not in or_preds:  # optimize obvious tautologies
                    or_string = " + ".join(or_preds)
                    model.add_string(f"constraint {zsucc} <= {or_string};\n")
    model.add_string(f"solve maximize ({' + '.join(variables)});\n")
    return model


def solve_ilp(
    model: Model,
    max_output: int,
    time_limit: int,
    nprocs: int,
) -> Generator[List[int], None, None]:
    """Run an ILP solver on given model and get the solutions."""
    solver = Solver.lookup("cbc")
    inst = Instance(solver, model)
    nsol = 0
    if time_limit > 0:
        remaining = timedelta(seconds=time_limit)
    else:
        remaining = None
    # TODO handle time limit?
    while (remaining is None or remaining > timedelta()) and (
        max_output == 0 or nsol < max_output
    ):
        start = perf_counter()

        try:
            get_running_loop()
            with ThreadPoolExecutor(1) as pool:
                coroutine = inst.solve_async(timeout=remaining, processes=nprocs)
                result = pool.submit(lambda: run(coroutine)).result()  # noqa: B023
        except RuntimeError:
            result = inst.solve(timeout=remaining, processes=nprocs)

        end = perf_counter()
        if remaining is not None:
            remaining -= timedelta(seconds=(end - start))
            # print(f"{remaining} remaining")
        if result.status == Status.OPTIMAL_SOLUTION:
            nsol += 1
            # print(result.solution)
            yield result
            d = asdict(result.solution)
            del d["_checker"]
            # non subset constrait for maximality
            non_sub = []
            for k, v in d.items():
                if not v and k != "objective":
                    non_sub.append(k)
            or_string = " + ".join(non_sub)
            model.add_string(f"constraint 1 <= {or_string};")
            inst = Instance(solver, model)
        else:
            if result.status != Status.UNSATISFIABLE:
                print(result.status)
            break


def get_ilp_solutions(
    petri_net: nx.DiGraph,
    max_output: int,
    time_limit: int,
    places: List[str],
    nprocs: int,
) -> Generator[List[str], None, None]:
    """Print the solutions."""
    for result in solve_ilp(create_ilp(petri_net), max_output, time_limit, nprocs):
        yield cp_to_bool(places, result)
