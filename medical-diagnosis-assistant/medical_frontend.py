import streamlit as st
import requests
import json

# 页面配置
st.set_page_config(
    page_title="医学症状分析系统",
    page_icon="🏥",
    layout="wide"
)

# API基础URL
API_BASE_URL = "http://127.0.0.1:5000"

# 初始化会话状态
if 'selected_symptoms' not in st.session_state:
    st.session_state.selected_symptoms = []  # 存储选中的症状 (CUI, 名称)
if 'validation_results' not in st.session_state:
    st.session_state.validation_results = {}  # 存储症状验证结果
if 'prediction_results' not in st.session_state:
    st.session_state.prediction_results = None  # 存储预测结果

# 页面标题和说明
st.title("医学症状分析系统")
st.markdown("通过UMLS数据库分析症状并预测可能的疾病")

# API调用函数
def call_api(endpoint, data):
    """通用API调用函数"""
    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data)
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API请求失败 (状态码: {response.status_code})")
            st.error(f"响应内容: {response.text}")
            return None
    except Exception as e:
        st.error(f"请求发生错误: {str(e)}")
        return None

# 1. 症状验证部分
st.subheader("1. 症状验证")
st.markdown("输入症状名称，系统会验证并返回匹配的标准症状及其CUI")

col1, col2 = st.columns(2)

with col1:
    symptom_input = st.text_input("输入症状名称", placeholder="例如：头痛、发烧、咳嗽")
    if st.button("验证症状"):
        if symptom_input.strip():
            with st.spinner("正在验证症状..."):
                result = call_api("/api/validateSymptom", {"name": symptom_input})
                if result:
                    st.session_state.validation_results = result
                    st.success(f"找到 {len(result)} 个匹配结果")
        else:
            st.warning("请输入症状名称")

with col2:
    if st.session_state.validation_results:
        st.write("匹配的症状结果：")
        for cui, name in st.session_state.validation_results.items():
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(f"• {name} (CUI: {cui})")
            with col_b:
                if st.button("添加", key=f"add_{cui}"):
                    if (cui, name) not in st.session_state.selected_symptoms:
                        st.session_state.selected_symptoms.append((cui, name))
                        st.success(f"已添加：{name}")

# 2. 已选症状展示
st.subheader("2. 已选症状")
if st.session_state.selected_symptoms:
    for i, (cui, name) in enumerate(st.session_state.selected_symptoms):
        cols = st.columns([3, 2, 1])
        
        with cols[0]:
            st.write(f"• {name} (CUI: {cui})")
        
        with cols[1]:
            if st.button("查看详情", key=f"detail_{i}"):
                with st.spinner("获取症状详情..."):
                    details = call_api("/api/getDetails", {"code": cui})
                    if details:
                        st.info(f"症状详情: {details}")
        
        with cols[2]:
            if st.button("移除", key=f"remove_{i}"):
                st.session_state.selected_symptoms.pop(i)
                st.experimental_rerun()
        
        # 相关症状建议
        with st.expander(f"查看与 {name} 相关的症状"):
            with st.spinner("获取相关症状..."):
                suggestions = call_api("/api/sySuggest", {"symptom": cui})
                if suggestions:
                    for s in suggestions:
                        if st.button(f"添加: {s['label']}", key=f"add_sug_{s['value']}_{i}"):
                            if (s['value'], s['label']) not in st.session_state.selected_symptoms:
                                st.session_state.selected_symptoms.append((s['value'], s['label']))
                                st.success(f"已添加相关症状：{s['label']}")
                else:
                    st.info("未找到相关症状")
else:
    st.info("尚未选择任何症状，请从上方验证结果中添加")

# 3. 疾病预测部分
st.subheader("3. 疾病预测")
st.markdown("基于所选症状预测可能的疾病")

predict_col1, predict_col2 = st.columns(2)

with predict_col1:
    st.markdown("**基于已选症状预测**")
    if st.button("开始预测", disabled=not st.session_state.selected_symptoms):
        with st.spinner("正在进行疾病预测..."):
            # 提取已选症状的CUI列表
            symptom_cuis = [cui for cui, name in st.session_state.selected_symptoms]
            results = call_api("/api/predict", {"symptoms": symptom_cuis})
            if results:
                st.session_state.prediction_results = results
                st.success("预测完成！结果显示在下方")

with predict_col2:
    st.markdown("**基于症状名称字符串预测**")
    symptoms_str = st.text_input("输入症状名称，用|分隔", placeholder="例如：头痛|发烧|咳嗽")
    if st.button("从字符串预测") and symptoms_str.strip():
        with st.spinner("正在进行疾病预测..."):
            results = call_api("/api/predictFromString", {"symptoms": symptoms_str})
            if results:
                st.session_state.prediction_results = results
                st.success("预测完成！结果显示在下方")

# 显示预测结果
if st.session_state.prediction_results:
    st.subheader("预测结果")
    for idx, disease in enumerate(st.session_state.prediction_results):
        with st.expander(f"{idx+1}. {disease['disease']} (概率: {disease['prob']}%)"):
            st.write(f"疾病CUI: {disease['disease_cui']}")
            if disease['sy']:
                st.write("相关症状:")
                for sy in disease['sy']:
                    st.write(f"- {sy}")

# 页脚信息
st.markdown("---")
st.info("""
注意：本系统仅用于医学研究和教育目的，不能替代专业医疗人员的诊断。
如有健康问题，请咨询合格的医疗专业人士。
""")

