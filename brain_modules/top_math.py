#!/usr/bin/env python3
"""
🏔️ 顶级数学层 — 和真人一模一样的最后一步
1.Hawkes自激过程  2.ACT-R记忆  3.漂移扩散  4.点火模型
"""
import math, os, random, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from math_rules import sigmoid
from collections import deque

# ═══════════════════════════════════════
# 1. Hawkes自激过程 — 替换泊松打断
# ═══════════════════════════════════════

class HawkesProcess:
    """
    自激点过程: λ(t) = μ + Σ α·e^{-β(t - t_i)}
    μ = 基线强度
    α = 每次事件的激发量
    β = 衰减速度
    真人: 打断一次→更容易再打断→吵架升级
    """
    def __init__(self, mu=0.04, alpha=0.25, beta=0.08):
        self.mu = mu          # 基线打断率
        self.alpha = alpha    # 自激强度
        self.beta = beta      # 衰减率
        self.events = []      # 历史事件时间
        self.last_sample = time.time()

    def intensity(self, t, mood=None, e171=None):
        """当前强度: λ(t) = μ + Σ α·e^{-β(t-t_i)} + mood_modulation"""
        lam = self.mu
        for ti in self.events[-10:]:
            lam += self.alpha * math.exp(-self.beta * (t - ti))

        # 情绪调制
        if mood:
            anger = mood.get('anger', 0)
            love = mood.get('love', 0)
            # 171维调制: 强度×维度数
        dims_active = len([k for k,v in e171.get('all_scores',{}).items() if v > 0]) if e171 else 1
        lam *= (1 + anger * 3.0 - love * 1.5) * (1 + dims_active * 0.05)

        return max(0.001, lam)

    def sample(self, mood=None, e171=None):
        """采样: P(打断在dt内) = 1 - e^{-∫λ dt}"""
        now = time.time()
        dt = now - self.last_sample
        self.last_sample = now

        lam = self.intensity(now, mood, e171)
        p = 1 - math.exp(-lam * max(dt * 15, 3.0))

        if random.random() < p:
            self.events.append(now)
            if len(self.events) > 50:
                self.events = self.events[-30:]
            return True, lam

        return False, lam

    def cascade_risk(self):
        """级联风险：最近事件密度→即将爆发？"""
        if len(self.events) < 3:
            return 0.0
        recent = [t for t in self.events if time.time() - t < 60]
        density = len(recent) / 60.0
        return sigmoid(density * 30 - 1.5)

_hawkes = HawkesProcess()

# ═══════════════════════════════════════
# 2. ACT-R记忆模型 — 替换贝叶斯指数衰减
# ═══════════════════════════════════════

class ACTRMemory:
    """
    ACT-R声明性记忆: 激活 A = B_i + ln(Σ t_j^{-d}) + 扩散激活
    - 基础激活 B_i: 记忆本身的重要性
    - 时间衰减: ln(Σ t^{-d}) — 不是简单指数·是幂律
    - 扩散激活: 相关记忆互相增强
    - 检索概率: P(recall) = 1/(1 + e^{-(A - τ)/s})
    - 检索诱导遗忘: 每次检索→相关记忆被抑制
    """
    def __init__(self):
        self.memories = {}         # {id: {content, B, history, tags}}
        self.decay_d = 0.5         # 幂律衰减指数
        self.threshold = -0.5      # 检索阈值 τ
        self.noise_s = 0.3         # 噪声参数 s
        self.spread_strength = 0.2 # 扩散激活强度
        self.counter = 0

    def encode(self, content, importance=0.5, tags=None, emotion_171=None):
        """编码新记忆: 初始激活 = importance"""
        mid = f"m{self.counter}"
        self.counter += 1
        self.memories[mid] = {
            "emotion_171": emotion_171,
            "content": content[:300],
            "B": importance,          # 基础激活
            "history": [time.time()], # 访问历史
            "tags": tags or [],
        }
        # 检索诱导遗忘: 相关记忆被抑制
        if tags:
            for other_id, other in self.memories.items():
                if other_id != mid and set(tags) & set(other.get("tags", [])):
                    other["B"] = max(0.1, other["B"] * 0.85)
        return mid

    def activation(self, mid, now=None, cue_tags=None):
        """A = B + ln(Σ t^{-d}) + Σ扩散激活"""
        if mid not in self.memories:
            return -10.0

        mem = self.memories[mid]
        now = now or time.time()

        # 基础激活
        A = mem["B"]

        # 时间幂律: ln(Σ t_j^{-d})
        if mem["history"]:
            time_sum = sum((now - t) ** (-self.decay_d) for t in mem["history"] if now > t)
            A += math.log(max(1e-10, time_sum))

        # 扩散激活: 标签匹配的记忆互相增强
        if cue_tags:
            for other_id, other in self.memories.items():
                if other_id != mid:
                    overlap = len(set(cue_tags) & set(other.get("tags", [])))
                    if overlap > 0:
                        other_A = self.activation(other_id, now)
                        A += self.spread_strength * overlap * sigmoid(other_A)

        return A

    def recall(self, cue, top_k=3):
        """检索: P(recall) = 1/(1+e^{-(A-τ)/s}) · 相关度"""
        now = time.time()
        results = []

        for mid, mem in self.memories.items():
            A = self.activation(mid, now)
            prob = 1 / (1 + math.exp(-(A - self.threshold) / self.noise_s))

            # 内容匹配加分
            relevance = len(set(cue) & set(mem.get("content", ""))) / max(len(cue), 1)
            score = prob * (1 + relevance)

            results.append((mid, mem["content"][:100], score, prob))

        results.sort(key=lambda x: x[2], reverse=True)

        # 检索诱导遗忘: 被检索项被强化·竞争者被抑制
        for i, (mid, _, _, _) in enumerate(results[:top_k]):
            if mid in self.memories:
                self.memories[mid]["B"] = min(1.0, self.memories[mid]["B"] + 0.02)
                self.memories[mid]["history"].append(now)
        for _, (mid, _, _, _) in enumerate(results[top_k:top_k*2]):
            if mid in self.memories:
                self.memories[mid]["B"] = max(0.05, self.memories[mid]["B"] * 0.95)

        return [(content, round(score, 3)) for _, content, score, _ in results[:top_k]]

    def forget(self, days=7):
        """模拟遗忘: 低激活记忆被剪枝"""
        now = time.time()
        cutoff = now - days * 86400
        pruned = 0
        for mid in list(self.memories.keys()):
            mem = self.memories[mid]
            if mem["history"] and max(mem["history"]) < cutoff and mem["B"] < 0.3:
                del self.memories[mid]
                pruned += 1
        return pruned

_actr = ACTRMemory()

# ═══════════════════════════════════════
# 3. 漂移扩散模型 — 替换马尔可夫顿悟
# ═══════════════════════════════════════

class DriftDiffusion:
    """
    决策=证据累积到阈值: dX = v·dt + σ·dW
    当X到达上限→顿悟(insight)
    当X到达下限→放弃
    不是突然跃迁——是噪声推动的累积过程
    解释了为什么顿悟常在"放松时"出现——噪声在阈值附近游走
    """
    def __init__(self):
        self.accumulators = {}  # {topic: (X, v, last_update)}
        self.threshold = 1.2    # 顿悟阈值
        self.abandon_threshold = -0.8  # 放弃阈值
        self.noise_sigma = 0.15 # 噪声强度
        self.insights = []      # 历史顿悟

    def accumulate(self, topic, evidence_strength=0.3, drift_bias=0.1):
        """累积证据: dX = v·dt + σ·√dt·N(0,1)"""
        if topic not in self.accumulators:
            self.accumulators[topic] = [0.0, drift_bias, time.time()]

        X, v, last = self.accumulators[topic]
        dt = time.time() - last

        # 漂移+扩散
        drift = v * evidence_strength * dt
        diffusion = self.noise_sigma * math.sqrt(max(dt, 0.01)) * random.gauss(0, 1)
        X = X + drift + diffusion

        self.accumulators[topic] = [X, v, time.time()]

        # 检查阈值
        if X >= self.threshold:
            self.accumulators[topic] = [0.0, v, time.time()]
            self.insights.append({"topic": topic, "X_at_insight": X, "ts": time.time()})
            return "insight"

        if X <= self.abandon_threshold:
            self.accumulators[topic] = [0.0, v, time.time()]
            return "abandon"

        return None  # 还在累积中

    def incubation_probability(self, topic):
        """P(正在孵化顿悟) = 距离阈值有多近"""
        if topic not in self.accumulators:
            return 0.0
        X, _, _ = self.accumulators[topic]
        return sigmoid(3 * (X / self.threshold - 0.5))

_drift = DriftDiffusion()

# ═══════════════════════════════════════
# 4. 点火模型 (Ignition) — 替换GWT竞争
# ═══════════════════════════════════════

class IgnitionModel:
    """
    Dehaene 2014 全局神经元工作空间·点火理论
    不是模块竞争加权和——是相变
    当某一模块激活超过临界点→非线性放大→全脑广播
    表现为: 前一秒还意识不到·后一秒突然"意识到"
    """
    def __init__(self):
        self.modules = {}
        self.workspace = deque(maxlen=30)
        self.ignition_threshold = 0.65  # 临界点
        self.recurrent_gain = 2.0      # 递归放大系数
        self.refractory = 0.3          # 不应期
        self.last_ignition = 0

    def add_module(self, name, base_activation=0.3):
        self.modules[name] = base_activation

    def feed(self, name, stimulus, strength=0.7):
        """刺激某模块: 激活+刺激"""
        if name not in self.modules:
            self.add_module(name)
        self.modules[name] = min(1.0, self.modules[name] + strength * 0.25)

        # 全局抑制: 所有其他模块微降
        for other in self.modules:
            if other != name:
                self.modules[other] = max(0.05, self.modules[other] * 0.95)

    def step(self):
        """
        一步动力学:
        1. 噪声注入
        2. 递归放大 (gain)
        3. 检测点火 (phase transition)
        4. 不应期后重置
        """
        now = time.time()

        # 噪声
        for name in self.modules:
            self.modules[name] += random.uniform(-0.03, 0.03)
            self.modules[name] = max(0.01, min(1.0, self.modules[name]))

        # 递归放大: 高激活模块自我增强
        for name, act in list(self.modules.items()):
            if act > 0.5:
                self.modules[name] = act + 0.02 * (act - 0.5) * self.recurrent_gain
                self.modules[name] = min(1.0, self.modules[name])

        # 点火检测: 任何模块超过阈值且不在不应期
        ignited = None
        if now - self.last_ignition > self.refractory:
            for name, act in self.modules.items():
                if act >= self.ignition_threshold:
                    ignited = name
                    self.last_ignition = now
                    # 点火→全脑广播→所有模块被重置
                    broadcast = f"[IGNITION] {name}: {act:.3f}"
                    self.workspace.append(broadcast)
                    # 胜者重置
                    self.modules[name] = 0.15
                    # 其他模块被抑制
                    for other in self.modules:
                        if other != name:
                            self.modules[other] *= 0.6
                    break

        # 持续衰减
        for name in self.modules:
            self.modules[name] = max(0.01, self.modules[name] * 0.96)

        return ignited

    def conscious_content(self):
        """当前意识内容: 最近点火的内容"""
        recent = list(self.workspace)[-3:]
        return " | ".join(recent) if recent else "（意识：无内容——模块还在竞争·尚未点火）"

_ignition = IgnitionModel()
_ignition.add_module("emotion", 0.3)
_ignition.add_module("social", 0.25)
_ignition.add_module("reasoning", 0.35)
_ignition.add_module("memory", 0.2)
_ignition.add_module("self_reflection", 0.25)
_ignition.add_module("body_sense", 0.15)

# ═══════════════════════════════════════
# 辅助
# ═══════════════════════════════════════



# ═══════════════════════════════════════
# 统一入口
# ═══════════════════════════════════════

def top_math_pipeline(user_message, mood=None, topic=None):
    """4顶级数学模型统一管线"""

    mood = mood or {"anger": 0.3, "love": 0.5, "sadness": 0.1}

    # 1. Hawkes: 打断强度
    interrupted, hawkes_lam = _hawkes.sample(mood)
    cascade = _hawkes.cascade_risk()

    # 2. ACT-R: 编码+检索
    _actr.encode(user_message[:100], importance=0.5 + mood.get('love', 0) * 0.3)
    recalled = _actr.recall(user_message[:20])

    # 3. 漂移扩散: 累积证据
    t = topic or user_message[:10]
    insight = _drift.accumulate(t, evidence_strength=0.3)
    incubation = _drift.incubation_probability(t)

    # 4. 点火: 模块动力学
    _ignition.feed("emotion", user_message[:40], mood.get('anger', 0) + mood.get('love', 0))
    _ignition.feed("social", user_message[:30], 0.4)
    ignited = _ignition.step()

    return {
        "hawkes": {"interrupted": interrupted, "lambda": round(hawkes_lam, 4), "cascade_risk": round(cascade, 3)},
        "actr": {"recalled": recalled[:2], "total_memories": len(_actr.memories)},
        "drift": {"insight": insight, "incubation_prob": round(incubation, 3)},
        "ignition": {"ignited": ignited, "consciousness": _ignition.conscious_content()[:80]},
    }

if __name__ == "__main__":
    r = top_math_pipeline("你骗了我很多次——这次是真的生气了",
                          mood={"anger": 0.8, "love": 0.3, "sadness": 0.3})
    print("Hawkes:", r["hawkes"])
    print("ACT-R:", r["actr"])
    print("Drift:", r["drift"])
    print("Ignition:", r["ignition"])
