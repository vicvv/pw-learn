"""Settings that change between environments (local, staging, production).

Values come from environment variables, with safe defaults. A .env file in the
repo root can set them too, without exporting anything in the terminal.
"""
import os
from pathlib import Path

DEFAULT_TODO_URL = "https://demo.playwright.dev/todomvc/"

# saucedemo.com publishes these on its own login page, so they are not secrets.
# A real application's credentials must come from the environment only.
DEMO_USER = "standard_user"
DEMO_PASSWORD = "secret_sauce"


def todo_url() -> str:
    """The TodoMVC address: TODO_URL if it is set, otherwise the public demo."""
    return os.environ.get("TODO_URL", DEFAULT_TODO_URL)


def shop_user() -> str:
    """The shop username: SHOP_USER if it is set, otherwise the public demo user."""
    return os.environ.get("SHOP_USER", DEMO_USER)


def shop_password() -> str:
    """The shop password: SHOP_PASSWORD if it is set, otherwise the public demo one."""
    return os.environ.get("SHOP_PASSWORD", DEMO_PASSWORD)


def read_env_file(path) -> dict:
    """Read KEY=VALUE lines from a file. Blank lines and # comments are ignored."""
    values = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_env_file(path=".env") -> dict:
    """Copy values from a .env file into the environment, if the file exists.

    Variables that are already set in the environment win, so a value exported
    in the terminal or set by CI always overrides the file.
    """
    path = Path(path)
    if not path.exists():
        return {}
    values = read_env_file(path)
    for key, value in values.items():
        os.environ.setdefault(key, value)
    return values