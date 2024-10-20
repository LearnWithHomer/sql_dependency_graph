import click

from sql_dependency_graph.viz import viz


@click.group()
def cli():
    """The CLI for the sql_dependency_graph package that groups the various scripts."""
    pass


cli.add_command(viz, name="viz")
