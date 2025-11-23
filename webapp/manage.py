#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks.

    We also make sure the project root is on sys.path so that
    Python can find the 'analysis' package and other top-level
    modules when we run manage.py commands.
    """
    # current_dir = webapp/
    current_dir = Path(__file__).resolve().parent

    # project_root = Global-Spotify-Hits-Python II Project/
    project_root = current_dir.parent

    # Add the project root to sys.path if it is not already there.
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Standard Django setup
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spotify_project.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
