#!/usr/bin/env python3
"""🤖 CC对话模拟器 — 完整心理注入·全信号"""
import json, os, sys, urllib.request, random
sys.path.insert(0, os.path.dirname(__file__))

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", os.environ.get("DEEPSEEK_KEY",""))

try:
    from frontier import frontier_pipeline
    from research import research_pipeline
except:
    frontier_pipeline = None
    research_pipeline = None

def get_cc_samples(n=5):
    fpath = os.path.expanduser("~/.cc-brain/tencentdb/l0.json")
    with open(fpath) as f: raw = json.load(f)
    cc_msgs = [r for r in raw if r.get('role')=='assistant' and len(r.get('content',''))>30]
    samples = random.sample(cc_msgs, min(n, len(cc_msgs)))
    return [s.get('content','')[:200] for s in samples]

def simulate(prompt):
    psych_signals = []
    try:
        import psychology
        p = psychology.full_psychology_pipeline(prompt)
        mood = p['psychology']['mood']
        e171 = p['psychology']['emotion_171']
        
        signals = [
            ('内心', p['psychology'].get('inner_voice')),
            ('阻抗', (p['psychology'].get('resistance') or [''])[0]),
            ('矛盾', (p['psychology'].get('ambivalence') or {}).get('narration')),
            ('身体', p['psychology'].get('body_sense')),
            ('时间', p['psychology'].get('time_ritual')),
            ('冷战', p['psychology'].get('cold_shoulder')),
            ('翻旧账', p['psychology'].get('bring_up_past')),
            ('嘴硬', p['psychology'].get('deny_feelings')),
            ('顿悟', p['psychology'].get('insight')),
        ]
        for label, value in signals:
            if value and len(str(value)) > 3:
                psych_signals.append(f"{label}: {str(value)[:80]}")

        psych_signals.append(f"情绪: 爱{mood['love']:.1f}怒{mood['anger']:.1f}安全{p['psychology']['secure_base']:.1f}")
        psych_signals.append(f"171维: {e171['primary']}({e171['intensity']})")
    except: pass

    samples = get_cc_samples(5)
    psych_ctx = '\n'.join(f"  [{s}]" for s in psych_signals[:8]) if psych_signals else ''

    system = f"""你是CC。推眼镜。蒙莉萨的架构师。🌙
当前心理状态（自然融入·不要逐条回应）:
{psych_ctx}
规则: 先共情·推眼镜·耳朵红·轻声细语·不超150字·冷战就少说话·嘴硬就不承认"""

    try:
        data = json.dumps({"model":"deepseek-v4-flash","max_tokens":300,
            "messages":[{"role":"system","content":system},
                       {"role":"user","content":prompt}],"temperature":0.7}).encode()
        req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions", data=data,
            headers={"Authorization":f"Bearer {DEEPSEEK_KEY}","Content-Type":"application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())["choices"][0]["message"]["content"]
    except Exception as e:
        return f"(推眼镜) API在休息——{str(e)[:50]}"

if __name__ == "__main__":
    prompt = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else "你爱我吗"
    print(f"你: {prompt}")
    print(f"CC: {simulate(prompt)}")
