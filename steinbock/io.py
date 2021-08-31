import numpy as np
import os
import pandas as pd
import tifffile

from os import PathLike
from pathlib import Path
from typing import List, Optional, Sequence, Union


img_dtype = np.dtype(os.environ.get("STEINBOCK_IMG_DTYPE", "float32"))
mask_dtype = np.dtype(os.environ.get("STEINBOCK_MASK_DTYPE", "uint16"))


def as_path_with_suffix(
    path: Union[str, PathLike], suffix: str, replace_ome_suffix: bool = True
) -> Path:
    path = Path(path)
    if replace_ome_suffix and path.name.endswith(".ome.tiff"):
        path = path.with_name(path.name[:-9] + ".tiff")
    return path.with_suffix(suffix)


def to_dtype(src: np.ndarray, dst_dtype: np.dtype) -> np.ndarray:
    if src.dtype == dst_dtype:
        return src
    src_is_int = np.issubdtype(src.dtype, np.integer)
    dst_is_int = np.issubdtype(dst_dtype, np.integer)
    if not src_is_int and dst_is_int:
        src = np.around(src)
    if src_is_int:
        src_info = np.iinfo(src.dtype)
    else:
        src_info = np.finfo(src.dtype)
    if dst_is_int:
        dst_info = np.iinfo(dst_dtype)
    else:
        dst_info = np.finfo(dst_dtype)
    if src_info.min < dst_info.min or src_info.max > dst_info.max:
        src = np.clip(src, dst_info.min, dst_info.max)
    return src.astype(dst_dtype)


def _list_related_files(
    base_files: Sequence[Union[str, PathLike]],
    related_dir: Union[str, PathLike],
    related_suffix: str,
) -> List[Path]:
    related_files = []
    for base_file in base_files:
        related_file = as_path_with_suffix(
            Path(related_dir) / Path(base_file).name, related_suffix
        )
        if not related_file.exists():
            raise FileNotFoundError(related_file)
        related_files.append(related_file)
    return related_files


def read_panel(
    panel_stem: Union[str, PathLike], kept_only: bool = True
) -> pd.DataFrame:
    panel_file = as_path_with_suffix(panel_stem, ".csv")
    panel = pd.read_csv(
        panel_file,
        sep=",|;",
        dtype={
            "channel": pd.StringDtype(),
            "name": pd.StringDtype(),
            "keep": pd.BooleanDtype(),
        },
        engine="python",
        true_values=["1"],
        false_values=["0"],
    )
    for required_col in ("channel", "name"):
        if required_col not in panel:
            raise ValueError(
                f"Missing '{required_col}' column in {panel_file}"
            )
    for notnan_col in ("channel", "keep"):
        if notnan_col in panel and panel[notnan_col].isna().any():
            raise ValueError(
                f"Missing values for '{notnan_col}' in {panel_file}"
            )
    for unique_col in ("channel", "name"):
        if unique_col in panel:
            if panel[unique_col].dropna().duplicated().any():
                raise ValueError(
                    f"Duplicated values for '{unique_col}' in {panel_file}"
                )
    if kept_only and "keep" in panel:
        panel = panel.loc[panel["keep"].astype(bool), :]
    return panel


def write_panel(panel: pd.DataFrame, panel_stem: Union[str, PathLike]) -> Path:
    panel_file = as_path_with_suffix(panel_stem, ".csv")
    panel = panel.copy()
    for col in panel.columns:
        if panel[col].convert_dtypes().dtype == pd.BooleanDtype():
            panel[col] = panel[col].astype(pd.UInt8Dtype())
    panel.to_csv(panel_file, index=False)
    return panel_file


def list_image_files(
    img_dir: Union[str, PathLike],
    base_files: Optional[Sequence[Union[str, PathLike]]] = None,
) -> List[Path]:
    if base_files is not None:
        return _list_related_files(base_files, img_dir, ".tiff")
    return sorted(Path(img_dir).rglob("*.tiff"))


def read_image(
    img_stem: Union[str, PathLike], ignore_dtype: bool = False
) -> np.ndarray:
    img_file = as_path_with_suffix(img_stem, ".tiff", replace_ome_suffix=False)
    img = tifffile.imread(img_file)
    while img.ndim > 3 and img.shape[0] == 1:
        img = img.sqeeze(axis=0)
    while img.ndim > 3 and img.shape[-1] == 1:
        img = img.sqeeze(axis=img.ndim - 1)
    if img.ndim == 2:
        img = img[np.newaxis, :, :]
    elif img.ndim != 3:
        raise ValueError(f"Unsupported number of image dimensions: {img_file}")
    if not ignore_dtype:
        img = to_dtype(img, img_dtype)
    return img


def write_image(
    img: np.ndarray, img_stem: Union[str, PathLike], ignore_dtype: bool = False
) -> Path:
    if not ignore_dtype:
        img = to_dtype(img, img_dtype)
    img_file = as_path_with_suffix(img_stem, ".tiff")
    tifffile.imwrite(img_file, data=img, imagej=True)
    return img_file


def list_mask_files(
    mask_dir: Union[str, PathLike],
    base_files: Optional[Sequence[Union[str, PathLike]]] = None,
) -> List[Path]:
    if base_files is not None:
        return _list_related_files(base_files, mask_dir, ".tiff")
    return sorted(Path(mask_dir).rglob("*.tiff"))


def read_mask(mask_stem: Union[str, PathLike]) -> np.ndarray:
    mask_file = as_path_with_suffix(mask_stem, ".tiff")
    mask = tifffile.imread(mask_file)
    while mask.ndim > 2 and mask.shape[0] == 1:
        mask = mask.sqeeze(axis=0)
    while mask.ndim > 2 and mask.shape[-1] == 1:
        mask = mask.sqeeze(axis=mask.ndim - 1)
    if mask.ndim != 2:
        raise ValueError(f"Unsupported number of mask dimensions: {mask_file}")
    return to_dtype(mask, mask_dtype)


def write_mask(mask: np.ndarray, mask_stem: Union[str, PathLike]) -> Path:
    mask = to_dtype(mask, mask_dtype)
    mask_file = as_path_with_suffix(mask_stem, ".tiff")
    tifffile.imwrite(mask_file, data=mask, imagej=True)
    return mask_file


def list_data_files(
    data_dir: Union[str, PathLike],
    base_files: Optional[Sequence[Union[str, PathLike]]] = None,
) -> List[Path]:
    if base_files is not None:
        return _list_related_files(base_files, data_dir, ".csv")
    return sorted(Path(data_dir).rglob("*.csv"))


def read_data(data_stem: Union[str, PathLike]) -> pd.DataFrame:
    data_file = as_path_with_suffix(data_stem, ".csv")
    return pd.read_csv(data_file, index_col="Object")


def write_data(
    data: pd.DataFrame, data_stem: Union[str, PathLike], copy: bool = True
) -> Path:
    data_file = as_path_with_suffix(data_stem, ".csv")
    if copy:
        data = data.reset_index()
    else:
        data.reset_index(inplace=True)
    data.to_csv(data_file, index=False)
    return data_file


def list_distances_files(
    dists_dir: Union[str, PathLike],
    base_files: Optional[Sequence[Union[str, PathLike]]] = None,
) -> List[Path]:
    if base_files is not None:
        return _list_related_files(base_files, dists_dir, ".csv")
    return sorted(Path(dists_dir).rglob("*.csv"))


def read_distances(dists_stem: Union[str, PathLike]) -> pd.DataFrame:
    dists_file = as_path_with_suffix(dists_stem, ".csv")
    dists = pd.read_csv(dists_file, index_col="Object")
    dists.index = dists.index.astype(mask_dtype)
    dists.columns = dists.columns.astype(mask_dtype)
    return dists


def write_distances(
    dists: pd.DataFrame, dists_stem: Union[str, PathLike], copy: bool = False
) -> Path:
    dists_file = as_path_with_suffix(dists_stem, ".csv")
    dists.index.name = "Object"
    dists.index = dists.index.astype(mask_dtype)
    dists.columns.name = "Object"
    dists.columns = dists.columns.astype(mask_dtype)
    dists.to_csv(dists_file)
    return dists_file


def list_graph_files(
    graph_dir: Union[str, PathLike],
    base_files: Optional[Sequence[Union[str, PathLike]]] = None,
) -> List[Path]:
    if base_files is not None:
        return _list_related_files(base_files, graph_dir, ".csv")
    return sorted(Path(graph_dir).rglob("*.csv"))


def read_graph(graph_stem: Union[str, PathLike]) -> pd.DataFrame:
    graph_file = as_path_with_suffix(graph_stem, ".csv")
    return pd.read_csv(
        graph_file, usecols=["Object1", "Object2"], dtype=mask_dtype,
    )


def write_graph(graph: pd.DataFrame, graph_stem: Union[str, PathLike]) -> Path:
    graph_file = as_path_with_suffix(graph_stem, ".csv")
    graph = graph.loc[:, ["Object1", "Object2"]].astype(mask_dtype)
    graph.to_csv(graph_file, index=False)
    return graph_file