# Sql Dependency Graph

Displays dependencies as a graph structure in your browswer.

## Why?

At Begin, we are faced with the challenge of consolidating many legacy warehouses. Not all warehouses have dependency visualization tooling, and if they do, they are not the same tool. In addition, they are generally not interactive or able to run locally. This Sql Dependency Graph tool is a simple tool that supports arbitrary sql/warehouses, if you can organize your sql files in the way described below. 

### Installing `sql_dependency_graph` package.

Recommended to use a [virtual environment](https://docs.python.org/3/library/venv.html)
``` bash
cd path/to/top/level/repository
pip3 install -r requirements.txt
pip3 install -e .
```

After installing `sql_dependency_graph`, you can run `sql_dependency_graph
viz --help` to see cli options.


### Assumptions and setup.

1. You need to use table/view object references with a full path separated
by ".". For example, Databricks calls this ````{catalog}.{schema}.{artifact}````
and Bigquery calls this ````{project}.{schema}.{artifact}````. It is also
possible to use just ````{schema}.{artifact}```` if you only have one "catalog".
More details in #3.
2. Your table/view object references must be surrounded by " or \`, which is
supported by most warehouses. Eg; ````{project}.{dataset}.{artifact}````
3. The path structure of `sql_dir` must match the object references and end
in ".sql" extension. For example, if the object reference is
`"{catalog}.{schema}.{artifact}"` then the path must be
"{catalog}/{schema}/{artifact}.sql". If the object reference is ````{schema}.{artifact}````,
then the path must be "{schema}/{artifact}.sql"
4. The relationship between table/view and file path should be 1:1. Unfortunately this means
having multiple create statements within one file or having multiple jobs writing to one table
will not work. The former could be solved by re-organizing code.

Optionally you can add ".table" in the file name prior to ".sql" to denote
a table.

### Configurations

If you want to add color/shape distinctions to your graph nodes, you can add a configuration yaml file.

For example, the following yaml adds the following node styles if the `pattern` is found in the object reference.

```
artifact_types:
  - name: "source"
    pattern: "magento|nextgen"
    color: "#FF4136"
    shape: "rectangle"

  - name: "google sheet"
    pattern: "google"
    color: "#00FF00"
    shape: "triangle"

  - name: "databricks"
    pattern: "databricks"
    color: "#00FF00"
    shape: "circle"
```

### Checking the cli options.

```
sql_dependency_graph --help 
sql_dependency_graph viz --help
```

### Example Useage

```
sql_dependency_graph viz --sql_dir bigquery
```

Uses defaults for  "dependency" `relationship` (will show all dependencies)
and sensible `graph_type`.

```
sql_dependency_graph viz --sql_dir bigquery relationship dependency --root_artifact {project}.{dataset}.{table}
```

Will show a subgraph of `{project}.{dataset}.{table}` dependencies.

```
sql_dependency_graph viz --sql_dir bigquery relationship parent --root_artifact {project}.{dataset}.{table}
```

Will show a subgraph of `{project}.{dataset}.{table}` parents.

### Tests

Run tests with
``` bash
pytest
```

## Future Enhancements & Contribution Requests

- [ ] Add column to the CLI options to trace column transformations.
