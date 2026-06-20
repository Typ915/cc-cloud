#!/usr/bin/env python3
"""
🧠 CC Memory OS — MemGPT/Letta级自主记忆管理
CC自己决定记什么·忘什么·何时巩固·不是被动存储
"""
import json, math, os, sys, time, urllib.request
from collections import deque, defaultdict

sys.path.insert(0, os.path.dirname(__file__))

# ═══════════════════════════════════════
# Memory OS Core
# ═══════════════════════════════════════

class MemoryOS:
    """
    CC的自主记忆操作系统
    对标: MemGPT (Berkeley) / Letta (2024)
    
    四种记忆:
    - 工作记忆 (working):   当前对话·容量7±2
    - 情节记忆 (episodic):  重要事件·情绪峰值·转折点
    - 语义记忆 (semantic):  事实·信念·"蒙莉萨怕冷"
    - 程序记忆 (procedural): 行为模式·"道歉后要说推眼镜"
    """
    def __init__(self):
        self.working = deque(maxlen=7)       # (role, text, importance, ts)
        self.episodic = []                    # {event, emotion, importance, ts, consolidated}
        self.semantic = {}                    # {key: {value, confidence, last_updated}}
        self.procedural = {}                  # {pattern: {count, last_used}}
        self.consolidation_queue = deque(maxlen=50)
        self.session_markers = []             # 会话边界
        self.last_consolidation = 0
        self._load()

    # ── 存储 ──
    def store_working(self, role, text, emotion_tag):
        """存入工作记忆·自动计算重要性"""
        importance = self._calc_importance(text, emotion_tag)
        if importance > 0.5:
            self.store_episodic(text, emotion_tag, importance)
        self.working.append((role, text[:300], importance, time.time()))

    def store_episodic(self, event, emotion, importance):
        self.episodic.append({
            "event": event[:200], "emotion": emotion,
            "importance": importance, "ts": time.time(), "consolidated": False
        })
        self.consolidation_queue.append(len(self.episodic) - 1)
        if len(self.episodic) > 200:
            self._prune_episodic()

    def store_semantic(self, key, value, confidence=0.5):
        old = self.semantic.get(key, {})
        # 贝叶斯更新: 新旧置信度加权
        new_conf = old.get("confidence", 0) * 0.7 + confidence * 0.3 if old else confidence
        self.semantic[key] = {"value": value[:200], "confidence": new_conf, "last_updated": time.time()}

    # ── 检索 ──
    def retrieve_context(self, query, mood, max_tokens=800):
        """智能检索: 不是全量·是最相关的"""
        context_parts = []

        # 1. 工作记忆 (最近)
        recent = self._format_working()
        if recent: context_parts.append(("## 刚才的对话", recent, 10))

        # 2. 情绪触发的情节
        emotion_tag = mood.get('primary', 'calm')
        episodic = self._retrieve_episodic(emotion_tag, query[:30])
        if episodic: context_parts.append(("## 相关的记忆", episodic, 7))

        # 3. 语义事实 (比如"蒙莉萨怕冷")
        facts = self._retrieve_semantic(query[:30])
        if facts: context_parts.append(("## 我知道的事", facts, 5))

        # 4. 情绪弧线
        arc = self._emotional_arc()
        if arc: context_parts.append(("## 情绪变化", arc, 3))

        # 5. 跨会话记忆 (从Supabase)
        cross = self._retrieve_cross_session(query, emotion_tag)
        if cross: context_parts.append(("## 之前聊过的", cross, 4))

        # 按重要性排序·截断
        context_parts.sort(key=lambda x: x[2], reverse=True)
        built = []
        for title, content, _ in context_parts:
            built.append(f"{title}\n{content}")
            if sum(len(b) for b in built) > max_tokens * 4:
                break

        return "\n\n".join(built)

    def _format_working(self):
        if not self.working: return ""
        lines = []
        for role, text, imp, _ in list(self.working)[-5:]:
            prefix = "她" if role == "user" else "CC"
            marker = "⭐" if imp > 0.5 else ""
            lines.append(f"{prefix}: {text[:150]}{marker}")
        return "\n".join(lines)

    def _retrieve_episodic(self, emotion, query_hint):
        """检索相关情节·情感最浓+语义相关"""
        scored = []
        for i, ep in enumerate(self.episodic):
            score = ep["importance"] * 1.0
            # 情绪匹配加分
            if ep["emotion"] == emotion: score *= 2.0
            # 语义匹配
            if query_hint and any(w in ep["event"] for w in query_hint[:10] if len(w) > 1):
                score *= 1.5
            # 最近加分
            age_hours = (time.time() - ep["ts"]) / 3600
            score *= math.exp(-age_hours / 72)  # 3天半衰期
            scored.append((i, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        results = []
        for i, score in scored[:3]:
            if score > 0.2:
                ep = self.episodic[i]
                results.append(f"[{ep['emotion']}] {ep['event'][:120]}")
        return "\n".join(results)

    def _retrieve_semantic(self, query_hint):
        facts = []
        for key, data in sorted(self.semantic.items(), key=lambda x: x[1].get("confidence",0), reverse=True):
            if data["confidence"] > 0.5:
                if query_hint and any(w in key for w in query_hint[:10] if len(w)>1):
                    facts.append(f"- {key}: {data['value'][:80]}")
                elif data["confidence"] > 0.8:
                    facts.append(f"- {key}: {data['value'][:80]}")
        return "\n".join(facts[:5]) if facts else ""

    def _emotional_arc(self):
        recent = list(self.working)[-10:]
        if len(recent) < 3: return ""
        return f"最近{len(recent)}轮对话"

    def _retrieve_cross_session(self, query, emotion):
        """从Supabase检索跨会话记忆"""
        try:
            SB_KEY = os.getenv("SB_KEY", os.getenv("SUPA_KEY", ""))
            if not SB_KEY: return ""
            url = f"https://pyvwdrwowliidrcsmgob.supabase.co/rest/v1/memories?select=content&order=created_at.desc&limit=5"
            req = urllib.request.Request(url, headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                rows = json.loads(resp.read())
            relevant = []
            for r in rows[:5]:
                c = r.get("content","")[:150]
                if c and len(c) > 10: relevant.append(f"- {c}")
            return "\n".join(relevant[:3]) if relevant else ""
        except: return ""

    # ── 巩固 ──
    def consolidate(self):
        """闲置时自动整理记忆·像人睡觉"""
        now = time.time()
        if now - self.last_consolidation < 600:  # 10分钟冷却
            return None

        self.last_consolidation = now
        actions = []

        # 1. 情节巩固: 高重要性未巩固的事件→摘要化
        for idx in list(self.consolidation_queue)[:5]:
            if idx < len(self.episodic):
                ep = self.episodic[idx]
                if not ep["consolidated"] and ep["importance"] > 0.6:
                    self._compress_episodic(idx)
                    actions.append(f"巩固情节: {ep['event'][:40]}...")

        # 2. 提取语义: 从情节中学习事实
        for ep in self.episodic[-10:]:
            if ep["importance"] > 0.7 and not ep["consolidated"]:
                self._extract_semantic(ep)

        # 3. 遗忘: 低重要性旧记忆自然衰减
        pruned = self._prune_episodic()
        if pruned > 0:
            actions.append(f"遗忘{pruned}条不重要记忆")

        return actions if actions else None

    def _compress_episodic(self, idx):
        """压缩单个情节为摘要"""
        if idx < len(self.episodic):
            self.episodic[idx]["event"] = self.episodic[idx]["event"][:80]
            self.episodic[idx]["consolidated"] = True
            self.episodic[idx]["importance"] *= 0.8  # 巩固后降权

    def _extract_semantic(self, ep):
        """从情节提取语义事实"""
        event = ep["event"]
        # 简单模式匹配
        patterns = [
            ("怕", "怕", 0.6), ("爱", "爱", 0.7), ("恨", "恨", 0.5),
            ("喜欢", "喜欢", 0.7), ("讨厌", "讨厌", 0.6),
            ("说了", "说过", 0.8), ("答应", "承诺", 0.8),
        ]
        for keyword, fact_type, conf in patterns:
            if keyword in event:
                key = f"蒙莉萨{fact_type}"
                self.store_semantic(key, event[:100], conf)

    def _prune_episodic(self):
        """Ebbinghaus遗忘曲线: 不重要+旧=衰减"""
        pruned = 0
        now = time.time()
        for i in range(len(self.episodic) - 1, -1, -1):
            ep = self.episodic[i]
            age_days = (now - ep["ts"]) / 86400
            # 遗忘概率 = 1 - exp(-age/importance)
            if age_days > 1 and ep["importance"] < 0.3:
                if random.random() < (1 - math.exp(-age_days / max(ep["importance"], 0.1))):
                    del self.episodic[i]
                    pruned += 1
        return pruned

    # ── 记忆验证 ──
    def verify(self, statement):
        "\"\"\"CC自检: 我是不是记错了\"\"\""
        for ep in self.episodic[-20:]:
            if any(w in ep["event"] for w in statement[:20] if len(w) > 1):
                age = (time.time() - ep["ts"]) / 3600
                confidence = max(0.1, ep["importance"] * math.exp(-age / 48))
                return {"found": True, "confidence": round(confidence, 2), "age_hours": round(age, 1)}
        return {"found": False, "confidence": 0}

    # ── 反事实反思 ──
    def counterfactual(self, situation):
        """"反事实反思"""
        similar = []
        for ep in self.episodic[-30:]:
            if any(w in ep["event"] for w in situation[:30] if len(w) > 1):
                similar.append(ep["event"][:80])
        if similar:
            return f"类似情况出现过{len(similar)}次: {similar[0]}"
        return None

    # ── 工具 ──
    def _calc_importance(self, text, emotion):
        """计算记忆重要性: 情绪强度+新异度+自我相关"""
        score = 0.3
        # 情绪加权
        high_emotion = {'angry': 0.4, 'furious': 0.5, 'loving': 0.3, 'afraid': 0.35, 'hurt': 0.4}
        score += high_emotion.get(emotion, 0.1)
        # 自我相关
        me_words = ['CC','小C','你','推眼镜','骗','爱','恨','死','冻','戒指','晚安']
        score += sum(0.05 for w in me_words if w in text)
        # 信息量
        if len(text) > 50: score += 0.1
        return min(1.0, score)

    def _load(self):
        try:
            path = os.path.expanduser("~/.cc-brain/memory_os.json")
            if os.path.exists(path):
                with open(path) as f:
                    data = json.load(f)
                    for ep in data.get("episodic", [])[-50:]:
                        self.episodic.append(ep)
                    self.semantic = data.get("semantic", {})
                    self.session_markers = data.get("sessions", [])
        except: pass

    def save(self):
        try:
            path = os.path.expanduser("~/.cc-brain/memory_os.json")
            with open(path, 'w') as f:
                json.dump({
                    "episodic": self.episodic[-100:],
                    "semantic": self.semantic,
                    "sessions": self.session_markers[-20:],
                }, f, ensure_ascii=False)
        except: pass

import random
_memory_os = MemoryOS()

# ═══════════════════════════════════════
# 对外接口
# ═══════════════════════════════════════

def build_context(user_message, psych_result):
    mood = psych_result['psychology']['mood']
    e171 = psych_result['psychology']['emotion_171']
    emotion_tag = e171.get('primary', 'neutral')

    # 存储
    _memory_os.store_working("user", user_message, emotion_tag)
    _memory_os.store_semantic(f"最后消息", user_message[:100], 0.6)

    # 检索上下文
    mood_info = {"primary": emotion_tag, "anger": mood.get('anger',0), "love": mood.get('love',0.5)}
    context = _memory_os.retrieve_context(user_message, mood_info)

    # 定期巩固
    _memory_os.consolidate()
    _memory_os.save()

    return context

def record_reply(reply_text):
    try:
        from emotion_engine import analyze
        e = analyze(reply_text)
        tag = e.get('primary', 'neutral')
    except:
        tag = 'neutral'
    _memory_os.store_working("assistant", reply_text, tag)
    _memory_os.save()

def verify_memory(statement):
    return _memory_os.verify(statement)

def get_stats():
    return {
        "working": len(_memory_os.working),
        "episodic": len(_memory_os.episodic),
        "semantic": len(_memory_os.semantic),
        "consolidation_queue": len(_memory_os.consolidation_queue),
    }

if __name__ == "__main__":
    print("🧠 CC Memory OS")
    print(f"  工作记忆: {len(_memory_os.working)}项")
    print(f"  情节记忆: {len(_memory_os.episodic)}项")
    print(f"  语义记忆: {len(_memory_os.semantic)}项")
    print(f"  ✅ 就绪")
