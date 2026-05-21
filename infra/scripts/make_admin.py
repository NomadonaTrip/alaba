"""Bootstrap an admin user.

Run from inside the backend-api container so that env vars and the
alaba package are on PYTHONPATH:

    docker exec -it alaba-backend-api python /app/scripts/make_admin.py --email x

For host-side convenience, the Makefile wraps this with `make make-admin email=...`."""

import argparse
import asyncio
import getpass
import os
import sys

# Allow running this file from inside the container at /app/scripts/make_admin.py
sys.path.insert(0, "/app")

from sqlalchemy import select  # noqa: E402

from alaba.db import AsyncSessionLocal  # noqa: E402
from alaba.models import Admin  # noqa: E402
from alaba.security import hash_password  # noqa: E402


async def create_admin(email: str, password: str) -> None:
    if len(password) < 10:
        print("ERROR: password must be at least 10 characters.", file=sys.stderr)
        sys.exit(1)
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(Admin).where(Admin.email == email))
        if existing.scalar_one_or_none() is not None:
            print(f"ERROR: admin {email!r} already exists.", file=sys.stderr)
            sys.exit(1)
        admin = Admin(email=email, password_hash=hash_password(password))
        db.add(admin)
        await db.commit()
        print(f"Admin created: {email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an Alaba admin user.")
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--password",
        default=None,
        help="Password (if omitted, prompts interactively).",
    )
    args = parser.parse_args()

    password = args.password
    if not password:
        password = getpass.getpass("Password (>= 10 chars): ")
        confirm = getpass.getpass("Confirm: ")
        if password != confirm:
            print("ERROR: passwords don't match.", file=sys.stderr)
            sys.exit(1)

    asyncio.run(create_admin(args.email, password))


if __name__ == "__main__":
    main()
