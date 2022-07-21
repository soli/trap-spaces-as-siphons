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
from typing import IO, Set

import networkx as nx  # TODO maybe replace with lists/dicts

from pyeda.boolalg.expr import AndOp, Constant, Literal, OrOp, Variable, expr
from pyeda.boolalg.minimization import espresso_exprs

from . import pnml_to_asp


def write_naive_asp(petri_net: nx.DiGraph, asp_file: IO):
    "Write the ASP program for naive encoding of trap spaces."
    nnodes = petri_net.number_of_nodes()
    if nnodes > 256:
        nproc = cpu_count()
    else:
        nproc = 1
    with Pool(nproc, setup_worker, (asp_file.name,)) as p:
        pids = set(
            p.imap_unordered(
                add_variable,
                petri_net.nodes(data=True),
                ceil(nnodes / (4 * nproc)),
            )
        )
    for p in pids:
        with open(f"{asp_file.name}_{p}", "r") as f:
            for line in f:
                asp_file.write(line)
        unlink(f"{asp_file.name}_{p}")


def setup_worker(filename):
    """Setup global variables for subprocess."""
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
    """Do what you need."""
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
            print(f"Houston we have a problem with {source}…")
    elif isinstance(source, OrOp):
        if unsafe(source):
            # espresso will not compute minimal implicants
            # but guarantees to remove redundancy
            (source,) = espresso_exprs(source.to_dnf())
            # we call back add_tree when source is not an OrOp any longer
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


def unsafe(expression: expr) -> bool:
    """Return True if leaves of two branches of an OrOp contain a variable and its negation."""
    if not isinstance(expression, OrOp):
        return False
    leaves_set = [leaves(child) for child in expression.xs]
    for child1, child2 in [
        (a, b) for index, a in enumerate(leaves_set) for b in leaves_set[index + 1 :]
    ]:
        for v in child1:
            if ~v in child2:
                return True
    return False
