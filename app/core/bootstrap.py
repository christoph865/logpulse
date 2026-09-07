"""Bootstrap a default admin user from environment configuration."""
import logging

from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.db import async_session_maker
from app.models import User

logger = logging.getLogger(__name__)


async def ensure_admin_user() -> None:
    """Create or promote the configured admin user if ADMIN_PASSWORD is set.

    No-op when ADMIN_PASSWORD is empty, so this is safe to run on every startup.
    """
    if not settings.ADMIN_PASSWORD:
        logger.info("ADMIN_PASSWORD not set; skipping admin bootstrap")
        return

    async with async_session_maker() as db:
        result = await db.execute(select(User).filter(User.username == settings.ADMIN_USERNAME))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                is_admin=1,
                is_active=1,
            )
            db.add(user)
            await db.commit()
            logger.info(f"Bootstrap admin user created: {settings.ADMIN_USERNAME}")
        elif not user.is_admin or not user.is_active:
            user.is_admin = 1
            user.is_active = 1
            await db.commit()
            logger.info(f"Bootstrap admin user promoted: {settings.ADMIN_USERNAME}")
