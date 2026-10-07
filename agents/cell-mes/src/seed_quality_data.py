"""
[DEPRECATED] 품질 관련 샘플 데이터 시딩 스크립트

이 스크립트는 seed_data.py에 통합되었습니다.
품질 데이터(검사계획, 측정결과, SPC, NCR)는 이제 seed_data.py에서 한 번에 생성됩니다.

사용법:
    cd agents/cell-mes
    uv run python -m src.seed_data                    # 전체 데이터 (품질 포함) 생성
    uv run python -m src.seed_data --date 2026-02-10  # 기준일 지정
"""

import warnings


def seed_quality_data():
    """[DEPRECATED] seed_data.py를 사용하세요."""
    warnings.warn(
        "seed_quality_data.py는 deprecated 되었습니다. "
        "seed_data.py에 품질 데이터가 통합되었습니다. "
        "'uv run python -m src.seed_data'를 사용하세요.",
        DeprecationWarning,
        stacklevel=2,
    )


if __name__ == "__main__":
    print("=" * 60)
    print("[DEPRECATED] 이 스크립트는 seed_data.py에 통합되었습니다.")
    print("")
    print("대신 다음 명령을 사용하세요:")
    print("  uv run python -m src.seed_data                    # 전체 데이터 생성")
    print("  uv run python -m src.seed_data --date 2026-02-10  # 기준일 지정")
    print("  uv run python -m src.seed_data --validate         # 검증만")
    print("=" * 60)
