"""Production RACEPULSE dashboard build entrypoint."""

from .production import build_all

if __name__ == "__main__":
    print("=" * 70)
    print("RACEPULSE DASHBOARD BUILDER")
    print("=" * 70)
    build_all()
    print("=" * 70)
    print("Dashboard generation complete.")
    print("=" * 70)

