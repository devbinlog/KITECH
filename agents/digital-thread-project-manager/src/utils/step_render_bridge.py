import os
import subprocess
import tempfile
from typing import Tuple

from .step_render_cadquery import StepCadQueryRenderError, InvalidStepFileError


def render_step_bytes_to_png_bytes_via_renderenv(
    *,
    step_bytes: bytes,
    resolution: Tuple[int, int] = (1920, 1080),
) -> bytes:
    step_path = None
    png_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".step") as f:
            f.write(step_bytes)
            step_path = f.name

        fd, png_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)

        cmd = [
            "conda",
            "run",
            "-n",
            "renderenv",
            "xvfb-run",
            "-a",
            "python",
            "-m",
            "src.utils.step_render_worker",
            "--in",
            step_path,
            "--out",
            png_path,
            "--resolution",
            f"{resolution[0]}x{resolution[1]}",
        ]

        env = os.environ.copy()
        env["DISPLAY"] = env.get("DISPLAY", "")
        env["VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN"] = "1"

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,  # ✅ 여기 연결
        )

        if result.returncode != 0:
            raise StepCadQueryRenderError(
                f"renderenv 실행 실패: rc={result.returncode}, stderr={result.stderr}"
            )

        if not os.path.exists(png_path) or os.path.getsize(png_path) == 0:
            raise StepCadQueryRenderError("PNG 생성 실패")

        with open(png_path, "rb") as f:
            return f.read()

    finally:
        for p in (step_path, png_path):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
