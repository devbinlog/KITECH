# src/utils/step_render_cadquery.py
from __future__ import annotations

import os
import tempfile
from typing import Tuple


class StepCadQueryRenderError(RuntimeError):
    """렌더링 일반 실패(환경/VTK/렌더 파이프라인 실패 등)"""


class InvalidStepFileError(StepCadQueryRenderError):
    """STEP 파일이 아니거나 손상되어 STEP import 자체가 실패하는 경우"""


def render_step_bytes_to_png_bytes_vtk(
    *,
    step_bytes: bytes,
    resolution: Tuple[int, int] = (1920, 1080),
) -> bytes:
    """
    STEP bytes -> PNG bytes
    (검증된 cadquery + VTK 렌더 파이프라인 사용)

    - 임시 .step 파일을 만들고
    - render_step_file_vtk()로 PNG 파일 생성 후
    - PNG bytes로 반환
    """
    step_path = None
    png_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".step") as f:
            f.write(step_bytes)
            step_path = f.name

        fd, png_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)

        render_step_file_vtk(
            step_file_path=step_path,
            output_image_path=png_path,
            resolution=resolution,
        )

        if not os.path.exists(png_path) or os.path.getsize(png_path) == 0:
            raise StepCadQueryRenderError("렌더링 결과 PNG가 생성되지 않았습니다.")

        with open(png_path, "rb") as f:
            return f.read()

    finally:
        for p in (step_path, png_path):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


def render_step_file_vtk(
    *,
    step_file_path: str,
    output_image_path: str,
    resolution: Tuple[int, int] = (1920, 1080),
) -> None:
    """
    ✅ render_step_cadquery.py의 핵심 렌더 로직 통합본

    - STEP -> cadquery import
    - OCC mesh -> STL 임시
    - VTK offscreen render -> PNG 저장

    실패 유형 분리:
    - STEP import 실패 => InvalidStepFileError (400으로 내려주기 용도)
    - 그 외 렌더 파이프라인 실패 => StepCadQueryRenderError (500)
    """
    try:
        import cadquery as cq
        import vtk
        from vtkmodules.vtkRenderingCore import (
            vtkRenderer,
            vtkRenderWindow,
            vtkActor,
            vtkPolyDataMapper,
        )
        from vtkmodules.vtkCommonColor import vtkNamedColors
        from vtkmodules.vtkFiltersCore import vtkTriangleFilter
        from vtkmodules.vtkRenderingCore import vtkWindowToImageFilter
        from vtkmodules.vtkIOImage import vtkPNGWriter

        from OCP.BRepMesh import BRepMesh_IncrementalMesh
        from OCP.StlAPI import StlAPI_Writer

    except Exception as e:
        raise StepCadQueryRenderError(
            "cadquery/vtk/OCP 의존성이 부족합니다. 환경 설치를 확인하세요."
        ) from e

    # 1) STEP import (여기서 실패하면 '잘못된 STEP 파일'로 본다)
    try:
        result = cq.importers.importStep(step_file_path)
    except Exception as e:
        raise InvalidStepFileError("잘못된 STEP 파일입니다. (STEP import 실패)") from e

    # 2) shape 추출
    try:
        shape = result.val() if hasattr(result, "val") else result
        wrapped = shape.wrapped  # cadquery Shape -> OCP shape
    except Exception as e:
        raise InvalidStepFileError("잘못된 STEP 파일입니다. (shape 추출 실패)") from e

    # 3) 삼각형화 + STL 임시 저장
    tmp_stl = step_file_path + ".tmp.stl"
    try:
        BRepMesh_IncrementalMesh(wrapped, 0.5, True, 0.5, True)
        writer = StlAPI_Writer()
        writer.Write(wrapped, tmp_stl)
    except Exception as e:
        raise StepCadQueryRenderError("STEP -> STL 변환 실패") from e

    try:
        # 4) VTK STL read
        reader = vtk.vtkSTLReader()
        reader.SetFileName(tmp_stl)
        reader.Update()

        # 5) triangle filter
        triangle_filter = vtkTriangleFilter()
        triangle_filter.SetInputConnection(reader.GetOutputPort())
        triangle_filter.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(triangle_filter.GetOutputPort())

        actor = vtkActor()
        actor.SetMapper(mapper)

        colors = vtkNamedColors()
        actor.GetProperty().SetColor(colors.GetColor3d("Silver"))

        renderer = vtkRenderer()
        renderer.AddActor(actor)
        renderer.SetBackground(colors.GetColor3d("White"))

        render_window = vtkRenderWindow()
        render_window.AddRenderer(renderer)
        render_window.SetOffScreenRendering(1)
        render_window.SetSize(resolution[0], resolution[1])

        camera = renderer.GetActiveCamera()
        camera.SetPosition(1, 1, 1)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1)
        renderer.ResetCamera()

        render_window.Render()

        window_to_image_filter = vtkWindowToImageFilter()
        window_to_image_filter.SetInput(render_window)
        window_to_image_filter.Update()

        png_writer = vtkPNGWriter()
        png_writer.SetFileName(output_image_path)
        png_writer.SetInputConnection(window_to_image_filter.GetOutputPort())
        png_writer.Write()

    except Exception as e:
        raise StepCadQueryRenderError("VTK 렌더링 실패") from e

    finally:
        try:
            if os.path.exists(tmp_stl):
                os.remove(tmp_stl)
        except Exception:
            pass
