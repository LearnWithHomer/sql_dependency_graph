from collections import defaultdict
from pathlib import Path
import re
from typing import cast, DefaultDict, Optional, TypeAlias


# Artifact is any location you want to parse in your files.
Artifact: TypeAlias = str
DependencyGraph = DefaultDict[Artifact, list[Artifact]]


def _get_dependencies(sql: str) -> list[Artifact]:
    """
    Params
    ------
    sql : str
        Sql to parse to return dependencies.

    Returns
    -------
    : list[Artifact]
        Dependencies.
    """
    # Note: supports only artifacts surrounded by " or `. Most warehouses
    # support one of these.
    dependency_regex = r'(?i)\b(?:FROM|TABLE|INTO|JOIN|UPDATE|DELETE)\s+[`"](.*?)[`"]'
    return list(set(re.findall(dependency_regex, sql)))


def _convert_path_to_artifact(
    sql_dir: str | Path, artifact_path: str | Path
) -> Artifact:
    """
    Parses {schema}.{artifact} from the path.

    Params
    ------
    artifact_path : str
        Path to artifact.

    Returns
    -------
    : Artifact
        {schema}.{artifact}
    """
    sql_dir = Path(sql_dir)
    artifact_path = Path(artifact_path)
    paths: list[str] = re.findall(f"{str(sql_dir)}/(.*)", str(artifact_path))
    if not paths:
        raise AssertionError(
            "Check your `artifact_path` and `sql_dir`, not finding the `artifact_path`."
        )
    return paths[0].replace("/", ".").replace(".table", "").replace(".sql", "")


def _get_path_lookup(sql_dir: str) -> dict[Artifact, Path]:
    """
    Parameters
    ----------
    sql_dir : str
        Sql directory path.

    Returns
    -------
    : Dict[Artifact, Path]
    """
    sql_paths: list[Path] = list(Path(sql_dir).rglob("*.sql"))
    path_lookup: dict[Artifact, Path] = {
        _convert_path_to_artifact(sql_dir, sql_path): sql_path for sql_path in sql_paths
    }
    return path_lookup


def _create_dependency_graph_helper(
    artifact: Artifact,
    dependencies: list[Artifact],
    dependency_graph: DependencyGraph,
    relationship: str,
) -> DependencyGraph:
    if relationship == "parent":
        for dependency in dependencies:
            dependency_graph[dependency].append(artifact)
    elif relationship == "dependency":
        dependency_graph[artifact] = dependencies
    else:
        raise NotImplementedError("")
    return dependency_graph


def create_dependency_graph(
    sql_dir: str, relationship: str, root_artifact: Optional[Artifact]
) -> dict[Artifact, list[Artifact]]:
    """
    Params
    ------
    sql_dir : str
        Path to sql.
    relationship : str
        In {"parent", "dependency"}.
        "parent" means the arrows will point to all artifacts that use this
        `root_artifact` as a dependency, ie; parent.
        "dependency" will display all of the dependencies of the `root_artifact`.
        In other words, this argument is the direction of the relationship.
    root_artifact : Optional[Artifact]
        If supplied, this argument will specify a root node for the subgraph.

    Returns
    -------
    dependency_graph : DependencyGraph
        A graph structure of dependencies or parents.
    """
    assert relationship in {
        "parent",
        "dependency",
    }, '`relationship` must be in {"parent", "dependency"}'
    if relationship == "parent" and not root_artifact:
        raise NotImplementedError(
            "Must pass a `root_artifact` for the parent relationship."
        )
    path_lookup: dict[Artifact, Path] = _get_path_lookup(sql_dir)
    dependency_graph: DependencyGraph = defaultdict(list)
    artifacts: list[Artifact] = list(path_lookup.keys())
    for artifact in artifacts:
        with open(path_lookup[artifact]) as file:
            sql = file.read()
        dependencies: list[Artifact] = _get_dependencies(sql)
        dependency_graph = _create_dependency_graph_helper(
            artifact, dependencies, dependency_graph, relationship
        )
    if root_artifact:
        # Note: If performance is an issue, consider creating the subgraph
        # first.
        dependency_graph = _create_dependency_subgraph(dependency_graph, root_artifact)
    return cast(DependencyGraph, dependency_graph)


def _create_dependency_subgraph(
    dependency_graph: DependencyGraph, root_artifact: Artifact
) -> DependencyGraph:
    """
    Params
    ------
    dependency_graph : DependencyGraph
        A graph structure of dependencies.
    root_artifact : Artifact
        Artifact you'd like to see dependencies/parents of. {schema}.{artifact}

    Returns
    -------
    dependency_subgraph : DependencyGraph
        Only the artifacts that are a dependency/parent of `root_artifact`
    """
    lookup_artifacts = {root_artifact}
    subgraph_artifacts: list[Artifact] = [root_artifact]
    visited: set = set()
    while lookup_artifacts:
        lookup_artifact = lookup_artifacts.pop()
        if lookup_artifact in dependency_graph.keys():
            lookup_artifacts.update(set(dependency_graph[lookup_artifact]) - visited)
            subgraph_artifacts += dependency_graph[lookup_artifact]
        else:
            subgraph_artifacts.append(lookup_artifact)
        visited.add(lookup_artifact)
    dependency_dict = {
        artifact: dependency_graph[artifact]
        for artifact in subgraph_artifacts
        if artifact in dependency_graph.keys()
    }
    dependency_subgraph: DependencyGraph = defaultdict(list, dependency_dict)
    return dependency_subgraph
