#!/usr/bin/env python3
"""Mint a development JWT for HorizonAI API access."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth.jwt import create_access_token


def main() -> None:
    parser = argparse.ArgumentParser(description="Mint a HorizonAI dev JWT")
    parser.add_argument("subject", nargs="?", default="operator", help="JWT subject (username)")
    parser.add_argument("--role", default="operator", help="Role claim")
    parser.add_argument("--minutes", type=int, default=60, help="Token lifetime in minutes")
    args = parser.parse_args()

    if not os.environ.get("AUTH_JWT_SECRET"):
        print("AUTH_JWT_SECRET must be set in the environment or backend/.env", file=sys.stderr)
        sys.exit(1)

    token = create_access_token(args.subject, expires_minutes=args.minutes, role=args.role)
    print(token)


if __name__ == "__main__":
    main()
