# 基于医疗大模型的辅助诊疗系统（Medical Diagnosis Assistant）

一个基于**症状输入 → 疾病预测**的智能辅助诊疗原型系统。系统以 UMLS（统一医学语言系统）的 CUI 标准编码为知识基础，结合 CUI2Vec 语义向量与朴素贝叶斯分类器，实现"症状验证 → 疾病预测 → 相关症状推荐 → 疾病详情查询"的完整交互流程。

> ⚠️ 本项目为课程/科研原型系统，仅供学习研究，**不构成任何医疗建议**。

## 功能一览

| 功能 | 说明 | 对应接口 |
| --- | --- | --- |
| 症状验证 | 输入症状名称（中英文均可尝试），返回标准化症状及 CUI 编码 | `/api/validateSymptom` |
| 疾病预测 | 输入一个或多个症状 CUI，返回可能疾病及其概率、相关症状 | `/api/predict` |
| 相关症状推荐 | 输入症状 CUI，返回语义相似的相关症状 | `/api/sySuggest` |
| 疾病详情查询 | 输入疾病/症状 CUI，返回 UMLS 数据库中的术语详情 | `/api/getDetails` |
| 字符串预测 | 用 `\|` 分隔的症状名直接预测疾病（快捷方式） | `/api/predictFromString` |

## 一键诊断（改进版）

前端新增「一键诊断」标签页：直接在输入框填写症状（支持中文/英文，多个用逗号或顿号分隔），系统会自动完成 **症状 → CUI → 疾病预测 → 相关症状建议 → 疾病详情** 的全流程，一次性输出完整诊断报告，无需再手动复制 CUI 到各个标签页。内置常见中文症状名（头痛、发烧、咳嗽等）到英文 UMLS 术语的映射。

其余标签页保留为手动模式，供逐步验证症状、查询 CUI 使用。
## 系统架构

```
[浏览器]
   │  http://localhost:5001
   ▼
[Gradio 前端  app_gradio.py]           ←—— 主界面（4 个标签页）
   │  http://localhost:7680/api
   ▼
[Flask 后端  app_1119.py]              ←—— 核心服务（Python 3.6）
   │
   ├─ validateSymptom ──► en_Labels.js（症状名 ↔ CUI 映射表）
   ├─ predict ─────────► all_mnb.pkl（朴素贝叶斯模型，MultinomialNB）
   │                     all_x.csv（症状 one-hot 特征）
   │                     disease-symptom-merged.csv（疾病-症状数据）
   ├─ sySuggest ───────► 10_epochs_0.6_similarity.npy（CUI2Vec 症状向量）
   │                     Dictionary.csv + symptom.npy
   └─ getDetails ──────► umls.db（UMLS SQLite 数据库）
```

**数据与模型的产生流程**（对应仓库里的训练脚本）：

```
disease-symptom-db.csv ─┐
                        ├─► disease-symptom-merged.csv ─► one-hot ─► all_x.csv
DiseaseSymptomKB.csv  ──┘                                          │
                                                          MultinomialNB 训练
                                                                   ▼
                                                          all_mnb.pkl（疾病预测模型）

CUI 共现关系 ─► relatedSymptoms.py（Keras skip-gram / CUI2Vec）
                                                       ▼
                                    10_epochs_0.6_similarity.npy（症状语义向量）
```

## 目录结构

```
├── app.py                # Flask 后端（上游原版，端口 5000）
├── app_1119.py           # Flask 后端（本项目实际使用版本，端口 7680）
├── app_gradio.py         # Gradio 前端（主界面，端口 5001）
├── medical_frontend.py   # Streamlit 前端（备选界面，端口 8501，调用 5000 后端）
├── medical_call.py       # 后端接口命令行测试工具
├── helper.py             # 后端工具函数（CUI 校验、模型加载、UMLS 查询封装）
├── relatedSymptoms.py    # CUI2Vec 症状向量训练脚本
├── generateLabels.py     # 从 umls.db 生成 en_Labels.js 症状映射表
├── cui2vec-converter.py  # CUI 词向量格式转换脚本
├── train.py              # 朴素贝叶斯疾病预测模型训练脚本
├── en_Labels.js          # 症状英文名 ↔ CUI 映射表
├── disease-symptom-*.csv # 疾病-症状训练数据
├── umls/                 # UMLS 工具模块（Apache 2.0，来自开源项目）
├── data/all-files-for-ml/# 运行所需的模型文件（见 data/README.md）
├── server_start.sh       # 一键启动脚本（后端 + 前端）
├── Dockerfile            # 后端镜像构建（python:3.6）
├── docker-compose.yml    # 上游项目的 compose 配置（端口 5000）
└── requirements.txt      # 后端 Python 依赖
```

## 快速开始

### 方式一：直接从现有容器运行（最省事）

如果你手头有当年导出的容器镜像/容器（如 `media-1119`）：

```bash
docker start media-1119
docker exec -it media-1119 bash
sh server_start.sh
# 浏览器打开 http://localhost:5001
```

### 方式二：从源码构建

**后端（Python 3.6，端口 7680）**

```bash
pip install -r requirements.txt
python app_1119.py
```

**前端（Gradio，端口 5001）**

```bash
pip install -r frontend-requirements.txt
python app_gradio.py
# 浏览器打开 http://localhost:5001
```

**前置条件**：需要先准备好 `umls/databases/umls.db`（UMLS 数据库，约 2.25GB，见下方"数据与许可证"）。

## 接口文档

所有接口均为 `POST` + JSON，基础地址 `http://localhost:7680/api`。

### 1. 验证症状 `POST /api/validateSymptom`

```json
// 请求
{"name": "fever"}
// 响应：完全匹配返回单个 CUI；否则返回最近似匹配列表
{"C0015967": "fever"}
```

### 2. 预测疾病 `POST /api/predict`

```json
// 请求：symptoms 为 CUI 数组
{"symptoms": ["C0015967", "C0018681"]}
// 响应：按概率降序的疾病列表（最多 15 条）
[
  {"disease": "Bronchopneumonia", "disease_cui": "C0006285",
   "prob": 60.4, "sy": ["Coughing", "Fever"]}
]
```

### 3. 相关症状推荐 `POST /api/sySuggest`

```json
{"symptom": "C0015967"}
// 响应
[{"label": "Coughing", "value": "C0006425"}]
```

### 4. 疾病详情 `POST /api/getDetails`

```json
{"code": "C0015967"}
// 响应：UMLS 中的术语描述
```

### 5. 字符串预测 `POST /api/predictFromString`

```json
{"symptoms": "fever|headache"}
```

> 也可以运行 `python medical_call.py` 用交互式菜单测试以上接口。

## 数据与许可证

- **`umls/` 模块**：来自开源项目，版权归 Boston Children's Hospital（2015），使用 **Apache License 2.0**（完整文本见 `umls/LICENSE.txt`）。
- **上游项目**：本系统是在开源项目 [sparrow-platform/disease-diagnostics-engine](https://github.com/sparrow-platform/disease-diagnostics-engine)（Docker 镜像 `jaylohokare/diseases-predictor`）基础上二次开发，前端界面与测试工具为本项目团队编写。
- **UMLS 数据库（`umls.db`）**：来自美国国立医学图书馆（NLM）的 UMLS 数据，需**单独申请授权**，不随本仓库分发。获取方式见 `data/README.md`。
- **模型文件**：训练产生的模型/特征文件位于 `data/all-files-for-ml/`，其中 1GB 的 `cui2vec_pretrained.csv` 未包含在仓库中（仅重训词向量时需要），获取方式见 `data/README.md`。

## 端口速查

| 端口 | 服务 |
| --- | --- |
| 5000 | 上游原版 Flask 后端（`app.py`，配合 docker-compose） |
| 7680 | 本项目 Flask 后端（`app_1119.py`） |
| 5001 | Gradio 前端（`app_gradio.py`） |
| 8501 | Streamlit 前端（`medical_frontend.py`，备选） |

