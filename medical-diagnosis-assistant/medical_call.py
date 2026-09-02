import requests
import json
import sys

# 接口基础URL（根据实际部署地址修改，默认本地Flask服务）
BASE_URL = "http://localhost:5000/api"

def print_separator():
    """打印分隔线，优化输出可读性"""
    print("\n" + "="*60 + "\n")

def call_validate_symptom():
    """调用 /api/validateSymptom 接口"""
    print("\n--- 调用 validateSymptom 接口（验证症状名称并返回CUI）---")
    symptom_name = input("请输入症状名称（例如：fever）：").strip()
    url = f"{BASE_URL}/validateSymptom"
    payload = {"name": symptom_name}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # 检查请求是否成功
        print("\n接口响应：")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except requests.exceptions.RequestException as e:
        print(f"请求失败：{str(e)}")

def call_get_details():
    """调用 /api/getDetails 接口"""
    print("\n--- 调用 getDetailsfromCode 接口（根据CUI获取详情）---")
    cui_code = input("请输入症状/疾病的CUI编码（例如：C0015967）：").strip()
    url = f"{BASE_URL}/getDetails"
    payload = {"code": cui_code}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("\n接口响应：")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except requests.exceptions.RequestException as e:
        print(f"请求失败：{str(e)}")

def call_sy_suggest():
    """调用 /api/sySuggest 接口"""
    print("\n--- 调用 sySuggest 接口（根据症状推荐相关症状）---")
    symptom = input("请输入症状（用于推荐相关症状）：").strip()
    url = f"{BASE_URL}/sySuggest"
    payload = {"symptom": symptom}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("\n接口响应：")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except requests.exceptions.RequestException as e:
        print(f"请求失败：{str(e)}")

def call_predict_from_string():
    """调用 /api/predictFromString 接口"""
    print("\n--- 调用 predictFromString 接口（通过|分隔的症状字符串预测疾病）---")
    symptoms_str = input("请输入症状（用|分隔，例如：fever|headache）：").strip()
    url = f"{BASE_URL}/predictFromString"
    payload = {"symptoms": symptoms_str}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("\n接口响应：")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except requests.exceptions.RequestException as e:
        print(f"请求失败：{str(e)}")

def call_predict():
    """调用 /api/predict 接口"""
    print("\n--- 调用 predict 接口（通过症状列表预测疾病）---")
    symptoms_input = input("请输入症状CUI列表（用逗号分隔，例如：C0015967,C0018681）：").strip()
    symptoms_list = [s.strip() for s in symptoms_input.split(",") if s.strip()]
    lang = input("请输入语言（默认en，可选de）：").strip() or "en"
    
    url = f"{BASE_URL}/predict?lang={lang}"
    payload = {
        "symptoms": symptoms_list,
        "text": ""  # 接口定义的text字段，此处可不填
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("\n接口响应：")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except requests.exceptions.RequestException as e:
        print(f"请求失败：{str(e)}")

def main():
    """主函数：显示菜单并处理用户选择"""
    print("===== Flask接口调用工具 =====")
    print("说明：请先确保Flask服务已启动（运行原代码：python  medical_call.py），基础URL为：", BASE_URL)
    print("支持的接口如下，可循环调用：\n")
    
    # 接口映射表：序号 -> (接口名称, 调用函数)
    interfaces = {
        "1": ("validateSymptom", call_validate_symptom),
        "2": ("getDetailsfromCode", call_get_details),
        "3": ("sySuggest", call_sy_suggest),
        "4": ("predictFromString", call_predict_from_string),
        "5": ("predict", call_predict),
        "0": ("退出程序", None)
    }
    
    while True:
        # 打印菜单
        for idx, (name, _) in interfaces.items():
            print(f"  {idx}. {name}")
        print()
        
        choice = input("请选择接口序号（0-5）：").strip()
        if choice not in interfaces:
            print("无效选择，请重新输入！")
            print_separator()
            continue
        
        if choice == "0":
            print("程序退出，再见！")
            sys.exit(0)
        
        # 调用选中的接口
        _, func = interfaces[choice]
        func()  # 执行接口调用函数
        print_separator()

if __name__ == "__main__":
    main()
