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

from typing import IO, Set

import networkx as nx  # TODO maybe replace with lists/dicts

from pyeda.boolalg.expr import AndOp, Constant, Literal, OrOp, Variable, expr
from pyeda.boolalg.minimization import espresso_exprs

from . import pnml_to_asp


def write_naive_asp(petri_net: nx.DiGraph, asp_file: IO):
    "Write the ASP program for naive encoding of trap spaces."
    counter = 0
    for node, data in petri_net.nodes(data=True):
        name = pnml_to_asp(node)
        print("{", name, "}.", sep="", file=asp_file)
        print(f"#show {name}/0.", file=asp_file)
        if not node.startswith("-"):
            print(
                f":- {name}, {pnml_to_asp('-' + node)}.", file=asp_file
            )  # conflict-freeness
        counter = add_tree(data["function"], data["var"], asp_file, counter)


def add_tree(source: expr, target: expr, asp_file, counter=0):
    """Add the AST of things->target to the ASP program."""
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
            print(f"{starget}.", file=asp_file)
        else:
            print(f"Houston we have a problem with {source}…")
    elif isinstance(source, OrOp):
        if unsafe(source):
            # espresso will not compute minimal implicants
            # but guarantees to remove redundancy
            source, = espresso_exprs(source.to_dnf())
            # we call back add_tree when source is not an OrOp any longer
            if not isinstance(source, OrOp):
                return add_tree(source, target, asp_file, counter)
        source_str = ""
        for s in source.xs:
            if isinstance(s, Literal):
                svs = pnml_to_asp(str(~s))
            else:
                vs = expr(f"aux_{counter}")
                counter = add_tree(s, vs, asp_file, counter + 1)
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
                counter = add_tree(s, target, asp_file, counter)
    else:
        print(f"Houston we have a problem with {source}…")
    return counter


def leaves(expression: expr) -> Set[Literal]:
    """Return all the Litterals in expression."""
    s = set()
    for ex in expression.iter_dfs():
        if isinstance(ex, Literal):
            s.add(ex)
    return s


def unsafe(expression: expr) -> bool:
    """Return true if leaves contain a variable and its negation."""
    for v in leaves(expression):
        if isinstance(v, Variable) and ~v in leaves(expression):
            return True
    return False
