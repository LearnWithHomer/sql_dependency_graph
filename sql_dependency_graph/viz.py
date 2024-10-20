import logging
from pathlib import Path
import re
from typing import Optional, TypeAlias, TypedDict

import click
import dash
from dash import html
import dash_cytoscape as cyto
import yaml

from sql_dependency_graph.graph import (
    Artifact,
    create_dependency_graph,
    DependencyGraph,
)

log = logging.getLogger(__name__)

DependencyGraphVizElems: TypeAlias = list[dict[str, dict[str, str]]]


class ArtifactType(TypedDict):
    name: str
    pattern: str
    color: str
    shape: str


class GraphConfig(TypedDict):
    artifact_types: list[ArtifactType]


def _load_graph_config(config_path: Path | str) -> GraphConfig:
    """Load artifact types from a YAML config file and validate them."""
    config_path = Path(config_path)
    with open(config_path, "r") as file:
        config: GraphConfig = yaml.safe_load(file)

    _validate_graph_config(config)
    return config


def _validate_graph_config(config: GraphConfig) -> None:
    """Validate the structure and types of the artifact types in the config."""

    if "artifact_types" not in config:
        raise ValueError("Missing key: 'artifact_types' in the configuration.")

    artifact_types = config["artifact_types"]
    if not isinstance(artifact_types, list):
        raise TypeError("'artifact_types' must be a list.")

    for idx, artifact in enumerate(artifact_types):
        if not isinstance(artifact, dict):
            raise TypeError(f"Artifact type at index {idx} must be a dictionary.")

        required_fields = ["name", "pattern", "color", "shape"]
        for field in required_fields:
            if field not in artifact:
                raise ValueError(
                    f"Missing field '{field}' in artifact type at index {idx}."
                )
            if not isinstance(artifact[field], str):
                raise TypeError(
                    f"Field '{field}' in artifact type at index {idx} must be a string."
                )


def _identify_artifact_type(
    artifact: str, root_artifact: str, artifact_types: list[ArtifactType]
) -> str:
    """Determine the artifact type based on regex patterns loaded from the config."""
    if root_artifact == artifact:
        return "root"

    for artifact_type in artifact_types:
        if re.search(artifact_type["pattern"], artifact, re.IGNORECASE):
            return artifact_type["name"]

    return "other"


def _get_unique_artifacts(dependency_graph: DependencyGraph) -> list[Artifact]:
    """
    Gets all artifacts associated with a DependencyGraph.
    """
    dependencies: list[Artifact] = [
        artifact for artifacts in dependency_graph.values() for artifact in artifacts
    ]
    unique_artifacts = set(dependencies) | set(dependency_graph.keys())
    return list(unique_artifacts)


def _create_dependency_viz_elements(
    dependency_graph: DependencyGraph,
    artifact_types: list[ArtifactType],
    root_artifact: Optional[Artifact] = None,
) -> DependencyGraphVizElems:
    """
    Turns the graph structure into the form needed for Dash Cytoscape: https://dash.plotly.com/cytoscape

    Params
    ------
    dependency_graph : DependencyGraph
        A graph structure of dependencies.
    artifact_types : list[ArtifactType]
        Configurations for different artifact type visualizations. See readme
        for options.
    root_artifact : Optional[Artifact]
        Artifact you'd like to see dependencies/parents of.

    Returns
    -------
    dependency_graph_viz_elems : DependencyGraphVizElems
        Structure needed in Dash Cytoscape.
    """
    dependency_graph_viz_elems = []
    artifacts: list[Artifact] = _get_unique_artifacts(dependency_graph)
    for artifact in artifacts:
        try:
            artifact_type = _identify_artifact_type(
                artifact, root_artifact, artifact_types
            )
        except:
            import pdb

            pdb.set_trace()
        dependency_graph_viz_elems.append(
            {
                "data": {
                    "id": f"{artifact}",
                    "label": f"{artifact}",
                    "artifact_type": f"{artifact_type}",
                }
            }
        )
        if artifact in dependency_graph.keys():
            for dependency in dependency_graph[artifact]:
                dependency_graph_viz_elems.append(
                    {"data": {"source": f"{artifact}", "target": f"{dependency}"}}
                )
    return dependency_graph_viz_elems


def _get_config_settings(
    artifact_types: list[ArtifactType],
) -> list[dict[str, str | dict[str, str]]]:
    config_settings: list[dict[str, str | dict[str, str]]] = []
    for artifact_type in artifact_types:
        artifact_name: str = artifact_type["name"]
        artifact_color: str = artifact_type["color"]
        artifact_shape: str = artifact_type["shape"]
        config_settings.append(
            {
                "selector": f'[artifact_type *= "{artifact_name}"]',
                "style": {"background-color": artifact_color, "shape": artifact_shape},
            }
        )
    config_settings += [
        {
            "selector": '[artifact_type *= "root"]',
            "style": {"background-color": "#000000", "shape": "triangle"},
        }
    ]
    return config_settings


@click.command()
@click.option(
    "--sql_dir",
    help="""Path to the sql directory, eg; ../sql. The default option assumes
    you are in the top of the directory""",
    default=".",
)
@click.option(
    "--relationship",
    help="""In {"parent", "dependency"}. Default is "dependency".
        "parent" means the arrows will point to artifacts that use this
        `root_artifact` as a dependency, ie; parent.
        "dependency" will display all of the dependencies of the `root_artifact`.
        """,
    default="dependency",
)
@click.option(
    "--root_artifact",
    help="""The name of the `root_artifact` for the dependency subgraph you'd like to see.
        No `root_artifact` with the "parent" `relationship` is not supported.""",
    default=None,
)
@click.option(
    "--graph_type",
    help="""Graph types can be read about here. I've
        added logic for sensible defaults given the cli options, but you can
        override. See https://blog.js.cytoscape.org/2020/05/11/layouts/""",
    default="default",
)
@click.option(
    "--config_path",
    help="""Path to the config file. See README for options.""",
    default=None,
)
def viz(
    sql_dir: str,
    relationship: str,
    root_artifact: Optional[str],
    graph_type: str,
    config_path: Optional[str],
):
    """
    Displays dependencies as a graph structure in your browswer.

    ### Installing `sql_dependency_graph` package.

    >>> cd path/to/top/level/repository
    >>> pip3 install -r requirements.txt
    >>> pip3 install -e .

    After installing `sql_dependency_graph`, you can run `sql_dependency_graph
    viz --help` to see cli options.


    ### Assumptions and setup.

    1. You need to use table/view object references with a full path separated
    by ".". For example, Databricks calls this {catalog}.{schema}.{artifact}
    and Bigquery calls this {project}.{schema}.{artifact}. It is also
    possible to use just {schema}.{artifact} if you only have one "catalog".
    More details in #3.
    2. Your table/view object references must be surrounded by " or `, which is
    supported by most warehouses. Eg; `{project}.{dataset}.{artifact}`
    3. The path structure of `sql_dir` must match the object references and end
    in ".sql" extension. For example, if the object reference is
    `{catalog}.{schema}.{artifact}` then the path must be
    "{catalog}/{schema}/{artifact}.sql". If the object reference is
    `{schema}.{artifact}`, then the path must be "{schema}/{artifact}.sql"

    Optionally you can add ".table" in the file name prior to ".sql" to denote
    a table.

    ### Checking the cli options.

    >>> sql_dependency_graph --help
    >>> sql_dependency_graph viz --help

    ### Example Useage

    >>> sql_dependency_graph viz --sql_dir bigquery

    Uses defaults for  "dependency" `relationship` (will show all dependencies)
    and sensible `graph_type`.

    >>> sql_dependency_graph viz --sql_dir bigquery relationship dependency --root_artifact {project}.{dataset}.{table}

    Will show a subgraph of "{project}.{dataset}.{table}" dependencies.

    >>> sql_dependency_graph viz --sql_dir bigquery relationship parent --root_artifact {project}.{dataset}.{table}

    Will show a subgraph of "{project}.{dataset}.{table}" parents.
    """
    assert relationship in {"parent", "dependency"}
    if config_path:
        config_path = Path(config_path)
        config: GraphConfig = _load_graph_config(config_path)
        artifact_types: list[ArtifactType] = config["artifact_types"]
    else:
        artifact_types = []
    dependency_graph: DependencyGraph = create_dependency_graph(
        sql_dir, relationship, root_artifact
    )
    dependency_graph_viz_elems: DependencyGraphVizElems = (
        _create_dependency_viz_elements(
            dependency_graph, artifact_types, root_artifact=root_artifact
        )
    )
    if graph_type == "default":
        if root_artifact:
            graph_type = "breadthfirst"
        else:
            graph_type = "concentric"
    if relationship == "parent":
        edge_color = "#FFA500"
    else:
        edge_color = "#C5D3E2"

    # See https://dash.plotly.com/cytoscape for details.
    app = dash.Dash(__name__)
    app.layout = html.Div(
        [
            cyto.Cytoscape(
                id="cytoscape-layout-3",
                elements=dependency_graph_viz_elems,
                style={
                    "width": "100%",
                    "height": "1500px",
                },
                stylesheet=[
                    {
                        "selector": "node",
                        "style": {
                            "shape": "rectangle",
                            "background-color": "lightgrey",
                            "border-color": "black",
                            "border-width": 1,
                            "text-valign": "center",
                            "text-halign": "left",
                            "text-margin-x": -2,
                            "text-rotation": (3.14 * 3 * 0.75),
                            "label": "data(label)",
                            "text-valign": "center",
                            "line-height": "2",
                            "text-wrap": "wrap",
                            "text-justification": "left",
                            "font-size": "20px",
                        },
                    },
                    {
                        "selector": "edge",
                        "style": {
                            "target-arrow-color": edge_color,
                            "target-arrow-shape": "triangle",
                            "line-color": "#C5D3E2",
                            "arrow-scale": 2,
                            "curve-style": "bezier",
                        },
                    },
                ]
                + _get_config_settings(artifact_types),
                layout={"name": graph_type},
            )
        ]
    )

    app.run_server(debug=True)
