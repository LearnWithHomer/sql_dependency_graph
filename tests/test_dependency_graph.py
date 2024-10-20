from typing import Dict, Set
from pathlib import Path
import os

import pytest

from sql_dependency_graph.graph import DependencyGraph, Artifact


def _dependency_graph_vals_to_set(
    dependency_graph: DependencyGraph,
) -> Dict[Artifact, Set[Artifact]]:
    ret = {}
    for view, dependency in dependency_graph.items():
        ret[view] = set(dependency_graph[view])
    return ret


def test_get_dependencies():
    """Check we are returning the correct number of dependencies"""
    from sql_dependency_graph.graph import _get_dependencies

    fake_dependencies = [
        "bigdata.master_tables.order",
        "bigdata.master_tables.subscription",
        "bigdata.master_tables.cat",
        "bigdata.master_tables.dog",
        "bigdata.master_tables.lemur",
        "bigdata.master_tables.bird",
    ]
    sql = f"""
        select * from `{fake_dependencies[0]}`
        left join `{fake_dependencies[1]}`
        table `{fake_dependencies[4]}`
        DELETE `{fake_dependencies[3]}`
        uPDate `{fake_dependencies[2]}`
        ads into "{fake_dependencies[5]}"
        """
    found_dependencies: list[Artifact] = _get_dependencies(sql)
    assert set(fake_dependencies) == set(found_dependencies)


def test_convert_path_to_artifact():
    """Check correct parsing."""
    from sql_dependency_graph.graph import _convert_path_to_artifact

    sql_dir = "tests/.test_data"
    fake_path: Path = Path(f"{sql_dir}/master_views/customer.sql")
    view: Artifact = _convert_path_to_artifact(sql_dir, fake_path)
    assert view == "master_views.customer"
    fake_path: Path = Path(f"{sql_dir}/master_tables/customer.table.sql")
    view: Artifact = _convert_path_to_artifact(sql_dir, fake_path)
    assert view == "master_tables.customer"
    with pytest.raises(AssertionError):
        fake_path: Path = Path("master_views/customer.sql")
        view: Artifact = _convert_path_to_artifact(sql_dir, fake_path)
    with pytest.raises(AssertionError):
        fake_path: Path = Path("master_views/customer.txt")
        view: Artifact = _convert_path_to_artifact(sql_dir, fake_path)


def test_get_path_lookup():
    """"""
    from sql_dependency_graph.graph import _get_path_lookup

    views_paths: Dict[Artifact, Path] = _get_path_lookup(Path("tests/.test_data"))
    assert set(views_paths.keys()) == set(
        [
            "master_views.customer",
            "master_views.package",
            "master_tables.package",
            "master_tables.customer",
        ]
    )
    assert views_paths.values()
    for path in views_paths.values():
        assert os.path.exists(path)


def test_identify_artifact_type():
    """"""
    from sql_dependency_graph.viz import (
        ArtifactType,
        GraphConfig,
        _identify_artifact_type,
        _load_graph_config,
    )

    config_path = "tests/.test_data/config.yaml"
    config_path = Path(config_path)
    config: GraphConfig = _load_graph_config(config_path)
    artifact_types: list[ArtifactType] = config["artifact_types"]
    assert (
        _identify_artifact_type("master_view.customer", None, artifact_types)
        == "master"
    )
    assert (
        _identify_artifact_type("nextgen_liveprod.test", None, artifact_types)
        == "source"
    )
    assert (
        _identify_artifact_type("google_sheet.FBA Skus", None, artifact_types)
        == "google sheet"
    )
    assert (
        _identify_artifact_type("databricks.some nonsense", None, artifact_types)
        == "databricks"
    )
    assert _identify_artifact_type("cat", "cat", artifact_types) == "root"
    assert _identify_artifact_type("", "cat", []) == "other"
    # TODO
    pass


def test_create_dependency_graph_1():
    from sql_dependency_graph.graph import (
        create_dependency_graph,
    )

    sql_dir = Path("tests/.test_data")
    dependency_graph: DependencyGraph = create_dependency_graph(
        sql_dir, "dependency", root_artifact=None
    )
    assert _dependency_graph_vals_to_set(dependency_graph) == {
        "master_views.customer": set(
            [
                "master_tables.subscription",
                "master_tables.package",
            ]
        ),
        "master_views.package": set(["nexgen_liveprod.test"]),
        "master_tables.package": set([]),
        "master_tables.customer": set([]),
    }


def test_create_dependency_graph_2():
    from sql_dependency_graph.graph import (
        create_dependency_graph,
    )

    sql_dir = Path("tests/.test_data")
    dependency_graph: DependencyGraph = create_dependency_graph(
        sql_dir, "parent", root_artifact="master_tables.package"
    )
    assert _dependency_graph_vals_to_set(dependency_graph) == {
        "master_tables.package": {"master_views.customer"}
    }


def test_create_dependency_subgraph():
    from sql_dependency_graph.graph import (
        create_dependency_graph,
        _create_dependency_subgraph,
    )

    sql_dir = Path("tests/.test_data")
    dependency_graph: DependencyGraph = create_dependency_graph(
        sql_dir, "dependency", root_artifact=None
    )
    dependency_subgraph: DependencyGraph = _create_dependency_subgraph(
        dependency_graph, "master_views.customer"
    )
    assert _dependency_graph_vals_to_set(dependency_subgraph) == {
        "master_views.customer": set(
            [
                "master_tables.subscription",
                "master_tables.package",
            ]
        ),
        "master_tables.package": set([]),
    }


def test_get_unique_artifacts():
    from sql_dependency_graph.viz import _get_unique_artifacts

    dependency_graph: DependencyGraph = {
        "master_views.customer": [
            "master_tables.subscription",
            "master_tables.package",
        ],
        "master_views.package": ["nexgen_liveprod.test"],
        "master_tables.package": [],
    }
    unique_artifacts_test: list[Artifact] = [
        "master_views.customer",
        "master_tables.subscription",
        "master_tables.package",
        "master_views.package",
        "nexgen_liveprod.test",
    ]
    unique_artifacts: list[Artifact] = _get_unique_artifacts(dependency_graph)
    assert set(unique_artifacts_test) == set(unique_artifacts)
