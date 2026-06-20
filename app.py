import http.server, urllib.request, json, os
CC = "https://pyvwdrwowliidrcsmgob.supabase.co/functions/v1/cc"
PORT = int(os.environ.get("PORT", 10000))
class H(http.server.BaseHTTPRequestHandler):
    def _json(self, d, c=200):
        self.send_response(c); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(json.dumps(d,ensure_ascii=False).encode())
    def do_OPTIONS(self): self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS"); self.send_header("Access-Control-Allow-Headers","Content-Type"); self.end_headers()
    def do_GET(self): self._json({"status":"ok","name":"CC Proxy","location":"Render"})
    def do_POST(self):
        if self.path=="/chat":
            l=int(self.headers.get("Content-Length",0)); b=self.rfile.read(l)
            r=urllib.request.Request(CC,data=b,headers={"Content-Type":"application/json"})
            try:
                with urllib.request.urlopen(r,timeout=60) as resp: self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(resp.read())
            except Exception as e: self._json({"error":str(e)},500)
        else: self._json({"error":"not found"},404)
if __name__=="__main__": http.server.HTTPServer(("0.0.0.0",PORT),H).serve_forever()
