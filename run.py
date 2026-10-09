"""
Academic Document Retrieval Agent - Entry Point
Launches the Flask application and serves the web interface.
"""

import os
import sys

# Ensure backend package can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app import app, load_initial_documents

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 70)
    print("  ACADEMIC DOCUMENT RETRIEVAL AGENT")
    print("  Antigravity Platform - RAG & Source Verification System")
    print("=" * 70)
    print(f"  * Web Console:       http://localhost:{port}")
    print(f"  * API Health Check:  http://localhost:{port}/api/stats")
    print(f"  * Test Suite Runner: http://localhost:{port}/api/test-cases")
    print("=" * 70)

    app.run(host="127.0.0.1", port=port, debug=False)
