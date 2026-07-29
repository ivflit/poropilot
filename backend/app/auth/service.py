"""Auth service — signup, login, user lookup. Thin async layer over the ORM."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.passwords import hash_password, verify_password
from app.models import User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def create_user(session: AsyncSession, email: str, password: str) -> User:
    user = User(email=email, password_hash=hash_password(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate(session: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(session, email)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


async def link_riot_id(
    session: AsyncSession, user: User, region: str, name: str, tag: str
) -> User:
    user.riot_region = region
    user.riot_name = name
    user.riot_tag = tag
    await session.commit()
    await session.refresh(user)
    return user
