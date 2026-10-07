# src/utils/step_render_worker.py
from __future__ import annotations

import argparse
import logging
import sys
from typing import Tuple

from src.utils.step_render_cadquery import (
    InvalidStepFileError,
    StepCadQueryRenderError,
    render_step_file_vtk,
)

logger = logging.getLogger(__name__)


def _parse_resolution(s: str) -> Tuple[int, int]:
    # e.g. "1920x1080"
    try:
        w, h = s.lower().split("x")
        return int(w), int(h)
    except Exception:
        raise argparse.ArgumentTypeError("resolution must be like 1920x1080")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="step_path", required=True, help="input STEP file path")
    p.add_argument("--out", dest="png_path", required=True, help="output PNG file path")
    p.add_argument("--resolution", type=_parse_resolution, default=(1920, 1080))
    args = p.parse_args()

    try:
        render_step_file_vtk(
            step_file_path=args.step_path,
            output_image_path=args.png_path,
            resolution=args.resolution,
        )
        logger.info("ok")
        return

    except InvalidStepFileError as e:
        sys.stderr.write(f"INVALID_STEP: {e}\n")
        sys.exit(40)  # -> API 400

    except StepCadQueryRenderError as e:
        sys.stderr.write(f"RENDER_ERROR: {e}\n")
        sys.exit(50)  # -> API 500

    except Exception as e:
        sys.stderr.write(f"UNKNOWN_ERROR: {e}\n")
        sys.exit(99)


if __name__ == "__main__":
    main()
