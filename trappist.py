"""Compute minimal trap-spaces of a Petri-net encoded Boolean model.

Copyright (C) 2022 Sylvain.Soliman@inria.fr and giang.trinh91@gmail.com

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

import argparse
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as etree
from typing import IO

import networkx as nx


version = "0.1.0"


def read_pnml(fileobj: IO) -> nx.DiGraph:
    """Parse the given file."""
    root = etree.parse(fileobj).getroot()
    if root.tag != "pnml":
        raise ValueError("Currently limited to parsing PNML files")
    net = nx.DiGraph()

    for place in root.findall("./net/place"):
        net.add_node(place.get("id"), name=place.find("./name/value").text)
        # print(place.get("id"), place.find("./name/value").text)

    for transition in root.findall("./net/transition"):
        net.add_node(transition.get("id"))

    for arc in root.findall("./net/arc"):
        net.add_edge(arc.get("source"), arc.get("target"))

    print(net.number_of_nodes(), net.size())
    return net


def write_asp(petri_net: nx.DiGraph, asp_file: IO):
    """Write the ASP program for the maximal conflict-free siphons of petri_net."""
    pass


def solve_asp(asp_filename: str):
    """Run an ASP solver on program asp_file and get the solutions."""
    result = subprocess.run(
        [
            "echo",
            "clingo",
            "--dom-pref=32",
            "--heu=domain",
            "--dom-mod=7",
            asp_filename,
            "0",
        ],
        capture_output=True,
    )
    print(result.stdout)


def main():
    """Read the Petri-net send the output to ASP and print solution."""
    parser = argparse.ArgumentParser(
        description=" ".join(__doc__.splitlines()[:3]) + " GPLv3"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s v{version}".format(version=version),
    )
    parser.add_argument(
        "infile",
        type=argparse.FileType("r", encoding="utf-8"),
        nargs="?",
        default=sys.stdin,
        help="Petri-net (PNML) file",
    )
    args = parser.parse_args()

    petri_net = read_pnml(args.infile)

    with tempfile.NamedTemporaryFile() as asp_file:
        write_asp(petri_net, asp_file)
        solve_asp(asp_file.name)


if __name__ == "__main__":
    main()
