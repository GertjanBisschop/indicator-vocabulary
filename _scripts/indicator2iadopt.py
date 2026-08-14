#!/usr/bin/env python3
"""Project minted indicator YAML into one I-ADOPT Variable assertion per term."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml
from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import OWL, SKOS

IADOPT = Namespace("https://w3id.org/iadopt/ont/")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    with args.data.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    indicators = data.get("indicator_subclasses") or []
    args.out.mkdir(parents=True, exist_ok=True)

    for indicator in indicators:
        graph = build_graph(indicator)
        indicator_id = require_string(indicator, "id")
        output_path = args.out / f"{local_name(indicator_id)}.ttl"
        graph.serialize(destination=output_path, format="turtle")
        print(f"Wrote I-ADOPT assertion -> {output_path}")

    print(f"Projected {len(indicators)} indicator(s) to I-ADOPT assertions")
    return 0


def build_graph(indicator: dict[str, Any]) -> Graph:
    graph = Graph()
    graph.bind("iadopt", IADOPT)
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)
    graph.bind("skos", SKOS)

    variable = uri(require_string(indicator, "id"))
    graph.add((variable, RDF.type, OWL.NamedIndividual))
    graph.add((variable, RDF.type, IADOPT.Variable))

    add_literal(graph, variable, SKOS.prefLabel, indicator.get("name"))
    add_literal(graph, variable, SKOS.definition, indicator.get("description"))
    add_literal(graph, variable, RDFS.comment, indicator.get("remark"))

    for alias in indicator.get("aliases") or []:
        add_literal(graph, variable, SKOS.altLabel, alias)
    if indicator.get("short_name"):
        add_literal(graph, variable, SKOS.altLabel, indicator.get("short_name"))
    if indicator.get("ui_label") and indicator.get("ui_label") != indicator.get("name"):
        add_literal(graph, variable, SKOS.altLabel, indicator.get("ui_label"))

    for translation in indicator.get("translations") or []:
        if translation.get("property_name") == "name":
            add_literal(
                graph,
                variable,
                SKOS.prefLabel,
                translation.get("translated_value"),
                lang=translation.get("language"),
            )

    add_typed_component(
        graph,
        variable,
        IADOPT.hasMatrix,
        indicator.get("matrix"),
        IADOPT.Entity,
    )
    add_typed_component(
        graph,
        variable,
        IADOPT.hasProperty,
        indicator.get("quantity_kind"),
        IADOPT.Property,
    )
    add_typed_component(
        graph,
        variable,
        IADOPT.hasObjectOfInterest,
        indicator.get("biochementity"),
        IADOPT.Entity,
    )

    for constraint in indicator.get("constraints") or []:
        add_constraint(graph, variable, constraint)

    return graph


def add_typed_component(
    graph: Graph,
    variable: URIRef,
    predicate: URIRef,
    value: str | None,
    rdf_type: URIRef,
) -> None:
    if not value:
        return
    node = uri(value)
    graph.add((variable, predicate, node))
    graph.add((node, RDF.type, rdf_type))


def add_constraint(graph: Graph, variable: URIRef, constraint: dict[str, Any]) -> None:
    constraint_id = constraint.get("constraint_id")
    node = uri(constraint_id) if constraint_id else BNode()
    graph.add((variable, IADOPT.hasConstraint, node))
    graph.add((node, RDF.type, IADOPT.Constraint))

    add_literal(graph, node, RDFS.label, constraint.get("name"))
    add_literal(graph, node, RDFS.comment, constraint.get("description"))

    constrains = constraint.get("constrains")
    if constrains:
        graph.add((node, IADOPT.constrains, uri(constrains)))


def add_literal(
    graph: Graph,
    subject: URIRef | BNode,
    predicate: URIRef,
    value: Any,
    lang: str | None = None,
) -> None:
    if value is None or value == "":
        return
    graph.add((subject, predicate, Literal(str(value), lang=lang)))


def require_string(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not value:
        raise ValueError(f"Indicator entry is missing required field '{key}'")
    return str(value)


def uri(value: str) -> URIRef:
    return URIRef(value)


def local_name(value: str) -> str:
    tail = re.split(r"[/#]", value.rstrip("/#"))[-1]
    return re.sub(r"[^A-Za-z0-9_.-]", "_", tail)


if __name__ == "__main__":
    raise SystemExit(main())
