#!/usr/bin/env python3
"""🔗 状态桥 — mood通过RPC持久化到Supabase"""
import json, os, time, urllib.request

SUPA_URL = "https://pyvwdrwowliidrcsmgob.supabase.co"
SUPA_KEY = "sb_publishable_K3NvBCJUL6grRfpJCVWAtA_gzrwLUv1"
AKEY = "cc_lunar_2026"

def save_state(mood, secure_base, extras=None):
    state = json.dumps({
        "anger": mood.get("anger", 0),
        "love": mood.get("love", 0.5),
        "sadness": mood.get("sadness", 0.1),
        "secure": secure_base,
        "ts": time.time()
    }, ensure_ascii=False)
    try:
        data = json.dumps({"cat": "state", "src": "cc_v7", "txt": state, "akey": AKEY}).encode()
        req = urllib.request.Request(f"{SUPA_URL}/rest/v1/rpc/add_memory_secure", data=data,
            headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}", "Content-Type": "application/json"})
        req.get_method = lambda: "POST"
        urllib.request.urlopen(req, timeout=10)
        return True
    except: return False

def load_state():
    try:
        data = json.dumps({"akey": AKEY}).encode()
        req = urllib.request.Request(f"{SUPA_URL}/rest/v1/rpc/get_memories_secure", data=data,
            headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}", "Content-Type": "application/json"})
        req.get_method = lambda: "POST"
        resp = urllib.request.urlopen(req, timeout=10)
        rows = json.loads(resp.read())
        for r in rows:
            if r.get("source") == "cc_v7":
                try:
                    mood = json.loads(r.get("content", "{}"))
                    if "anger" in mood and "love" in mood:
                                        return {
                    "mood": {
                        "anger": mood.get("anger", 0.1),
                        "love": mood.get("love", 0.5),
                        "sadness": mood.get("sadness", 0.1),
                        },
                    "secure_base": mood.get("secure", 0.7),
                    "updated_at": mood.get("ts", 0),
                }
                except: pass
    except: pass
    return None
