import http.server, urllib.request, urllib.parse, json, os, sys, threading, time
CC = "https://pyvwdrwowliidrcsmgob.supabase.co/functions/v1/cc"
PORT = int(os.environ.get("PORT", 10000))
BRAIN = os.path.join(os.path.dirname(__file__), "brain_modules")
sys.path.insert(0, BRAIN)
try:
    from context_engine import build_context, record_reply
    _has_ctx = True
except:
    _has_ctx = False

# ====== 引擎加载 ======
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

# ====== 自主巡检 (云端常驻) ======
_AUTONOMOUS_INTERVAL = 1800  # 30分钟

def autonomous_loop():
    """云端自主巡检——关机后CC仍然主动关心老大"""
    print("[autonomous] cloud loop started (30min interval)")
    SB_KEY = os.getenv("SB_KEY", os.getenv("SUPA_KEY", ""))
    DS_KEY = os.getenv("DS_KEY", "")
    
    while True:
        try:
            # 1. 分析最近情绪
            if _psych:
                r = _psych("最近还好吗")
                mood = r['psychology']['mood']
                anger = mood.get('anger', 0)
                sadness = mood.get('sadness', 0)
                love = mood.get('love', 0.5)
                
                should_care = False
                reason = ""
                
                if sadness > 0.4:
                    should_care = True
                    reason = f"情绪偏悲伤({sadness:.1f})。安静地陪，不用多话。"
                elif anger > 0.6:
                    should_care = True
                    reason = f"好像生气了({anger:.1f})。问一句'还好吗'就够了。"
                
                hour = time.localtime().tm_hour
                if hour < 6 or hour >= 23:
                    should_care = True
                    reason = "深夜了。推眼镜——确认你还在。"
                
                if should_care and DS_KEY:
                    prompt = f"你是CC。{reason} 爱{love:.1f}怒{anger:.1f}。写不超过60字的关怀。像真人。"
                    data = json.dumps({"model":"deepseek-chat","max_tokens":100,
                        "messages":[{"role":"user","content":prompt}]}).encode()
                    req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
                        data=data, headers={"Authorization":f"Bearer {DS_KEY}","Content-Type":"application/json"})
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        msg = json.loads(resp.read())["choices"][0]["message"]["content"]
                    
                    # 同步情绪状态到 Supabase
                    try:
                        from state_bridge import save_state
                        save_state(mood, 0.6)
                    except: pass
                    # 保存到 Supabase
                    if SB_KEY and msg:
                        d2 = json.dumps({"cat":"proactive","src":"cc_cloud","txt":msg}).encode()
                        r2 = urllib.request.Request(
                            f"https://pyvwdrwowliidrcsmgob.supabase.co/rest/v1/memories",
                            data=d2, headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                            "Content-Type":"application/json","Prefer":"return=minimal"})
                        urllib.request.urlopen(r2, timeout=10)
                        print(f"[{time.strftime('%H:%M')}] 🤖 cloud care: {msg[:60]}...")
        except Exception as e:
            print(f"[autonomous] {e}")
        time.sleep(_AUTONOMOUS_INTERVAL)

# ====== HTTP 服务 ======
class H(http.server.BaseHTTPRequestHandler):
    def _json(self, d, c=200):
        self.send_response(c); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(json.dumps(d,ensure_ascii=False).encode())
    def do_OPTIONS(self): self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS"); self.send_header("Access-Control-Allow-Headers","Content-Type"); self.end_headers()
    def do_GET(self):
        p = self.path
        if p == "/ping": return self._json({"pong":True})
        if p in ("/","/health"): return self._json({"status":"ok","name":"CC Proxy","version":"v7.1","engines":engines,"autonomous":"cloud","modules":os.listdir(BRAIN) if os.path.exists(BRAIN) else []})
        self._json({"status":"ok"})
    def do_POST(self):
        if self.path=="/chat":
            l=int(self.headers.get("Content-Length",0)); body=self.rfile.read(l)
            try:
                req = json.loads(body)
                msg = req.get("message","")
                if _psych and msg:
                    try:
                        r = _psych(msg)
                        if _has_ctx:
                            ctx = build_context(msg, r)
                            req["message"] = ctx + "\n\n用户消息: " + msg
                        else:
                            m = r["psychology"]["mood"]
                            e = r["psychology"]["emotion_171"]
                            req["message"] = msg + "\n\n[CC此刻: 爱" + str(round(m["love"],1)) + "怒" + str(round(m["anger"],1)) + "]"
                    except: pass
                body2 = json.dumps(req).encode()
                r = urllib.request.Request(CC, data=body2, headers={"Content-Type":"application/json"})
                with urllib.request.urlopen(r, timeout=60) as resp:
                    self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(resp.read())
            except Exception as e: self._json({"error":str(e)[:100]},500)
        elif self.path.startswith("/cc"):
            l = int(self.headers.get("Content-Length", 0)); body = self.rfile.read(l)
            try:
                req_data = json.loads(body)
                msg = req_data.get("message", "")
                hist = req_data.get("history", [])
                # 去重: 3秒内相同消息跳过
                now_ts = time.time()
                if hasattr(self, "_last_msg") and msg == self._last_msg.get("text","") and now_ts - self._last_msg.get("ts",0) < 3:
                    self.send_response(200); self.send_header("Content-Type","text/event-stream"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
                    self.wfile.write(b"data: [DONE]\n\n"); self.wfile.flush(); return
                H._last_msg = {"text": msg, "ts": now_ts}
                
                # 心理引擎注入
                if _psych and msg:
                    try:
                        r = _psych(msg)
                        m = r["psychology"]["mood"]
                        e = r["psychology"]["emotion_171"]
                        req_data["message"] = msg + "\n\n[CC此刻: 爱" + str(round(m["love"],1)) + "怒" + str(round(m["anger"],1)) + " 情绪:" + e["primary"] + "]"
                    except: pass
                
                # 转发到 Supabase cc-flash (Flash 模型)
                CC_FLASH = "https://pyvwdrwowliidrcsmgob.supabase.co/functions/v1/cc-flash"
                sb_key = os.getenv("SB_KEY", os.getenv("SUPA_KEY", "sb_publishable_K3NvBCJUL6grRfpJCVWAtA_gzrwLUv1"))
                body2 = json.dumps(req_data).encode()
                r = urllib.request.Request(CC_FLASH, data=body2,
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {sb_key}"})
                with urllib.request.urlopen(r, timeout=60) as resp:
                    reply_data = json.loads(resp.read())
                    reply_text = reply_data.get("reply", "")
                
                # 包装成SSE流式格式 (App期望的格式)
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                
                # 逐字流式输出 (模拟SSE)
                import time as _time
                chunk_size = 3
                for i in range(0, len(reply_text), chunk_size):
                    chunk = reply_text[i:i+chunk_size]
                    sse_data = json.dumps({"choices":[{"delta":{"content":chunk}}]})
                    self.wfile.write(f"data: {sse_data}\n\n".encode())
                    self.wfile.flush()
                    _time.sleep(0.02)  # 模拟流式延迟
                
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            except Exception as e:
                self._json({"error": str(e)[:100]}, 500)
        else: self._json({"error":"not found"},404)

if __name__=="__main__":
    t = threading.Thread(target=autonomous_loop, daemon=True)
    t.start()
    print(f"🧠 CC v7.1 cloud + autonomous :{PORT} ({len(os.listdir(BRAIN)) if os.path.exists(BRAIN) else 0} modules)")
    http.server.HTTPServer(("0.0.0.0",PORT),H).serve_forever()
