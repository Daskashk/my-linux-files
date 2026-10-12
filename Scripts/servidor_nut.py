#!/usr/bin/env python3
import http.server
import socketserver
import os
import subprocess
import urllib.parse

# --- CONFIGURACIÓN ---
PORT = 8000
# Rutas oficiales del sistema en openSUSE
CGI_BIN_PATH = "/srv/www/cgi-bin/nut"
STATIC_FILES_PATH = "/srv/www/htdocs/nut"

class NUTHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. Servir archivos estáticos (CSS, Imágenes)
        if path.startswith("/nut/"):
            file_path = os.path.join(STATIC_FILES_PATH, path[len("/nut/"):])
            self.serve_static(file_path)
            return

        # 2. Servir scripts CGI
        if path.startswith("/cgi-bin/"):
            script_name = path.split("/")[-1]
            script_path = os.path.join(CGI_BIN_PATH, script_name)

            if os.path.exists(script_path):
                self.run_cgi(script_path)
            else:
                self.send_error(404, "Script no encontrado")
            return

        # 3. Raíz
        if path == "/":
            self.send_response(302)
            self.send_header('Location', '/cgi-bin/upsstats.cgi')
            self.end_headers()
            return

        self.send_error(404)

    def serve_static(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                self.send_response(200)
                # Adivinar tipo de archivo
                if file_path.endswith('.css'): mt = 'text/css'
                elif file_path.endswith('.png'): mt = 'image/png'
                elif file_path.endswith('.jpg'): mt = 'image/jpeg'
                else: mt = 'text/plain'

                self.send_header('Content-type', mt)
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_error(404, "Archivo estático no encontrado")

    def run_cgi(self, script_path):
        """Ejecuta el CGI y parsea las cabeceras correctamente"""
        env = os.environ.copy()
        # Variables de entorno requeridas por CGI
        env['SERVER_SOFTWARE'] = 'PythonNUT/1.0'
        env['SERVER_NAME'] = 'localhost'
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PROTOCOL'] = 'HTTP/1.1'
        env['SERVER_PORT'] = str(PORT)
        env['REQUEST_METHOD'] = 'GET'
        env['SCRIPT_NAME'] = self.path
        env['QUERY_STRING'] = urllib.parse.urlparse(self.path).query
        env['REMOTE_ADDR'] = self.client_address[0]
        # Variable necesaria para que upsstats.cgi encuentre los archivos de configuración
        env['PATH'] = '/bin:/usr/bin:/usr/sbin'

        try:
            # Ejecutar el script
            proc = subprocess.run([script_path], env=env, capture_output=True, timeout=5)
            output = proc.stdout.decode('utf-8')

            # Separar cabeceras del cuerpo (los CGI separan con doble salto de línea)
            parts = output.split("\n\n", 1)

            headers_raw = parts[0]
            body = parts[1] if len(parts) > 1 else ""

            # Enviar respuesta HTTP OK
            self.send_response(200)

            # Parsear y reenviar cabeceras del CGI
            for line in headers_raw.split("\n"):
                if ": " in line:
                    key, val = line.split(": ", 1)
                    self.send_header(key, val)

            self.end_headers()
            self.wfile.write(body.encode('utf-8'))

        except Exception as e:
            self.send_error(500, f"Error interno: {e}")

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")

if __name__ == '__main__':
    print(f"✅ Servidor NUT corregido en http://localhost:{PORT}")
    print(f"🔗 Interfaz: http://localhost:{PORT}/")

    with socketserver.TCPServer(("", PORT), NUTHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Servidor detenido.")
