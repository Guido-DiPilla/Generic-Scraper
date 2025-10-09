"""Module entrypoint to run the Typer app via `python -m generic_scraper`."""

try:
    from .refactored import app
except ImportError:
    from refactored import app

if __name__ == "__main__":
    app()
