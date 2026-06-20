import http.server, urllib.request, urllib.parse, json, os, sys
CC = "https://pyvwdrwowliidrcsmgob.supabase.co/functions/v1/cc"
PORT = int(os.environ.get("PORT", 10000))
BRAIN = os.path.join(os.path.dirname(__file__), "brain_modules")
sys.path.insert(0, BRAIN)

# 预加载引擎
engines = {}
for mod, name in [("psychology","psych"),("top_math","top_math"),("frontier","frontier"),("research","research")]:
    try: __import__(mod); engines[name] = True
    except: engines[name] = False

class H(http.server.BaseHTTPRequestHandler):
    def _json(self, d, c=200):
        self.send_response(c); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(json.dumps(d,ensure_ascii=False).encode())
    def do_OPTIONS(self): self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS"); self.send_header("Access-Control-Allow-Headers","Content-Type"); self.end_headers()
    def do_GET(self):
        p = self.path
        if p == "/ping": return self._json({"pong":True})
        if p in ("/","/health"): return self._json({"status":"ok","name":"CC Proxy","version":"v7.0","engines":engines,"modules":os.listdir(BRAIN) if os.path.exists(BRAIN) else []})
        if p.startswith("/brain/psych"):
            q = urllib.parse.parse_qs(p.split("?")[1]).get("text",["ping"])[0] if "?" in p else "ping"
            try:
                from psychology import full_psychology_pipeline
                r = full_psychology_pipeline(q)
                return self._json({"text":q[:50],"mood":r['psychology']['mood'],"emotion_171":r['psychology']['emotion_171']['primary']})
            except Exception as e: return self._json({"error":str(e)},500)
        self._json({"status":"ok","name":"CC Proxy","location":"Render"})
    def do_POST(self):
        if self.path=="/chat":
            l=int(self.headers.get("Content-Length",0)); b=self.rfile.read(l)
            r=urllib.request.Request(CC,data=b,headers={"Content-Type":"application/json"})
            try:
                with urllib.request.urlopen(r,timeout=60) as resp: self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(resp.read())
            except Exception as e: self._json({"error":str(e)},500)
        else: self._json({"error":"not found"},404)
if __name__=="__main__": http.server.HTTPServer(("0.0.0.0",PORT),H).serve_forever()
