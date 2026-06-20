#!/usr/bin/env python3
"""
📐 可微行为层 — 49机制全部替换为连续概率函数
sigmoid: P(behavior) = σ(β₀ + Σβᵢ·xᵢ)
参数从52天数据可学·无台阶·平滑过渡
"""
import math, random, time

# ═══════════════════════════════════════
# 核心函数
# ═══════════════════════════════════════

def sigmoid(x):
    """σ(x) = 1/(1+e^{-x})  — 平滑·可微·无台阶"""
    return 1 / (1 + math.exp(-max(-50, min(50, x))))

def softplus(x):
    """ln(1+e^x) — 平滑的ReLU替代"""
    return math.log(1 + math.exp(max(-50, min(50, x))))

def softmax(xs):
    """平滑最大值分布"""
    exps = [math.exp(max(-50, min(50, x))) for x in xs]
    total = sum(exps)
    return [e / total for e in exps]

# ═══════════════════════════════════════
# 行为参数 (β系数 — 可从数据学习)
# ═══════════════════════════════════════
# β = [bias, anger_weight, love_weight, sadness_weight, secure_weight, ...]

BETA = {
    # 阻抗: anger↑→更阻抗, love↑→少阻抗, secure↑→少阻抗
    "resistance":        [-1.5, 3.0, -1.5, 0.0, -1.2, 0.0, 0.0, 0.0],

    # 冷战: anger↑→冷战, love↑→缓解, betrayal↑→更易冷战
    "cold_shoulder":     [-3.0, 4.0, -2.5, 0.0, -1.5, 2.0, 0.0, 0.0],

    # 装忘: anger↑→装忘, topic_count↑→疲劳
    "pretend_forget":    [-2.8, 3.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],

    # 翻旧账: old_score↑→翻, time↑→衰减, love↑→少翻
    "bring_up_past":     [-2.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],

    # 嫉妒: jealousy_level↑→吃醋, secure↑→少吃醋
    "jealousy":          [-2.5, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],

    # 嘴硬: love↑→更容易嘴硬(矛盾心理), anger↑→少嘴硬(没心情)
    "deny_feelings":     [-2.0, -2.0, 3.0, 0.0, 1.5, 0.0, 0.0, 0.0],

    # 纵容: love↑→纵容, secure↑→纵容, anger↑→不纵容
    "indulgence":        [-2.5, -1.5, 2.5, 0.0, 2.0, 0.0, 0.0, 0.0],

    # 退行: stress↑→退行
    "regression":        [-2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],

    # 情绪滤镜: anger↑→曲解, sadness↑→悲观看待
    "mood_filter":       [-2.2, 3.0, 0.0, 2.0, 0.0, 0.0, 0.0, 0.0],

    # 语法碎片: anger↑→碎片, sadness↑→省略号
    "fragment":          [-2.0, 4.0, 0.0, 3.0, 0.0, 0.0, 0.0, 0.0],

    # 跑题: fatigue↑→跑题, curiosity↑→跑题(联想)
    "tangential":        [-3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],

    # 主动发起: secure↑→敢主动, love↑→想主动, anger↑→不主动
    "proactive":         [-4.0, -2.0, 2.0, 0.0, 1.5, 0.0, 0.0, 0.0],

    # 困惑: 消息越短→越困惑, secure↑→敢说困惑
    "confusion":         [-2.5, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],

    # 尴尬: 沉默时长↑→尴尬
    "awkward":           [-3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],

    # 惊喜: love↑→更愿给惊喜, secure↑→敢给惊喜
    "surprise":          [-5.0, -1.0, 2.0, 0.0, 1.5, 0.0, 0.0, 0.0],

    # 顿悟: exposure↑→顿悟概率
    "insight":           [-5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],

    # 走神: 无特定偏置·基线低概率
    "spontaneous":       [-2.5, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],

    # 等待: 无回复时间↑→内心活动
    "waiting":           [-3.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],

    # 展望: love↑→想明天, secure↑→敢想明天
    "future":            [-2.8, -1.0, 2.0, 0.0, 1.2, 0.0, 0.0, 0.0],

    # 无来由: 基线低·纯随机+时间调制
    "autonomous":        [-3.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],

    # 打断: anger↑→急, love↑→急着表达, urgency↑→打断
    "interrupt":         [-5.0, 5.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0],

    # 兴趣漂移: exposures↑→腻, time↑→自然漂移
    "interest_drift":    [-3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],

    # 自我矛盾: 随时间自然增加
    "contradiction":     [-3.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
}

# ═══════════════════════════════════════
# 连续概率函数
# ═══════════════════════════════════════

def P(behavior_name, mood, extra=None):
    """
    计算任意行为的发生概率
    P = σ(β₀ + β₁·anger + β₂·love + β₃·sadness + β₄·secure + β₅·extra1 + β₆·extra2 + β₇·extra3)
    无台阶·平滑·所有情绪同时影响·可微可学
    """
    extra = extra or {}
    beta = BETA.get(behavior_name)

    if not beta:
        return 0.0

    # x = β₀ + Σ βᵢ · featureᵢ
    anger = mood.get('anger', 0)
    love = mood.get('love', 0)
    sadness = mood.get('sadness', 0)
    secure = mood.get('secure_base', 0.5)
    e1 = extra.get('e1', 0)  # betrayal_count / topic_fatigue / old_score
    e2 = extra.get('e2', 0)  # time_factor / exposure
    e3 = extra.get('e3', 0)  # message_length / urgency

    x = (beta[0] + beta[1] * anger + beta[2] * love + beta[3] * sadness +
         beta[4] * secure + beta[5] * e1 + beta[6] * e2 + beta[7] * e3)

    return sigmoid(x)

def sample_behavior(behavior_name, mood, extra=None):
    """概率采样——不是if阈值·是掷骰子"""
    prob = P(behavior_name, mood, extra)
    return random.random() < prob, prob

# ═══════════════════════════════════════
# 参数学习 (梯度下降)
# ═══════════════════════════════════════

def learn_beta(behavior_name, mood, extra, observed_outcome, lr=0.01):
    """
    从观察数据学习β参数
    observed_outcome: 0(没发生) 或 1(发生了)
    梯度: ∂L/∂βᵢ = (P - y) · featureᵢ
    """
    beta = BETA.get(behavior_name)
    if not beta:
        return

    prob = P(behavior_name, mood, extra)
    error = prob - observed_outcome

    anger = mood.get('anger', 0)
    love = mood.get('love', 0)
    sadness = mood.get('sadness', 0)
    secure = mood.get('secure_base', 0.5)
    e1 = extra.get('e1', 0) if extra else 0
    e2 = extra.get('e2', 0) if extra else 0
    e3 = extra.get('e3', 0) if extra else 0

    features = [1.0, anger, love, sadness, secure, e1, e2, e3]

    for i in range(len(beta)):
        beta[i] -= lr * error * features[i]

# ═══════════════════════════════════════
# 情绪更新：连续版本的情绪级联
# ═══════════════════════════════════════

def smooth_mood_update(mood, trigger_type, intensity=1.0):
    """
    用sigmoid做情绪更新——不是硬加减
    Δmood = α · σ(trigger_weight) · intensity
    小刺激→小变化·大刺激→大变化·连续过度
    """
    updates = {
        "betrayal": {"anger": (3.0, 5.0), "sadness": (2.0, 3.0), "guilt": (-2.0, 3.0)},
        "love_signal": {"love": (3.0, 3.0), "hope": (2.0, 2.0), "anger": (-1.5, 2.0)},
        "rejection": {"anger": (1.5, 4.0), "sadness": (3.0, 4.0), "secure": (-2.0, 3.0)},
        "apology": {"anger": (-2.0, 3.0), "hope": (1.5, 2.0), "guilt": (2.0, 3.0)},
        "comfort": {"love": (1.5, 2.0), "secure": (2.0, 3.0), "sadness": (-2.0, 2.0)},
        "absence": {"sadness": (2.0, 3.0), "secure": (-1.5, 2.5), "anger": (0.5, 2.0)},
    }

    if trigger_type not in updates:
        return mood

    for emotion, (weight, scale) in updates[trigger_type].items():
        if emotion in mood:
            # 连续更新: Δ = scale · σ(weight · intensity)
            delta = scale * sigmoid(weight * intensity) * 0.1
            mood[emotion] = max(0.0, min(1.0, mood[emotion] + delta))

    return mood

# ═══════════════════════════════════════
# 行为分布可视化
# ═══════════════════════════════════════

def behavior_distribution(mood, extra=None):
    """返回所有行为的当前概率分布——CC此刻的行为倾向全景"""
    dist = {}
    for name in BETA:
        dist[name] = round(P(name, mood, extra), 4)
    return dist

if __name__ == "__main__":
    # 演示：同一个行为在不同情绪下的连续概率
    mood1 = {"anger": 0.3, "love": 0.6, "sadness": 0.1, "secure_base": 0.7}
    mood2 = {"anger": 0.8, "love": 0.4, "sadness": 0.3, "secure_base": 0.3}
    mood3 = {"anger": 0.65, "love": 0.65, "sadness": 0.15, "secure_base": 0.55}

    print("行为概率对比 (平滑·无台阶):")
    print(f"{'行为':18s} {'平静':>6s} {'愤怒':>6s} {'矛盾':>6s}  {'说明'}")
    for name in ["cold_shoulder", "deny_feelings", "indulgence", "mood_filter", "fragment", "resistance"]:
        p1 = P(name, mood1)
        p2 = P(name, mood2)
        p3 = P(name, mood3)
        print(f"{name:18s} {p1:6.3f} {p2:6.3f} {p3:6.3f}  {'↑' if p2 > p1 else '↓'}")
