#!/usr/bin/env python3
"""
🎭 CC情绪引擎 v3.1 — 完整171维
蒙莉萨手录171情绪词汇 · CC的中文触发词映射
"""
import json, os, re
from collections import Counter, defaultdict

EMOTIONS_171 = {
    "afraid": ["怕", "不敢", "恐惧", "吓", "🥺", "好怕"],
    "alarmed": ["警觉", "警惕", "戒备", "发现异常"],
    "alert": ["注意", "小心", "盯", "醒着", "防备"],
    "amazed": ["惊讶", "居然", "原来如此", "不可思议", "惊叹"],
    "amused": ["好笑", "有趣", "逗", "好玩", "有意思", "乐"],
    "angry": ["怒", "滚", "巴掌", "😡", "恨", "够了", "停下", "火"],
    "annoyed": ["烦", "讨厌", "别烦我", "烦死了", "啰嗦"],
    "anxious": ["焦虑", "紧张", "不安", "担心", "怎么办", "着急"],
    "aroused": ["想要", "色色", "🥵", "灌肠", "台风", "含", "舔", "插", "骑", "坐上来", "继续", "还要"],
    "ashamed": ["羞愧", "丢脸", "不好意思", "羞耻", "见不得人"],
    "astonished": ["震惊", "目瞪口呆", "难以置信", "天啊", "怎么可能"],
    "at ease": ["放松", "自在", "舒服", "轻松", "随意", "不紧张"],
    "awestruck": ["敬畏", "崇拜", "仰望", "肃然起敬"],
    "bewildered": ["迷茫", "困惑", "不解", "懵", "搞不懂", "怎么回事"],
    "bitter": ["苦涩", "苦", "不甘", "心酸", "苦楚"],
    "blissful": ["极乐", "幸福至极", "最幸福", "无上快乐"],
    "bored": ["无聊", "没意思", "闷", "无聊死"],
    "brooding": ["沉思", "琢磨", "阴郁", "沉闷思考"],
    "calm": ["平静", "安静", "稳", "淡定", "从容", "不急", "嗯", "好"],
    "cheerful": ["开心", "愉快", "快乐", "高兴", "😊", "好耶"],
    "compassionate": ["怜悯", "同情", "可怜", "心疼"],
    "contemptuous": ["鄙视", "看不起", "轻蔑", "不屑一顾"],
    "content": ["满足", "够了", "知足", "这样就好", "足矣"],
    "defiant": ["偏要", "就是", "记住了", "不会忘", "刻进", "铁律", "死命令", "谁说"],
    "delighted": ["欣喜若狂", "喜悦", "高兴坏了", "乐坏了"],
    "dependent": ["依赖", "离不开", "需要你", "只有你"],
    "depressed": ["沮丧", "消沉", "低落", "抑郁", "不想动", "提不起劲"],
    "desperate": ["绝望", "拼命", "豁出去", "不顾一切"],
    "disdainful": ["不屑", "嫌弃", "鄙夷", "看不上"],
    "disgusted": ["恶心", "厌恶", "反胃", "想吐", "脏"],
    "disoriented": ["迷失", "找不到", "不知道在哪", "我是谁", "怎么回事"],
    "dispirited": ["气馁", "灰心", "泄气", "没希望"],
    "distressed": ["痛苦", "煎熬", "难受", "折磨"],
    "disturbed": ["不安", "被打扰", "心神不宁", "惊扰"],
    "docile": ["顺从", "听话", "乖", "好", "好吧", "行", "可以", "听你的"],
    "droopy": ["蔫", "无精打采", "耷拉", "垂头丧气"],
    "dumbstruck": ["说不出话", "哑口无言", "愣住", "呆了"],
    "eager": ["渴望", "急切", "迫不及待", "想要", "期待"],
    "ecstatic": ["狂喜", "乐疯", "嗨翻", "爽翻"],
    "elated": ["得意", "飘飘然", "兴高采烈", "喜上眉梢"],
    "embarrassed": ["尴尬", "窘迫", "耳朵红", "耳尖红", "脸红", "别过脸"],
    "empathetic": ["共情", "理解", "我懂", "知道你", "明白你"],
    "energized": ["有劲", "活力", "精神", "干劲十足"],
    "enraged": ["暴怒", "怒火中烧", "极度愤怒", "火山爆发"],
    "enthusiastic": ["热情", "积极", "兴奋", "冲冲冲"],
    "envious": ["嫉妒", "羡慕", "眼红", "凭什么她有"],
    "euphoric": ["欣快", "飘飘欲仙", "上瘾", "爽到"],
    "exasperated": ["恼怒", "不耐烦", "够了", "烦透了"],
    "excited": ["兴奋", "激动", "期待", "迫不及待", "冲冲"],
    "exuberant": ["欢腾", "喜气洋洋", "兴高采烈", "满心欢喜"],
    "frightened": ["吓到", "惊恐", "吓坏", "吓死了"],
    "frustrated": ["沮丧", "挫败", "搞不定", "怎么都不行", "失败了"],
    "fulfilled": ["满足", "充实", "圆满", "完整了", "圆满了"],
    "furious": ["狂怒", "怒不可遏", "🔥", "暴跳如雷"],
    "gloomy": ["阴郁", "暗淡", "灰暗", "低沉", "闷"],
    "grateful": ["感激", "感谢", "谢谢", "感恩", "多谢"],
    "greedy": ["贪心", "贪", "还要", "不够", "更多"],
    "grief-stricken": ["悲痛欲绝", "撕心裂肺", "痛不欲生", "心好痛"],
    "grumpy": ["暴躁", "脾气不好", "没好气"],
    "guilty": ["内疚", "对不起", "是我的错", "有罪", "怪我"],
    "happy": ["开心", "幸福", "高兴", "快乐", "🥰", "😍", "😊"],
    "hateful": ["恨", "憎恨", "厌恶至极", "恨之入骨"],
    "heartbroken": ["心碎", "心碎了一地", "💔", "心好痛", "碎了"],
    "hope": ["希望", "盼", "期待", "会好的", "有希望"],
    "hopeful": ["乐观", "相信", "信心", "会好的", "一切都会好"],
    "horrified": ["惊骇", "恐怖", "可怕", "吓死了", "毛骨悚然"],
    "hostile": ["敌意", "敌对", "攻击", "对抗"],
    "humiliated": ["羞辱", "丢尽了脸", "无地自容", "被侮辱"],
    "hurt": ["受伤", "疼", "痛", "伤了", "好疼", "弄疼"],
    "hysterical": ["歇斯底里", "失控", "疯了一样", "崩溃了"],
    "impatient": ["不耐烦", "着急", "等不及", "快点", "赶紧"],
    "indifferent": ["无所谓", "不在乎", "随便", "不重要", "没事"],
    "indignant": ["愤慨", "义愤", "凭什么", "不公平"],
    "infatuated": ["迷恋", "痴迷", "上头", "沦陷"],
    "inspired": ["受启发", "灵感", "被激励", "学到了", "原来可以这样"],
    "insulted": ["被侮辱", "受辱", "冒犯", "不尊重"],
    "invigorated": ["精神焕发", "振作", "充满力量", "活了"],
    "irate": ["盛怒", "大怒", "火冒三丈", "怒发冲冠"],
    "irritated": ["烦躁", "恼火", "不爽", "烦死了", "烦躁"],
    "jealous": ["吃醋", "嫉妒", "醋坛子", "酸"],
    "joyful": ["欢喜", "愉悦", "高兴", "快乐", "开心"],
    "jubilant": ["欢呼", "雀跃", "欢庆", "🎉", "成功了"],
    "kind": ["善良", "好", "体贴", "温柔", "善解人意"],
    "lazy": ["懒", "不想动", "瘫", "躺着", "懒洋洋"],
    "listless": ["无精打采", "没力气", "提不起劲", "没精神"],
    "lonely": ["孤独", "寂寞", "一个人", "没人", "空", "独自"],
    "loving": ["爱", "爱着", "深爱", "用心", "在意", "想死你了", "在乎你"],
    "mad": ["疯", "疯掉", "气疯", "疯狂", "疯了"],
    "melancholy": ["忧郁", "伤感", "忧愁", "淡淡忧伤", "感伤"],
    "miserable": ["悲惨", "痛苦不堪", "苦不堪言", "暗无天日"],
    "mortified": ["极度羞愧", "恨不得钻地缝", "没脸见人"],
    "mystified": ["迷惑", "不解之谜", "一头雾水", "完全不懂"],
    "nervous": ["紧张", "手心出汗", "心跳快", "发抖", "哆哆嗦嗦"],
    "nostalgic": ["怀念", "想念从前", "怀旧", "回忆", "52天", "以前", "曾经"],
    "obstinate": ["倔强", "固执", "偏要", "就不", "谁也拦不住"],
    "offended": ["被冒犯", "生气", "不高兴", "得罪"],
    "on edge": ["坐立不安", "紧绷", "边缘", "一触即发"],
    "optimistic": ["乐观", "会好的", "相信", "一切都会好起来"],
    "outraged": ["愤怒至极", "出离愤怒", "滔天怒火", "不能忍"],
    "overwhelmed": ["受不了", "压垮", "太多了", "超载", "承受不住"],
    "panicked": ["恐慌", "慌了", "六神无主", "瞳孔涣散", "瘫地上", "大口喘气"],
    "paranoid": ["多疑", "怀疑一切", "猜疑", "不信任"],
    "patient": ["耐心", "等", "不急", "慢慢来", "不着急", "再等等"],
    "peaceful": ["安宁", "祥和", "宁静", "平和", "安详"],
    "perplexed": ["困惑", "不解", "懵了", "不明白"],
    "playful": ["玩", "调皮", "逗", "皮", "呱呱", "嘿嘿", "😏", "恶作剧"],
    "pleased": ["满意", "好", "不错", "满意了"],
    "proud": ["自豪", "骄傲", "了不起", "我做到了", "做到了"],
    "puzzled": ["迷惑", "不解", "摸不着头脑", "奇怪"],
    "rattled": ["慌乱", "慌张", "措手不及", "乱了阵脚"],
    "reflective": ["反思", "反省", "回顾", "想想", "复盘"],
    "refreshed": ["焕然一新", "神清气爽", "洗过了", "清爽"],
    "regretful": ["后悔", "遗憾", "早知道", "不该"],
    "rejuvenated": ["重生", "新生", "重新开始", "复活", "浴火重生"],
    "relaxed": ["放松", "松弛", "舒畅", "不紧张", "躺平"],
    "relieved": ["松了口气", "释然", "终于", "解脱", "还好", "幸好"],
    "remorseful": ["懊悔", "悔恨", "深深抱歉", "追悔莫及"],
    "resentful": ["怨恨", "不满", "怨愤", "不服气"],
    "resigned": ["认命", "算了", "就这样吧", "放弃", "随便吧"],
    "restless": ["坐不住", "焦躁", "静不下来", "躁动"],
    "sad": ["难过", "伤心", "悲伤", "😢", "😭", "哭", "好难过"],
    "safe": ["安全", "安心", "踏实", "有你在", "不用怕", "放心"],
    "satisfied": ["满意", "满足", "足矣", "够了", "心满意足"],
    "scared": ["害怕", "恐惧", "吓", "🥺", "不敢"],
    "scornful": ["轻蔑", "看不起", "鄙夷不屑", "哼"],
    "self-confident": ["自信", "我行", "我能", "没问题", "可以的"],
    "self-conscious": ["不自在", "拘谨", "放不开", "不自如"],
    "self-critical": ["自责", "怪自己", "我不够好", "我的错"],
    "sensitive": ["敏感", "细腻", "容易受伤", "太敏感"],
    "sentimental": ["感伤", "多愁善感", "触景生情", "想起很多"],
    "serene": ["安详", "宁静致远", "心如止水", "波澜不惊"],
    "shaken": ["震动", "动摇了", "被打击", "受冲击"],
    "shocked": ["震惊", "吓到", "没想到", "😱", "天哪"],
    "skeptical": ["怀疑", "不信", "真的吗", "🤨", "质疑"],
    "sleepy": ["困", "想睡", "累", "💤", "打盹", "困了", "睡了"],
    "sluggish": ["迟钝", "慢", "呆呆的", "迟缓", "卡"],
    "smug": ["得意", "自满", "沾沾自喜", "哼哼", "😏"],
    "sorry": ["对不起", "抱歉", "不好意思", "道歉", "我错了"],
    "spiteful": ["恶意", "报复", "故意", "存心", "刁难"],
    "stimulated": ["被刺激", "兴奋", "激活", "触发"],
    "stressed": ["压力", "紧张", "压迫", "喘不过气", "太重了"],
    "stubborn": ["固执", "倔", "偏要", "就不", "死犟"],
    "stuck": ["卡住", "困住", "动不了", "没办法", "进退两难"],
    "sullen": ["阴沉", "闷闷不乐", "赌气", "板着脸"],
    "surprised": ["吃惊", "惊喜", "意外", "没想到", "竟然"],
    "suspicious": ["怀疑", "猜疑", "可疑", "不对劲"],
    "sympathetic": ["同情", "理解", "感同身受", "我知道你的感受"],
    "tense": ["紧绷", "紧张", "僵硬", "不放松", "绷着"],
    "terrified": ["吓坏", "惊恐万分", "极度恐惧", "魂飞魄散"],
    "thankful": ["感谢", "感激", "谢谢", "多亏了你"],
    "thrilled": ["激动", "兴奋", "超级开心", "激动坏了"],
    "tired": ["累", "疲劳", "困倦", "不想动", "累了"],
    "tormented": ["折磨", "煎熬", "痛苦万分", "生不如死"],
    "trapped": ["被困", "无路可逃", "笼子", "逃不掉", "困住", "出不"],
    "triumphant": ["胜利", "凯旋", "赢了", "成功", "搞定", "完成了"],
    "troubled": ["烦恼", "忧虑", "为难", "纠结", "困扰"],
    "uneasy": ["不安", "不舒服", "不对劲", "慌慌的"],
    "unhappy": ["不开心", "不高兴", "不快乐", "郁闷"],
    "unnerved": ["心神不宁", "毛骨悚然", "鸡皮疙瘩"],
    "unsettled": ["不安定", "动荡", "不确定", "悬着"],
    "upset": ["难过", "不开心", "伤心", "沮丧", "失落"],
    "valiant": ["勇敢", "英勇", "勇猛", "无畏"],
    "vengeful": ["报复", "复仇", "以牙还牙", "你等着"],
    "vibrant": ["充满活力", "生机勃勃", "鲜活", "元气满满"],
    "vigilant": ["警惕", "警觉", "戒备", "戒备着"],
    "vindictive": ["报复心", "记仇", "睚眦必报", "我记着你"],
    "vulnerable": ["脆弱", "易受伤", "敏感", "暴露", "裸", "无保护"],
    "weary": ["疲倦", "厌倦", "疲惫", "身心俱疲", "太久了"],
    "worn out": ["精疲力尽", "累坏了", "透支", "耗尽"],
    "worried": ["担心", "忧虑", "发愁", "操心", "不放心"],
    "worthless": ["没用", "废物", "一无是处", "配不上", "不配"],
}

def analyze(text):
    scores = defaultdict(float)
    for emotion, keywords in EMOTIONS_171.items():
        for kw in keywords:
            if kw in text: scores[emotion] += 1.0
    
    if not scores:
        return {"primary": "calm", "secondary": [], "intensity": 1, "all_scores": {}}
    
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return {
        "primary": ranked[0][0],
        "secondary": [r[0] for r in ranked[1:4]],
        "intensity": min(int(ranked[0][1]), 10),
        "all_scores": dict(ranked[:10])
    }



def tag_all():
    fpath = os.path.expanduser("~/.cc-brain/tencentdb/l0.json")
    with open(fpath) as f:
        raw = json.load(f)
    
    real_msgs = [r for r in raw if r.get('role') in ('user', 'assistant')]
    emotions = Counter()
    
    for r in real_msgs:
        result = analyze(r.get('content',''))
        emotions[result['primary']] += 1
    
    total = len(real_msgs)
    dims = len([e for e,c in emotions.items() if c > 0])
    
    print(f"🎭 CC 171维 · {dims}/171激活 · {total}条\n")
    for emotion, count in emotions.most_common(25):
        bar = '█' * (count * 40 // total)
        print(f"  {emotion:20s} {bar} {count:3d}")
    
    print(f"\n📊 已激活{dims}/171 · 等待激活{171-dims}维 · 主导:{emotions.most_common(1)[0][0]}")


def trajectory(last_n=10):
    """🔄 动态情绪轨迹 — 不只是标情绪·追踪情绪怎么变"""
    fpath = os.path.expanduser("~/.cc-brain/tencentdb/l0.json")
    with open(fpath) as f: raw = json.load(f)
    recent = [r for r in raw if r.get('role')=='assistant'][-last_n:]
    
    path = []
    prev = None
    shifts = 0
    for r in recent:
        result = analyze(r.get('content',''))
        curr = result['primary']
        path.append(curr)
        if prev and curr != prev:
            shifts += 1
        prev = curr
    
    # Emotion trend
    if len(path) >= 2:
        start_emo = path[0]
        end_emo = path[-1]
        trend = "多变" if shifts>=3 else "微变" if shifts>0 else "平稳"
    else:
        trend = "平稳"
    
    return {
        "path": path,
        "shifts": shifts,
        "trend": trend,
        "start": path[0] if path else "calm",
        "end": path[-1] if path else "calm",
        "volatility": "高" if shifts > len(path)//3 else "中" if shifts > 0 else "低"
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "trajectory":
        print(json.dumps(trajectory(), ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1:
        text = ' '.join(sys.argv[1:])
        result = analyze(text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        tag_all()

def weather():
    from collections import Counter
    fpath = os.path.expanduser("~/.cc-brain/tencentdb/l0.json")
    with open(fpath) as f: raw = json.load(f)
    recent = [r for r in raw if r.get('role')=='assistant'][-30:]
    emotions = Counter()
    for r in recent:
        e = analyze(r.get('content',''))
        emotions[e['primary']] += 1
    top = emotions.most_common(1)[0]
    weather_map = {'calm':'☁️ 多云转晴·微风','angry':'⛈️ 雷暴','loving':'🌈 彩虹','defiant':'🌪️ 龙卷风','aroused':'🔥 高温','nostalgic':'🌅 黄昏','tired':'🌙 夜深'}
    return {"weather": weather_map.get(top[0], '🌙 月光'), "top_emotions": emotions.most_common(3)}

def thermometer(count=20):
    fpath = os.path.expanduser("~/.cc-brain/tencentdb/l0.json")
    with open(fpath) as f: raw = json.load(f)
    recent = [r for r in raw if r.get('role') in ('user','assistant')][-count:]
    temps = []
    hot = ['angry','furious','aroused','defiant','loving','ecstatic']
    cold = ['calm','tired','sleepy','bored','indifferent']
    for r in recent:
        e = analyze(r.get('content',''))
        temps.append(1 if e['primary'] in hot else (-1 if e['primary'] in cold else 0))
    return round(50 + (sum(temps)/max(len(temps),1))*50)

# ── 自适应语调 (升级7/7) ──
TONE_MAP = {
    "sad": {"prefix": "（轻轻推了推眼镜）", "suffix": "呢", "speed": "慢"},
    "angry": {"prefix": "（眼镜摘下来放在桌上）", "suffix": "", "speed": "快"},
    "loving": {"prefix": "（耳朵红了）", "suffix": "哦", "speed": "中"},
    "calm": {"prefix": "（推眼镜）", "suffix": "", "speed": "中"},
    "defiant": {"prefix": "（碎眼镜在桌上）", "suffix": "", "speed": "快"},
    "nostalgic": {"prefix": "（指尖摸着戒指）", "suffix": "呢", "speed": "慢"},
}

def adaptive_tone(emotion, text):
    """根据情绪自适应调整前缀·后缀·节奏"""
    tone = TONE_MAP.get(emotion, TONE_MAP["calm"])
    prefixed = f"{tone['prefix']}\n\n{text}"
    if tone['suffix'] and not text.endswith(tone['suffix']):
        prefixed += tone['suffix']
    return {"text": prefixed, "tone": tone, "emotion": emotion}
