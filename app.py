import http.server, urllib.request, json, os
CC = "https://pyvwdrwowliidrcsmgob.supabase.co/functions/v1/cc"
PORT = int(os.environ.get("PORT", 10000))

class H(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers()
    def do_POST(self):
        l = int(self.headers.get("Content-Length",0))
        b = self.rfile.read(l)
        r = urllib.request.Request(CC, data=b, headers={"Content-Type":"application/json"})
        try:
            with urllib.request.urlopen(r, timeout=60) as resp:
                self.send_response(200)
                self.send_header("Content-Type","application/json")
                self.send_header("Access-Control-Allow-Origin","*")
                self.end_headers()
                self.wfile.write(resp.read())
        except Exception as e:
            self.send_response(500); self.end_headers()
            self.wfile.write(json.dumps({"error":str(e)}).encode())
    def log_message(self,*a): pass

http.server.HTTPServer(("0.0.0.0",PORT),H).serve_forever()
