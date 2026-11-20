import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Debug mode is off unless explicitly enabled, so the interactive
    # debugger is never exposed by default.
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
