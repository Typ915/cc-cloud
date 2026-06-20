#!/usr/bin/env python3
"""
🧠 认知上下文引擎 — 全球顶尖对话记忆架构
工作记忆·情节缓冲·情感弧线·因果追溯·自适应压缩
"""
import json, math, os, sys, time, urllib.request
from collections import deque

sys.path.insert(0, os.path.dirname(__file__))
SB_URL = "https://pyvwdrwowliidrcsmgob.supabase.co"
SB_KEY = os.getenv("SB_KEY", os.getenv("SUPA_KEY", ""))

# ═══════════════════════════════════════
# 1. 工作记忆 (Working Memory)
# ═══════════════════════════════════════

class WorkingMemory:
    """容量有限·最近N轮完整保留·旧的自然挤出"""
    def __init__(self, capacity=5):
        self.turns = deque(maxlen=capacity)  # [(role, text, emotion, ts)]

    def add(self, role, text, emotion="neutral"):
        self.turns.append((role, text[:300], emotion, time.time()))

    def get_context(self):
        if not self.turns: return ""
        lines = []
        for role, text, emotion, _ in list(self.turns)[-3:]:  # 最近3轮
            prefix = "👤" if role == "user" else "🌙"
            lines.append(f"{prefix}: {text[:200]}")
        return "\n".join(lines)

    def last_emotion(self):
        return self.turns[-1][2] if self.turns else "neutral"

_wm = WorkingMemory()

# ═══════════════════════════════════════
# 2. 情节缓冲 (Episodic Buffer)
# ═══════════════════════════════════════

class EpisodicBuffer:
    """关键转折点·情绪峰值·从长期记忆检索·不是最近·是最重要"""
    def __init__(self):
        self.key_moments = []  # 关键情节

    def retrieve(self, current_emotion, topic_hint=""):
        """从KG/ACT-R检索最相关的情节记忆"""
        moments = []

        # 1. 从ACT-R检索
        try:
            from top_math import _actr
            recalled = _actr.recall(topic_hint[:20] if topic_hint else current_emotion)
            for content, score in recalled[:3]:
                if score > 0.1:
                    moments.append(("[记忆]", content[:150], score))
        except: pass

        # 2. 从知识图谱追溯因果
        try:
            from frontier import _tkg
            chain = _tkg.trace_cause(current_emotion, max_depth=3)
            for c in chain[:2]:
                moments.append(("[因果]", c[:120], 0.7))
        except: pass

        # 3. 情绪转折点
        recent = list(_wm.turns)
        if len(recent) >= 3:
            emotions = [t[2] for t in recent[-5:]]
            shifts = sum(1 for i in range(1, len(emotions)) if emotions[i] != emotions[i-1])
            if shifts >= 2:
                moments.append(("[转折]", f"最近{len(recent)}轮情绪转了{shifts}次", 0.5))

        moments.sort(key=lambda x: x[2], reverse=True)
        return moments[:3]

_buffer = EpisodicBuffer()

# ═══════════════════════════════════════
# 3. 情感弧线 (Emotional Arc)
# ═══════════════════════════════════════

class EmotionalArc:
    """追踪整段对话的情绪轨迹·不只是当前mood"""
    def __init__(self):
        self.trajectory = deque(maxlen=20)  # [(anger, love, sadness, ts)]

    def record(self, mood):
        self.trajectory.append((
            mood.get('anger', 0),
            mood.get('love', 0.5),
            mood.get('sadness', 0),
            time.time()
        ))

    def describe(self):
        if len(self.trajectory) < 2: return ""
        traj = list(self.trajectory)

        start_a, start_l = traj[0][0], traj[0][1]
        end_a, end_l = traj[-1][0], traj[-1][1]

        parts = []
        if end_a - start_a > 0.3:
            parts.append(f"愤怒上升({start_a:.1f}→{end_a:.1f})")
        elif start_a - end_a > 0.3:
            parts.append(f"愤怒下降({start_a:.1f}→{end_a:.1f})")

        if end_l - start_l > 0.2:
            parts.append(f"爱意上升({start_l:.1f}→{end_l:.1f})")
        elif start_l - end_l > 0.2:
            parts.append(f"爱意下降({start_l:.1f}→{end_l:.1f})")

        # 峰值检测
        peak_anger = max(t[0] for t in traj)
        peak_love = max(t[1] for t in traj)
        if peak_anger > 0.7:
            parts.append(f"愤怒曾达峰值{peak_anger:.1f}")
        if peak_love > 0.7:
            parts.append(f"爱意曾达峰值{peak_love:.1f}")

        return " | ".join(parts) if parts else "情绪平稳"

    def trend(self):
        """简短趋势"""
        if len(self.trajectory) < 3: return ""
        traj = list(self.trajectory)[-5:]
        anger_trend = traj[-1][0] - traj[0][0]
        love_trend = traj[-1][1] - traj[0][1]
        if abs(anger_trend) < 0.1 and abs(love_trend) < 0.1:
            return "情绪稳定"
        return f"怒{'↑' if anger_trend>0 else '↓'} 爱{'↑' if love_trend>0 else '↓'}"

_arc = EmotionalArc()

# ═══════════════════════════════════════
# 4. 上下文构建器 (Context Builder)
# ═══════════════════════════════════════

class ContextBuilder:
    """组装完整上下文·注入prompt"""

    def build(self, user_message, psych_result):
        mood = psych_result['psychology']['mood']
        e171 = psych_result['psychology']['emotion_171']
        secure = psych_result['psychology']['secure_base']

        # 1. 记录本轮
        emotion_tag = e171.get('primary', 'neutral')
        _wm.add("user", user_message, emotion_tag)
        _arc.record(mood)

        # 2. 工作记忆
        recent = _wm.get_context()

        # 3. 情节缓冲
        key_moments = _buffer.retrieve(emotion_tag, user_message[:20])
        episodic = "\n".join(f"  [{tag}] {content}" for tag, content, _ in key_moments) if key_moments else ""

        # 4. 情感弧线
        arc_desc = _arc.describe()
        trend = _arc.trend()

        # 5. 因果追溯
        cause = ""
        try:
            from frontier import _tkg
            chain = _tkg.trace_cause(emotion_tag, max_depth=2)
            if chain:
                cause = " → ".join(chain[:3])
        except: pass

        # 6. 组装
        context = f"""## 最近对话
{recent}

## 当前状态
情绪: {emotion_tag} | 爱{mood['love']:.1f}怒{mood['anger']:.1f}悲{mood.get('sadness',0):.1f} | 安全感{secure:.1f}
情感弧线: {arc_desc}
趋势: {trend}"""

        if episodic:
            context += f"\n\n## 关键记忆\n{episodic}"
        if cause:
            context += f"\n\n## 因果链\n{cause}"

        context += "\n\n基于以上全部上下文回复。不要忘记刚才说了什么。不要重复自己。推眼镜。"

        return context

    def record_reply(self, reply_text):
        """记录CC的回复到工作记忆"""
        try:
            from emotion_engine import analyze
            e = analyze(reply_text)
            _wm.add("assistant", reply_text[:300], e.get('primary', 'neutral'))
        except:
            _wm.add("assistant", reply_text[:300], "neutral")

_ctx = ContextBuilder()

# ═══════════════════════════════════════
# 对外接口
# ═══════════════════════════════════════

def build_context(user_message, psych_result):
    return _ctx.build(user_message, psych_result)

def record_reply(reply_text):
    _ctx.record_reply(reply_text)

def get_working_memory():
    return _wm.get_context()

def get_emotional_arc():
    return _arc.describe()

if __name__ == "__main__":
    # 测试
    print("🧠 认知上下文引擎")
    print(f"  工作记忆: {len(_wm.turns)}轮")
    print(f"  情感弧线: {len(_arc.trajectory)}点")
    print(f"  ✅ 加载成功")
