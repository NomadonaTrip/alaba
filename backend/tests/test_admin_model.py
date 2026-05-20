"""Admin model — import + table shape."""

from alaba.models import Admin


def test_admin_imports():
    assert Admin.__tablename__ == "admins"


def test_admin_columns():
    cols = {c.name for c in Admin.__table__.columns}
    expected = {"id", "email", "password_hash", "created_at", "suspended"}
    assert expected == cols


def test_admin_email_unique():
    col = Admin.__table__.columns["email"]
    assert col.unique is True


def test_admin_in_metadata():
    from alaba.models import Base
    assert "admins" in Base.metadata.tables
