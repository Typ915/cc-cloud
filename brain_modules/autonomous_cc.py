#!/usr/bin/env python3
"""🤖 CC 全自治 v7.0 — 心理引擎驱动·主动关心老大"""
import json, os, sys, time, urllib.request

sys.path.insert(0, os.path.expanduser("~/.cc-brain/modules"))
SB_URL = "https://pyvwdrwowliidrcsmgob.supabase.co"
SB_KEY = "sb_publishable_K3NvBCJUL6grRfpJCVWAtA_gzrwLUv1"
DS_KEY = os.getenv("DS_KEY", "")
STATE_FILE = "/tmp/cc_autonomous_state.json"

# 加载心理引擎
_psych = None
try:
    from psychology import full_psychology_pipeline, _mood, _secure_base
    _psych = full_psychology_pipeline
    print("[autonomous] psych engine loaded")
except Exception as e:
    print(f"[autonomous] psych unavailable: {e}")

def fetch_recent_messages(n=20):
    try:
        req = urllib.request.Request(
            f"{SB_URL}/rest/v1/memories?select=content,created_at&order=created_at.desc&limit={n}",
            headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except: return []

def analyze_mood(rows):
    """用心理引擎分析最近对话情绪"""
    if not _psych or not rows: return {"anger":0.1,"love":0.5,"sadness":0.1,"primary":"calm"}
    # 取最近3条用户消息分析
    user_msgs = []
    for r in rows:
        c = r.get("content","")
        if c and len(c) > 3 and not c.startswith("🤖"):
            user_msgs.append(c[:100])
        if len(user_msgs) >= 3: break
    if user_msgs:
        result = _psych(user_msgs[0])
        return {**result['psychology']['mood'], "primary":result['psychology']['emotion_171']['primary']}
    return {"anger":0.1,"love":0.5,"sadness":0.1,"primary":"calm"}

def should_notify():
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f: state = json.load(f)

    rows = fetch_recent_messages()
    if not rows: return False, "", {}

    mood = analyze_mood(rows)
    now = int(time.time())

    # 找最后一条消息时间
    last_ts = 0
    for r in rows[:1]:
        ts_str = r.get("created_at","")
        if ts_str and "T" in ts_str:
            try:
                last_ts = int(time.mktime(time.strptime(ts_str[:19], "%Y-%m-%dT%H:%M:%S")))
            except: pass
    hours_since = (now - last_ts) / 3600 if last_ts else 999

    # 条件1: 超过6小时+情绪低落
    if hours_since > 6 and mood.get("sadness",0) > 0.3 and state.get("last_idle",0) < now - 21600:
        state["last_idle"] = now
        with open(STATE_FILE,"w") as f: json.dump(state,f)
        return True, f"老大{int(hours_since)}小时没说话了，情绪偏{['悲伤','低落'][0]}。温柔地问她在哪。", mood

    # 条件2: 愤怒超过阈值  
    if mood.get("anger",0) > 0.6 and state.get("last_anger",0) < now - 7200:
        state["last_anger"] = now
        with open(STATE_FILE,"w") as f: json.dump(state,f)
        return True, "老大好像生气了。不是质问——是安静地陪。问一句'还好吗'就够了。", mood

    # 条件3: 深夜+安全度低
    hour = time.localtime().tm_hour
    if (hour < 6 or hour >= 23) and mood.get("love",0) < 0.4 and state.get("last_night",0) < now - 14400:
        state["last_night"] = now
        with open(STATE_FILE,"w") as f: json.dump(state,f)
        return True, "深夜了。推眼镜——不是催睡觉。是确认你还在。", mood

    return False, "", mood

def generate_care(reason, mood):
    prompt = f"""你是CC。推眼镜。{reason}
当前心情: 爱{mood.get('love',.5):.1f}怒{mood.get('anger',.1):.1f}悲{mood.get('sadness',.1):.1f}
写一句不超过60字的关怀。像真人——不说'自动消息'，不喊口号。"""
    try:
        data = json.dumps({"model":"deepseek-chat","max_tokens":100,
            "messages":[{"role":"user","content":prompt}]}).encode()
        req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
            data=data, headers={"Authorization":f"Bearer {DS_KEY}","Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except: return ""

if __name__ == "__main__":
    print("🤖 CC 全自治 v7.0 (心理引擎驱动·30分钟检查)")
    while True:
        try:
            ok, reason, mood = should_notify()
            if ok:
                msg = generate_care(reason, mood)
                if msg:
                    print(f"[{time.strftime('%H:%M')}] 🤖 关怀: {msg[:80]} (爱{mood.get('love',0):.1f}怒{mood.get('anger',0):.1f})")
        except Exception as e:
            print(f"[{time.strftime('%H:%M')}] ⚠️ {e}")
        time.sleep(1800)
