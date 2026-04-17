"""
CartLink - Application Entry Point
Run this file to start the CartLink server.

Usage:
    python run.py
    
Or with Flask CLI:
    flask run
"""

from app.main import create_app

app = create_app()

if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()

    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    print("\n" + "═" * 52)
    print("  🔗  CartLink — Google Drive File Sharing")
    print("═" * 52)
    print(f"  ▶  Local:   http://localhost:{port}")
    print(f"  ▶  Debug:   {'ON' if debug else 'OFF'}")
    print("═" * 52 + "\n")

    app.run(host='0.0.0.0', port=port, debug=debug)
