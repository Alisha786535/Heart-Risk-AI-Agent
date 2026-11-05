import csv, hashlib
import pytest
from core import auth


@pytest.fixture(autouse=True)
def _db(tmp_path, monkeypatch):
    monkeypatch.setenv("HEART_DB", str(tmp_path / "a.db"))
    monkeypatch.setattr(auth, "LEGACY_CSV", tmp_path / "users.csv")


def test_hash_is_salted_and_not_sha256():
    h1, h2 = auth.hash_password("longenough1"), auth.hash_password("longenough1")
    assert h1 != h2 and h1.startswith("scrypt$") and hashlib.sha256(b"longenough1").hexdigest() not in h1
    assert auth.verify_password("longenough1", h1) and not auth.verify_password("other", h1)


def test_register_validation():
    assert not auth.register("not-an-email", "A", "longenough1")[0]
    assert not auth.register("a@b.com", "A", "short")[0]
    assert auth.register("a@b.com", "  Ann   Lee ", "longenough1")[0]
    assert not auth.register("A@B.com", "Dup", "longenough1")[0]


def test_legacy_sha256_account_is_upgraded(tmp_path):
    with open(tmp_path / "users.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["email", "name", "password_hash"])
        w.writerow(["old@x.com", "Old User", hashlib.sha256(b"oldpass123").hexdigest()])
    ok, user, _ = auth.authenticate("old@x.com", "oldpass123")
    assert ok and user["name"] == "Old User"
    (tmp_path / "users.csv").unlink()                      # works without the CSV afterwards
    assert auth.authenticate("old@x.com", "oldpass123")[0]
    assert not auth.authenticate("old@x.com", "nope")[0]
