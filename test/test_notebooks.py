"""Opt-in end-to-end test for the companion bomwater notebooks."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest


pytestmark = pytest.mark.notebook_bom

NOTEBOOK_REPOSITORY = (
    "https://github.com/csiro-hydroinformatics/bomwater-notebook.git"
)
KERNEL_NAME = "pybomwater-notebooks"
REQUIRED_MODULES = {
    "cftime": "cftime",
    "geopandas": "geopandas",
    "ipykernel": "ipykernel",
    "ipyleaflet": "ipyleaflet",
    "ipywidgets": "ipywidgets",
    "matplotlib": "matplotlib",
    "nbconvert": "nbconvert",
    "nbformat": "nbformat",
    "netCDF4": "netCDF4",
    "pint": "pint",
    "pint-xarray": "pint_xarray",
    "plotly": "plotly",
    "sidecar": "sidecar",
    "xarray": "xarray",
}


def _positive_timeout(name, default):
    raw_value = os.environ.get(name, str(default))
    try:
        value = int(raw_value)
    except ValueError:
        pytest.fail(f"{name} must be a positive integer, got {raw_value!r}")
    if value <= 0:
        pytest.fail(f"{name} must be a positive integer, got {raw_value!r}")
    return value


def _require_notebook_runtime():
    missing = [
        distribution
        for distribution, module in REQUIRED_MODULES.items()
        if importlib.util.find_spec(module) is None
    ]
    if missing:
        pytest.fail(
            "notebook test dependencies are missing: "
            f"{', '.join(sorted(missing))}; install them with "
            f"{sys.executable} -m pip install -r requirements-notebooks.txt"
        )
    if shutil.which("git") is None:
        pytest.fail("git is required to clone the notebook repository")


def _write_kernelspec(jupyter_data_dir):
    kernelspec_dir = jupyter_data_dir / "kernels" / KERNEL_NAME
    kernelspec_dir.mkdir(parents=True)
    kernelspec = {
        "argv": [
            sys.executable,
            "-m",
            "ipykernel_launcher",
            "-f",
            "{connection_file}",
        ],
        "display_name": "pybomwater notebook tests",
        "language": "python",
    }
    (kernelspec_dir / "kernel.json").write_text(
        json.dumps(kernelspec),
        encoding="utf-8",
    )


def _failure_output(command, result):
    return (
        f"command failed with exit code {result.returncode}:\n"
        f"{' '.join(command)}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def _executed_notebook_errors(path):
    import nbformat

    with path.open(encoding="utf-8") as notebook_file:
        notebook = nbformat.read(notebook_file, as_version=4)

    code_cells = [
        (index, cell)
        for index, cell in enumerate(notebook.cells)
        if cell.cell_type == "code"
    ]
    errors = []
    unexecuted = [
        str(index)
        for index, cell in code_cells
        if cell.execution_count is None
    ]
    if unexecuted:
        errors.append(f"unexecuted code cells: {', '.join(unexecuted)}")

    caught_processing_failures = []
    for index, cell in code_cells:
        for output in cell.get("outputs", []):
            if output.output_type == "error":
                errors.append(
                    f"cell {index}: {output.ename}: {output.evalue}"
                )
            if output.output_type == "stream":
                text = output.get("text", "")
                if "Processing failed with system info:" in text:
                    caught_processing_failures.append(str(index))
    if caught_processing_failures:
        errors.append(
            "notebook caught internal processing failures in cells: "
            f"{', '.join(caught_processing_failures)}"
        )
    return errors


def test_clone_and_execute_notebooks(tmp_path):
    """Clone and execute every companion notebook with the current Python."""
    _require_notebook_runtime()
    clone_timeout = _positive_timeout(
        "PYBOMWATER_NOTEBOOK_CLONE_TIMEOUT",
        300,
    )
    notebook_timeout = _positive_timeout(
        "PYBOMWATER_NOTEBOOK_TIMEOUT",
        1200,
    )
    cell_timeout = _positive_timeout(
        "PYBOMWATER_NOTEBOOK_CELL_TIMEOUT",
        600,
    )

    repository = os.environ.get(
        "PYBOMWATER_NOTEBOOK_REPOSITORY",
        NOTEBOOK_REPOSITORY,
    )
    clone_dir = tmp_path / "bomwater-notebook"
    clone_command = [
        "git",
        "clone",
        "--depth=1",
        "--no-tags",
        repository,
        str(clone_dir),
    ]
    try:
        clone_result = subprocess.run(
            clone_command,
            capture_output=True,
            text=True,
            timeout=clone_timeout,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(
            f"cloning {repository} exceeded {clone_timeout} seconds"
        )
    if clone_result.returncode:
        pytest.fail(_failure_output(clone_command, clone_result))

    notebooks = sorted(clone_dir.glob("*.ipynb"))
    assert notebooks, f"no notebooks found in cloned repository {repository}"

    runtime_dir = tmp_path / "runtime"
    executed_dir = tmp_path / "executed"
    executed_dir.mkdir()
    jupyter_data_dir = runtime_dir / "jupyter-data"
    _write_kernelspec(jupyter_data_dir)

    project_root = Path(__file__).resolve().parents[1]
    python_path = [str(project_root)]
    if os.environ.get("PYTHONPATH"):
        python_path.append(os.environ["PYTHONPATH"])

    execution_env = os.environ.copy()
    execution_env.update(
        {
            "IPYTHONDIR": str(runtime_dir / "ipython"),
            "JUPYTER_CONFIG_DIR": str(runtime_dir / "jupyter-config"),
            "JUPYTER_DATA_DIR": str(jupyter_data_dir),
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": str(runtime_dir / "matplotlib"),
            "PYDEVD_DISABLE_FILE_VALIDATION": "1",
            "PYTHONPATH": os.pathsep.join(python_path),
            "XDG_CACHE_HOME": str(runtime_dir / "xdg-cache"),
        }
    )

    failures = []
    for notebook in notebooks:
        output_path = executed_dir / f"{notebook.stem}.executed.ipynb"
        command = [
            sys.executable,
            "-m",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            str(notebook),
            f"--output={output_path.name}",
            f"--output-dir={executed_dir}",
            f"--ExecutePreprocessor.kernel_name={KERNEL_NAME}",
            f"--ExecutePreprocessor.timeout={cell_timeout}",
        ]
        started = time.perf_counter()
        print(f"\nExecuting {notebook.name}")
        try:
            result = subprocess.run(
                command,
                cwd=clone_dir,
                env=execution_env,
                capture_output=True,
                text=True,
                timeout=notebook_timeout,
            )
        except subprocess.TimeoutExpired as error:
            failures.append(
                f"{notebook.name} exceeded {notebook_timeout} seconds; "
                f"stdout:\n{error.stdout or ''}\n"
                f"stderr:\n{error.stderr or ''}"
            )
            continue

        duration = time.perf_counter() - started
        if result.returncode:
            failures.append(
                f"{notebook.name}: {_failure_output(command, result)}"
            )
            continue
        if not output_path.is_file():
            failures.append(
                f"{notebook.name}: nbconvert did not create {output_path}"
            )
            continue

        notebook_errors = _executed_notebook_errors(output_path)
        if notebook_errors:
            failures.append(
                f"{notebook.name}: {'; '.join(notebook_errors)}"
            )
            continue
        print(f"Completed {notebook.name} in {duration:.1f} seconds")

    processing_log = clone_dir / "tmp5a.log"
    if processing_log.is_file():
        log_text = processing_log.read_text(
            encoding="utf-8",
            errors="replace",
        )
        if "Processing failed with system info:" in log_text:
            failures.append(
                f"{processing_log.name} contains caught processing failures"
            )

    assert not failures, "\n\n".join(failures)
