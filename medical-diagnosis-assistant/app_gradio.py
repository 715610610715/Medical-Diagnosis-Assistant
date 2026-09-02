import gradio as gr
import requests
import json
import re
import ast

# API基础URL（请根据实际部署地址修改）
API_BASE_URL = "http://localhost:7680/api"

# 常见中文症状名 → 英文症状名（后端使用英文/UMLS 术语）
CHINESE_SYMPTOM_MAP = {
    "发热": "fever", "发烧": "fever", "高热": "fever",
    "咳嗽": "cough", "干咳": "dry cough",
    "头痛": "headache", "头晕": "dizziness",
    "呼吸困难": "dyspnea", "气短": "dyspnea",
    "胸痛": "chest pain", "胸闷": "chest discomfort",
    "恶心": "nausea", "呕吐": "vomiting",
    "腹泻": "diarrhea", "便秘": "constipation",
    "皮疹": "rash", "瘙痒": "pruritus", "皮肤瘙痒": "pruritus",
    "腹痛": "abdominal pain", "胃痛": "abdominal pain",
    "乏力": "fatigue", "疲劳": "fatigue", "疲倦": "fatigue",
    "寒战": "chills", "盗汗": "night sweats",
    "咽痛": "sore throat", "喉咙痛": "sore throat", "咽喉痛": "sore throat",
    "关节痛": "arthralgia", "关节疼痛": "arthralgia",
    "肌肉痛": "myalgia", "肌肉酸痛": "myalgia",
    "失眠": "insomnia", "心悸": "palpitations", "心慌": "palpitations",
    "鼻塞": "nasal congestion", "流鼻涕": "runny nose", "流涕": "runny nose",
    "食欲不振": "anorexia", "体重下降": "weight loss",
    "水肿": "edema", "便血": "hematochezia",
    "耳鸣": "tinnitus", "视力模糊": "blurred vision",
    "背痛": "back pain", "腰痛": "back pain",
    "抑郁": "depression", "焦虑": "anxiety",
    "高血压": "hypertension", "糖尿病": "diabetes",
}


def _post(endpoint, payload, timeout=120):
    """调用后端接口，统一异常处理"""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"__error__": f"{endpoint} 调用失败: {str(e)}"}


def _resolve_cui(symptom_name):
    """把症状名转成 CUI。支持直接输入 CUI、中文名、英文名。"""
    name = symptom_name.strip()
    if not name:
        return None, "空输入"
    # 已经是 CUI 就直接用
    if re.fullmatch(r"C\d{7}", name):
        return name, name
    # 中文映射到英文，再交给后端做模糊匹配
    query = CHINESE_SYMPTOM_MAP.get(name, name)
    result = _post("/validateSymptom", {"name": query})
    if isinstance(result, dict) and "__error__" not in result and result:
        cui = next(iter(result))
        return cui, result[cui]
    return None, name


def _format_details(raw):
    """把 getDetails 返回的元组字符串列表解析成可读文本"""
    if not raw or (isinstance(raw, dict) and "__error__" in raw):
        return "（无详情）"
    if isinstance(raw, list):
        names = []
        for item in raw[:4]:
            try:
                t = ast.literal_eval(str(item))
                if isinstance(t, (tuple, list)) and len(t) >= 5:
                    names.append(str(t[4]))
            except Exception:
                continue
        seen = []
        for n in names:
            if n not in seen:
                seen.append(n)
        return "；".join(seen) if seen else "（无详情）"
    return str(raw)


def full_diagnosis(symptoms_text):
    """一键诊断：症状 → CUI → 疾病预测 + 相关症状建议 + 疾病详情"""
    if not symptoms_text or not symptoms_text.strip():
        return "请输入至少一个症状，例如：头痛、发烧、咳嗽"

    parts = [p.strip() for p in re.split(r"[,，、;；|]+", symptoms_text) if p.strip()]
    if not parts:
        return "请输入至少一个症状，例如：头痛、发烧、咳嗽"

    # 1. 症状 → CUI
    cuis, labels, unrecognized = [], [], []
    for p in parts:
        cui, label = _resolve_cui(p)
        if cui:
            cuis.append(cui)
            labels.append(f"{label}（{cui}）")
        else:
            unrecognized.append(label)

    if not cuis:
        return "未能识别任何症状，请检查输入。未识别：" + "、".join(unrecognized)

    # 2. 疾病预测
    pred = _post("/predict", {"symptoms": cuis, "text": ""})
    diseases = pred if isinstance(pred, list) else []

    # 3. 相关症状建议（基于每个输入症状）
    related = []
    for cui in cuis:
        sug = _post("/sySuggest", {"symptom": cui})
        if isinstance(sug, list):
            for s in sug:
                if isinstance(s, dict) and s.get("label"):
                    item = f"{s['label']}（{s['value']}）"
                    if item not in related:
                        related.append(item)
        if len(related) >= 12:
            break

    # 4. 疾病详情（取预测结果前 3 个）
    details = []
    for d in (diseases[:3] if diseases else []):
        cui = d.get("disease_cui", "")
        if cui:
            details.append((d.get("disease", cui), _format_details(_post("/getDetails", {"code": cui}))))

    # 组装报告
    lines = ["【诊断报告】", ""]
    lines.append("🔹 已识别的症状")
    lines.extend(f"  {i+1}. {lbl}" for i, lbl in enumerate(labels))
    if unrecognized:
        lines.append("")
        lines.append("⚠️ 未识别的症状：" + "、".join(unrecognized) + "（可换成英文，或到「症状验证」页查询）")

    lines.append("")
    lines.append("🔹 疾病预测（按概率排序）")
    if diseases:
        for i, d in enumerate(diseases[:5], 1):
            sy = "、".join(d.get("sy", [])[:6]) or "—"
            lines.append(f"  {i}. {d.get('disease', d.get('disease_cui', '未知'))}（{d.get('disease_cui', '')}）")
            lines.append(f"     概率：{d.get('prob', 0)}%   相关症状：{sy}")
    else:
        lines.append("  未能返回预测结果，请稍后重试")

    lines.append("")
    lines.append("🔹 相关症状建议")
    if related:
        lines.extend(f"  - {r}" for r in related)
    else:
        lines.append("  暂无相关症状建议")

    lines.append("")
    lines.append("🔹 疾病详情")
    if details:
        for name, detail in details:
            lines.append(f"  【{name}】{detail}")
    else:
        lines.append("  暂无详情")

    lines.append("")
    lines.append("⚠️ 以上结果由机器学习模型自动生成，仅供参考，不构成医疗建议。")
    return "\n".join(lines)


# ---------- 以下为手动模式（保留，供进阶使用） ----------

def validate_symptom(symptom_name):
    """验证症状并获取匹配的CUI（支持中文/英文）"""
    if not symptom_name or not symptom_name.strip():
        return "请输入症状名称"
    cui, label = _resolve_cui(symptom_name)
    if cui:
        return f"已确认症状: {label} (CUI: {cui})"
    return f"未找到相关症状，请检查输入（{label}）"


def predict_diseases(symptom_cuis):
    """根据症状CUI列表预测疾病"""
    if not symptom_cuis:
        return "请输入症状CUI（用逗号分隔）"
    try:
        cui_list = [cui.strip() for cui in symptom_cuis.split(",") if cui.strip()]
        url = f"{API_BASE_URL}/predict"
        response = requests.post(url, json={"symptoms": cui_list, "text": ""})
        results = response.json()
        if not results:
            return "未预测到相关疾病"
        output = []
        for i, disease in enumerate(results[:5], 1):
            output.append(
                f"{i}. {disease['disease']} (CUI: {disease['disease_cui']})\n"
                f"   概率: {disease['prob']}%\n"
                f"   相关症状: {', '.join(disease['sy'])}\n"
            )
        return "\n".join(output)
    except Exception as e:
        return f"预测失败: {str(e)}"


def suggest_related_symptoms(symptom_cui):
    """获取相关症状建议"""
    if not symptom_cui:
        return "请输入症状CUI"
    try:
        url = f"{API_BASE_URL}/sySuggest"
        response = requests.post(url, json={"symptom": symptom_cui})
        results = response.json()
        if not results:
            return "未找到相关症状建议"
        suggestions = "\n".join([f"- {item['label']} (CUI: {item['value']})" for item in results])
        return f"相关症状建议:\n{suggestions}"
    except Exception as e:
        return f"获取建议失败: {str(e)}"


def get_disease_details(cui):
    """获取疾病详情"""
    if not cui:
        return "请输入疾病CUI"
    cui = cui.strip()
    detail = _format_details(_post("/getDetails", {"code": cui}))
    return f"{cui} 详情：{detail}"


# 创建Gradio界面
with gr.Blocks(title="医疗诊断辅助系统", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 医疗诊断辅助系统")
    gr.Markdown("输入症状，一键完成：疾病预测、相关症状建议、疾病详情查询")

    with gr.Tabs():
        with gr.Tab("一键诊断"):
            gr.Markdown("### 输入症状（支持中文/英文，多个用逗号或顿号分隔）")
            oneclick_input = gr.Textbox(label="症状", placeholder="例如：头痛、发烧、咳嗽", lines=2)
            oneclick_btn = gr.Button("开始诊断", variant="primary")
            oneclick_output = gr.Textbox(label="诊断报告", lines=24)
            oneclick_btn.click(full_diagnosis, inputs=[oneclick_input], outputs=[oneclick_output])

        with gr.Tab("症状验证"):
            symptom_input = gr.Textbox(label="输入症状名称", placeholder="例如：头痛、发烧")
            validate_btn = gr.Button("验证症状")
            validate_output = gr.Textbox(label="验证结果")
            validate_btn.click(validate_symptom, inputs=[symptom_input], outputs=[validate_output])

        with gr.Tab("疾病预测"):
            cui_input = gr.Textbox(
                label="输入症状CUI",
                placeholder="多个CUI用逗号分隔，例如：C0018787,C0034106"
            )
            predict_btn = gr.Button("预测疾病")
            predict_output = gr.Textbox(label="预测结果", lines=10)
            predict_btn.click(predict_diseases, inputs=[cui_input], outputs=[predict_output])

        with gr.Tab("相关症状建议"):
            sy_cui_input = gr.Textbox(label="输入症状CUI", placeholder="例如：C0018787")
            suggest_btn = gr.Button("获取相关症状")
            suggest_output = gr.Textbox(label="相关症状", lines=6)
            suggest_btn.click(suggest_related_symptoms, inputs=[sy_cui_input], outputs=[suggest_output])

        with gr.Tab("疾病详情查询"):
            disease_cui_input = gr.Textbox(label="输入疾病CUI", placeholder="例如：C0011847")
            details_btn = gr.Button("查询详情")
            details_output = gr.Textbox(label="疾病详情", lines=8)
            details_btn.click(get_disease_details, inputs=[disease_cui_input], outputs=[details_output])

    gr.Markdown("""
    ### 使用说明
    1. 在「一键诊断」输入症状，即可一次性获得疾病预测、相关症状建议与疾病详情
    2. 其余标签页为手动模式，可逐步验证症状、查询CUI、预测疾病
    """)

if __name__ == "__main__":
    demo.launch(debug=True, server_name='0.0.0.0', server_port=5001)
