import os


def get_env_or_default(key: str, default: str) -> str:
    """
    환경변수를 우선 읽고 없으면 기본값 반환
    """
    return os.getenv(key, default)
