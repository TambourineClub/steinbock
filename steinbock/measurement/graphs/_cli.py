import click

from pathlib import Path

from steinbock import cli, io
from steinbock.measurement.graphs import graphs


@click.group(
    name="graphs",
    cls=cli.OrderedClickGroup,
    help="Construct spatial object neighborhood graphs",
)
def graphs_cmd():
    pass


@graphs_cmd.command(
    help="Construct directed spatial k-nearest neighbor graphs",
)
@click.option(
    "--dists",
    "dists_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_dists_dir,
    show_default=True,
    help="Path to the object distances directory",
)
@click.option(
    "--k",
    "k",
    type=click.INT,
    required=True,
    help="Number of neighbors per object",
)
@click.option(
    "--dest",
    "graph_dir",
    type=click.Path(file_okay=False),
    default=cli.default_graph_dir,
    show_default=True,
    help="Path to the object graph output directory",
)
def knn(dists_dir, k, graph_dir):
    graph_dir = Path(graph_dir)
    graph_dir.mkdir(exist_ok=True)
    dists_files = io.list_distances(dists_dir)
    it = graphs.construct_knn_graphs(dists_files, k)
    for dists_file, g in it:
        graph_file = io.write_graph(g, graph_dir / Path(dists_file).stem)
        click.echo(graph_file)
        del g


@graphs_cmd.command(
    help="Construct undirected graphs by thresholding on object distances",
)
@click.option(
    "--dists",
    "dists_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_dists_dir,
    show_default=True,
    help="Path to the object distances directory",
)
@click.option(
    "--thres",
    "dist_thres",
    type=click.FLOAT,
    required=True,
    help="Object distance threshold",
)
@click.option(
    "--dest",
    "graph_dir",
    type=click.Path(file_okay=False),
    default=cli.default_graph_dir,
    show_default=True,
    help="Path to the object graph output directory",
)
def dist(dists_dir, dist_thres, graph_dir):
    graph_dir = Path(graph_dir)
    graph_dir.mkdir(exist_ok=True)
    dists_files = io.list_distances(dists_dir)
    it = graphs.construct_distance_graphs(dists_files, dist_thres)
    for dists_file, g in it:
        graph_file = io.write_graph(g, graph_dir / Path(dists_file).stem)
        click.echo(graph_file)
        del g
