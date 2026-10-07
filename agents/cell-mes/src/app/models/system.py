"""System configuration models."""

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class MiddlewareConfig(Base):
    """Middleware server connection configuration."""

    __tablename__ = "middleware_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)  # Support IPv6
    port: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<MiddlewareConfig(id={self.id}, name='{self.name}', {self.ip_address}:{self.port})>"
        )

    @property
    def base_url(self) -> str:
        """Get the base URL for the middleware server."""
        return f"http://{self.ip_address}:{self.port}"
