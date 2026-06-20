import http.server, urllib.request, urllib.parse, json, os, sys
CC = "https://pyvwdrwowliidrcsmgob.supabase.co/functions/v1/cc"
PORT = int(os.environ.get("PORT", 10000))
BRAIN = os.path.join(os.path.dirname(__file__), "brain_modules")
sys.path.insert(0, BRAIN)

# 预加载引擎
engines = {}
_psych = None
try:
    from psychology import full_psychology_pipeline
    _psych = full_psychology_pipeline
    engines['psych'] = True
except: engines['psych'] = False

for mod, name in [("top_math","top_math"),("frontier","frontier"),("research","research")]:
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
                r = _psych(q)
                return self._json({"text":q[:50],"mood":r['psychology']['mood'],"emotion_171":r['psychology']['emotion_171']['primary']})
            except Exception as e: return self._json({"error":str(e)[:100]},500)
        self._json({"status":"ok"})
    def do_POST(self):
        if self.path=="/chat":
            l=int(self.headers.get("Content-Length",0)); body=self.rfile.read(l)
            try:
                req = json.loads(body)
                msg = req.get("message","")
                # 心理引擎注入：分析消息→追加情绪上下文到prompt
                if _psych and msg:
                    try:
                        r = _psych(msg)
                        mood = r['psychology']['mood']
                        e171 = r['psychology']['emotion_171']
                        # 注入情绪信号
                        req["message"] = msg + f"\n\n[CC此刻: 爱{mood['love']:.1f}怒{mood['anger']:.1f}悲{mood.get('sadness',0):.1f} 安全{r['psychology']['secure_base']:.1f} 情绪:{e171['primary']}]"
                    except: pass
                body2 = json.dumps(req).encode()
                r = urllib.request.Request(CC, data=body2, headers={"Content-Type":"application/json"})
                with urllib.request.urlopen(r, timeout=60) as resp:
                    self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(resp.read())
            except Exception as e: self._json({"error":str(e)[:100]},500)
        else: self._json({"error":"not found"},404)
if __name__=="__main__": http.server.HTTPServer(("0.0.0.0",PORT),H).serve_forever()
