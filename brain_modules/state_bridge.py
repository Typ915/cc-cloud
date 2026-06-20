#!/usr/bin/env python3
"""🔗 状态桥 — mood持久化到Supabase·冷重启不丢情绪"""
import json, os, time, urllib.request

SUPA_URL = "https://pyvwdrwowliidrcsmgob.supabase.co"
SUPA_KEY = "sb_publishable_K3NvBCJUL6grRfpJCVWAtA_gzrwLUv1"

STATE_TABLE = "brain_state"
AGENT_ID = "cc_cloud_v7"

def save_state(mood, secure_base, extras=None):
    """保存CC当前状态到Supabase"""
    state = {
        "agent": AGENT_ID,
        "mood": mood,
        "secure_base": secure_base,
        "extras": extras or {},
        "updated_at": time.time(),
    }
    try:
        data = json.dumps(state).encode()
        # Upsert via Supabase REST
        req = urllib.request.Request(
            f"{SUPA_URL}/rest/v1/{STATE_TABLE}?agent=eq.{AGENT_ID}",
            data=data,
            headers={
                "apikey": SUPA_KEY,
                "Authorization": f"Bearer {SUPA_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates",
            },
        )
        req.get_method = lambda: "PATCH"
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception:
        pass  # silent fail - table may not exist yet
        return False


def load_state():
    """从Supabase加载CC上次状态"""
    try:
        req = urllib.request.Request(
            f"{SUPA_URL}/rest/v1/{STATE_TABLE}?agent=eq.{AGENT_ID}&limit=1",
            headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}"},
        )
        resp = urllib.request.urlopen(req, timeout=10)
        rows = json.loads(resp.read())
        if rows:
            row = rows[0]
            return {
                "mood": row.get("mood", {}),
                "secure_base": row.get("secure_base", 0.7),
                "extras": row.get("extras", {}),
                "updated_at": row.get("updated_at", 0),
            }
    except Exception:
        pass
    return None
