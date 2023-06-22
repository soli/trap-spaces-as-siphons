"""Compute minimal trap-spaces of a Petri-net encoded Boolean model.

Copyright (C) 2023 Sylvain.Soliman@inria.fr

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
from typing import IO

import networkx as nx  # TODO maybe replace with lists/dicts

from pyeda.boolalg.bdd import bdd2expr, expr2bdd
from pyeda.boolalg.expr import And, AndOp, Constant, Literal, Or, OrOp, Variable, expr

# from pyeda.boolalg.minimization import espresso_exprs

from . import pnml_to_asp
from .naive import split_safe_unsafe


def write_conj_asp(petri_net: nx.DiGraph, asp_file: IO, nprocs: int):
    """Write the ASP program for conjunctive encoding of trap spaces."""
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
    # FIXME duplicated from naive, because it uses globals…
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
    print(f"#show {name}/0.", file=asp_file)
    if not node.startswith("-"):
        print(f"{name}, {pnml_to_asp('-' + node)}.", file=asp_file)  # conflict-freeness
    add_tree(expr(data["var"]), expr(data["function"]).to_nnf(), asp_file)
    asp_file.flush()
    return pid


def add_tree(source: expr, target: expr, asp_file):
    """Add the AST of things->target to the ASP program."""
    global counter
    if isinstance(source, Variable) and source.name.startswith("aux"):
        ssource = source.name
    else:
        ssource = pnml_to_asp(str(~source))

    if isinstance(target, Literal):
        print(f"{ssource} :- {pnml_to_asp(str(~target))}.", file=asp_file)
    elif isinstance(target, Constant):
        if target.is_zero():
            # nothing to do
            pass
        elif target.is_one():
            print(f"{ssource}.", file=asp_file)
        else:
            raise ValueError(f"Houston we have a problem with {target}…")
    elif isinstance(target, AndOp):
        safe, unsafe = split_safe_unsafe(target)
        if unsafe:
            target = And(dnf_from_bdd(And(*unsafe)), *safe)
            if not isinstance(target, AndOp):
                return add_tree(source, target, asp_file)
        target_str = ""
        for s in target.xs:
            if isinstance(s, Literal):
                svs = pnml_to_asp(str(~s))
            else:
                vs = expr(f"aux_{pid}_{counter}")
                counter += 1
                add_tree(vs, s, asp_file)
                svs = str(vs)
            if target_str:
                target_str += ", " + svs
            else:
                target_str = svs
        print(f"{ssource} :- {target_str}.", file=asp_file)
    elif isinstance(target, OrOp):
        for s in target.xs:
            if isinstance(s, Literal):
                print(f"{ssource} :- {pnml_to_asp(str(~s))}.", file=asp_file)
            else:
                add_tree(source, s, asp_file)
    else:
        print(f"Houston we have a problem with {target}…")


def dnf_from_bdd(source):
    """Get a DNF via a BDD."""
    disjunct = []
    for success in expr2bdd(source).satisfy_all():
        conjunct = []
        for p, v in success.items():
            if v == 1:
                conjunct.append(bdd2expr(p))
            else:
                conjunct.append(~bdd2expr(p))
        disjunct.append(And(*conjunct))
    result = Or(*disjunct)
    return result
