"""Models import + table-existence smoke tests."""

from alaba.models import (
    Admin,
    AdminAction,
    Base,
    Film,
    License,
    OtpCode,
    Payout,
    Producer,
    Rating,
    User,
    UserDevice,
)


def test_all_models_import():
    """All 10 models can be imported from alaba.models."""
    assert Admin.__tablename__ == "admins"
    assert User.__tablename__ == "users"
    assert UserDevice.__tablename__ == "user_devices"
    assert OtpCode.__tablename__ == "otp_codes"
    assert Producer.__tablename__ == "producers"
    assert Film.__tablename__ == "films"
    assert License.__tablename__ == "licenses"
    assert Rating.__tablename__ == "ratings"
    assert Payout.__tablename__ == "payouts"
    assert AdminAction.__tablename__ == "admin_actions"


def test_metadata_lists_all_tables():
    table_names = set(Base.metadata.tables.keys())
    expected = {
        "admins",
        "users",
        "user_devices",
        "otp_codes",
        "producers",
        "films",
        "licenses",
        "ratings",
        "payouts",
        "admin_actions",
    }
    assert expected == table_names


def test_user_has_no_device_id_column():
    """Spec amendment: users.device_id is dropped in favor of user_devices."""
    cols = {c.name for c in User.__table__.columns}
    assert "device_id" not in cols
    assert "phone" in cols
    assert "phone_verified" in cols
    assert "suspended" in cols


def test_user_device_columns():
    cols = {c.name for c in UserDevice.__table__.columns}
    expected = {
        "id",
        "user_id",
        "device_id",
        "display_name",
        "model",
        "platform",
        "activated_at",
        "deactivated_at",
        "last_seen_at",
    }
    assert expected <= cols


def test_license_has_payment_ref_unique():
    """licenses.payment_ref must be UNIQUE for webhook idempotency."""
    col = License.__table__.columns["payment_ref"]
    assert col.unique is True
