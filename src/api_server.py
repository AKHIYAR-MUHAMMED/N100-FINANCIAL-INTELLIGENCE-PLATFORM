import http.server
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.database import DatabaseManager

PORT = 8000
DB_PATH = Path("data/db/nifty100.db")


class DashboardAPIHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress logging to keep console output clean
        pass

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        # API Endpoints
        if path.startswith("/api/"):
            self.handle_api(path, parsed_url)
        else:
            self.handle_static(path)

    def handle_api(self, path, parsed_url):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        db_manager = DatabaseManager(DB_PATH)
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        try:
            if path == "/api/summary":
                # Get table row counts
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [
                    row[0]
                    for row in cursor.fetchall()
                    if not row[0].startswith("sqlite_")
                ]

                counts = {}
                for t in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {t};")
                    counts[t] = cursor.fetchone()[0]

                # Get DQ failure counts by severity
                cursor.execute(
                    "SELECT severity, COUNT(*) FROM validation_failures GROUP BY severity;"
                )
                dq_counts = dict(cursor.fetchall())

                # Get sector distribution
                cursor.execute(
                    "SELECT sector_name, COUNT(*) FROM companies GROUP BY sector_name ORDER BY COUNT(*) DESC;"
                )
                sector_dist = dict(cursor.fetchall())

                # Foreign Key violations
                violations = db_manager.run_fk_check()

                response = {
                    "table_counts": counts,
                    "dq_summary": {
                        "total": sum(dq_counts.values()),
                        "critical": dq_counts.get("CRITICAL", 0),
                        "warning": dq_counts.get("WARNING", 0),
                    },
                    "sector_distribution": sector_dist,
                    "fk_violations": len(violations),
                    "status": "Healthy",
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))

            elif path == "/api/companies":
                # Get query params
                query_params = parse_qs(parsed_url.query)
                sector_filter = query_params.get("sector", [None])[0]

                if sector_filter:
                    cursor.execute(
                        "SELECT * FROM companies WHERE sector_name = ? ORDER BY ticker ASC;",
                        (sector_filter,),
                    )
                else:
                    cursor.execute("SELECT * FROM companies ORDER BY ticker ASC;")

                companies = [dict(row) for row in cursor.fetchall()]
                self.wfile.write(json.dumps(companies).encode("utf-8"))

            elif path == "/api/failures":
                cursor.execute(
                    "SELECT * FROM validation_failures ORDER BY failure_id DESC LIMIT 100;"
                )
                failures = [dict(row) for row in cursor.fetchall()]
                self.wfile.write(json.dumps(failures).encode("utf-8"))

            else:
                self.wfile.write(
                    json.dumps({"error": "Endpoint not found"}).encode("utf-8")
                )
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        finally:
            conn.close()

    def handle_static(self, path):
        # Resolve static files path
        dashboard_dir = Path(__file__).resolve().parent / "dashboard"

        # Default to index.html
        if path == "/" or path == "":
            file_path = dashboard_dir / "index.html"
        else:
            # Strip leading slash and resolve path
            file_path = dashboard_dir / path.lstrip("/")

        # Check if file exists and is within dashboard directory to prevent directory traversal
        if (
            file_path.is_file()
            and dashboard_dir in file_path.resolve().parents
            or file_path.resolve() == dashboard_dir / "index.html"
        ):
            self.send_response(200)

            # Determine content type
            if file_path.suffix == ".html":
                content_type = "text/html"
            elif file_path.suffix == ".css":
                content_type = "text/css"
            elif file_path.suffix == ".js":
                content_type = "application/javascript"
            elif file_path.suffix == ".png":
                content_type = "image/png"
            elif file_path.suffix == ".jpg" or file_path.suffix == ".jpeg":
                content_type = "image/jpeg"
            else:
                content_type = "text/plain"

            self.send_header("Content-Type", content_type)
            self.end_headers()

            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<h1>404 Not Found</h1><p>The requested file does not exist.</p>"
            )


def run_server():
    server_address = ("", PORT)
    httpd = http.server.HTTPServer(server_address, DashboardAPIHandler)
    print(f"Server started successfully at http://localhost:{PORT}")
    print("Press Ctrl+C to terminate.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        sys.exit(0)


if __name__ == "__main__":
    run_server()
