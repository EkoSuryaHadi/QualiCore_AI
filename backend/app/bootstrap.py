from .config import settings
from .database import Base, engine


def bootstrap_database() -> None:
    """Optional MVP bootstrap for a fresh hosted PostgreSQL database."""
    if not settings.auto_bootstrap:
        return
    Base.metadata.create_all(bind=engine)
    if settings.seed_demo:
        from .seed import run
        run()
