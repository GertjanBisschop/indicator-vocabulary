from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from rdflib import RDF, URIRef


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "_scripts" / "indicator2iadopt.py"
SPEC = spec_from_file_location("indicator2iadopt", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
indicator2iadopt = module_from_spec(SPEC)
SPEC.loader.exec_module(indicator2iadopt)


def test_matrix_and_biochementity_are_typed_as_iadopt_entities() -> None:
    matrix = URIRef("https://w3id.org/peh/terms/Matrix/blood")
    biochementity = URIRef("https://w3id.org/peh/BE-lead")
    variable = URIRef("https://w3id.org/peh/IND-lead-blood")

    graph = indicator2iadopt.build_graph(
        {
            "id": str(variable),
            "name": "Lead in blood",
            "matrix": str(matrix),
            "biochementity": str(biochementity),
        }
    )

    assert (variable, indicator2iadopt.IADOPT.hasMatrix, matrix) in graph
    assert (matrix, RDF.type, indicator2iadopt.IADOPT.Entity) in graph
    assert (variable, indicator2iadopt.IADOPT.hasObjectOfInterest, biochementity) in graph
    assert (biochementity, RDF.type, indicator2iadopt.IADOPT.Entity) in graph
