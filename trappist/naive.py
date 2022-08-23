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

from math import ceil
from multiprocessing import Pool, cpu_count, current_process
from os import unlink
from sys import setrecursionlimit
from typing import IO, List, Set, Tuple

import networkx as nx  # TODO maybe replace with lists/dicts

from pyeda.boolalg.bdd import bdd2expr, expr2bdd
from pyeda.boolalg.expr import And, AndOp, Constant, Literal, Or, OrOp, Variable, expr

# from pyeda.boolalg.minimization import espresso_exprs

from . import pnml_to_asp


def write_naive_asp(petri_net: nx.DiGraph, asp_file: IO, nprocs: int):
    """Write the ASP program for naive encoding of trap spaces."""
    nnodes = petri_net.number_of_nodes()
    if nprocs == 0:
        nproc = cpu_count()
    else:
        nproc = min(nprocs, cpu_count())
    if nproc > 1:
        chunksize = ceil(nnodes / (8 * nproc))  # seems decent
        with Pool(nproc, setup_worker, (asp_file.name,)) as p:
            pids = set(
                p.imap_unordered(
                    add_variable,
                    petri_net.nodes(data=True),
                    chunksize,
                )
            )
        for p in pids:
            with open(f"{asp_file.name}_{p}", "r") as f:
                for line in f:
                    asp_file.write(line)
            unlink(f"{asp_file.name}_{p}")
    else:
        setrecursionlimit(2048)
        globals()["counter"] = 0
        globals()["pid"] = 0
        globals()["asp_file"] = asp_file
        for node_and_data in petri_net.nodes(data=True):
            add_variable(node_and_data)


def setup_worker(filename):
    """Set global variables for subprocess."""
    # big bnets…
    setrecursionlimit(2048)
    global counter
    counter = 0
    global pid
    pid = current_process().pid
    while pid is None:
        pid = current_process().pid
    global asp_file
    asp_file = open(f"{filename}_{pid}", "wt")


def add_variable(node_and_data):
    """Add all the rules for one variable."""
    node, data = node_and_data
    name = pnml_to_asp(node)
    print("{", name, "}.", sep="", file=asp_file)
    print(f"#show {name}/0.", file=asp_file)
    if not node.startswith("-"):
        print(
            f":- {name}, {pnml_to_asp('-' + node)}.", file=asp_file
        )  # conflict-freeness
    add_tree(expr(data["function"]).to_nnf(), expr(data["var"]), asp_file)
    asp_file.flush()
    return pid


def add_tree(source: expr, target: expr, asp_file):
    """Add the AST of things->target to the ASP program."""
    global counter
    if isinstance(target, Variable) and target.name.startswith("aux"):
        starget = target.name
    else:
        starget = pnml_to_asp(str(~target))

    if isinstance(source, Literal):
        print(f"{pnml_to_asp(str(~source))} :- {starget}.", file=asp_file)
    elif isinstance(source, Constant):
        if source.is_zero():
            print(f":- {starget}.", file=asp_file)
        elif source.is_one():
            # nothing to do
            pass
        else:
            raise ValueError(f"Houston we have a problem with {source}…")
    elif isinstance(source, OrOp):
        safe, unsafe = split_safe_unsafe(source)
        if unsafe:
            source = Or(cnf_from_bdd(Or(*unsafe)), *safe)
            if not isinstance(source, OrOp):
                return add_tree(source, target, asp_file)
        source_str = ""
        for s in source.xs:
            if isinstance(s, Literal):
                svs = pnml_to_asp(str(~s))
            else:
                vs = expr(f"aux_{pid}_{counter}")
                counter += 1
                add_tree(s, vs, asp_file)
                svs = str(vs)
            if source_str:
                source_str += "; " + svs
            else:
                source_str = svs
        print(f"{source_str} :- {starget}.", file=asp_file)
    elif isinstance(source, AndOp):
        for s in source.xs:
            if isinstance(s, Literal):
                print(f"{pnml_to_asp(str(~s))} :- {starget}.", file=asp_file)
            else:
                add_tree(s, target, asp_file)
    else:
        print(f"Houston we have a problem with {source}…")


def leaves(expression: expr) -> Set[Literal]:
    """Return all the Litterals in expression."""
    # TODO cache?
    s = set()
    for ex in expression.iter_dfs():
        if isinstance(ex, Literal):
            s.add(ex)
    return s


def split_safe_unsafe(expression: expr) -> Tuple[List[expr], List[expr]]:
    """Split an Or into safe and unsafe (contains a literal and its negation) parts."""
    assert isinstance(expression, OrOp)
    leaves_list = [leaves(child) for child in expression.xs]
    conflicts = set()
    for child1, child2 in [
        (a, b) for index, a in enumerate(leaves_list) for b in leaves_list[index + 1 :]
    ]:
        for v in child1:
            if ~v in child2:
                conflicts.add(v)
                conflicts.add(~v)
    safe = []
    unsafe = []
    for child, child_leaves in zip(expression.xs, leaves_list):
        if child_leaves & conflicts:
            unsafe.append(child)
        else:
            safe.append(child)
    return (safe, unsafe)


def cnf_from_bdd(source):
    """Get a CNF via a BDD."""
    conjunct = []
    for success in expr2bdd(~source).satisfy_all():
        disjunct = []
        for p, v in success.items():
            if v == 0:
                disjunct.append(bdd2expr(p))
            else:
                disjunct.append(~bdd2expr(p))
        conjunct.append(Or(*disjunct))
    result = And(*conjunct)
    return result
