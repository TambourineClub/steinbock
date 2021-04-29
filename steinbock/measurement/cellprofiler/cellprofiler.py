from os import PathLike
from pathlib import Path
from typing import Union

from steinbock import utils

_data_dir = Path(__file__).parent / "data"
_measurement_pipeline_file_template = _data_dir / "cell_measurement.cppipe"


def create_measurement_pipeline(
    measurement_pipeline_file: Union[str, PathLike],
    num_channels: int,
):
    measurement_pipeline_file = Path(measurement_pipeline_file)
    with _measurement_pipeline_file_template.open(mode="r") as f:
        s = f.read()
    s = s.replace("{{NUM_CHANNELS}}", str(num_channels))
    with measurement_pipeline_file.open(mode="w") as f:
        f.write(s)


def measure_objects(
    cellprofiler_binary: str,
    measurement_pipeline_file: Union[str, PathLike],
    input_dir: Union[str, PathLike],
    output_dir: Union[str, PathLike],
    cellprofiler_plugin_dir: Union[str, PathLike, None] = None,
):
    args = [
        cellprofiler_binary,
        "-c",
        "-r",
        "-p",
        str(measurement_pipeline_file),
        "-i",
        str(input_dir),
        "-o",
        str(output_dir),
    ]
    if cellprofiler_plugin_dir is not None:
        args.append("--plugins-directory")
        args.append(str(cellprofiler_plugin_dir))
    return utils.run_captured(args)
