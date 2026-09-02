# data/ 数据说明

`data/all-files-for-ml/` 存放模型运行所需文件（已随仓库提供）：

| 文件 | 大小 | 用途 |
| --- | --- | --- |
| `all_mnb.pkl` | ~4.3 MB | 朴素贝叶斯疾病预测模型（MultinomialNB） |
| `all_x.csv` | ~0.8 MB | 症状 one-hot 特征矩阵（模型输入维度） |
| `all_pivoted.csv` | ~0.8 MB | 疾病-症状 透视表 |
| `Dictionary.csv` | ~14 KB | CUI 与向量索引映射 |
| `symptom.npy` | ~224 KB | 症状集合 |
| `10_epochs_0.6_similarity.npy` | ~1.6 MB | CUI2Vec 症状语义向量（相似度推荐用） |

## 未随仓库提供的大文件

### 1. `cui2vec_pretrained.csv`（约 1 GB）

CUI2Vec 预训练词向量，仅在重训症状向量（`relatedSymptoms.py`）时需要，
运行时不需要。可从上游项目的公开数据获取：

- 上游 README 中的 Google Drive 链接（`data` 文件夹）：
  https://drive.google.com/file/d/1nwD3aEMwW5CF8CWOscOT3IMztuNBpaYq/view?usp=sharing

### 2. `umls/databases/umls.db`（约 2.25 GB）

UMLS 数据库，`getDetails` / 疾病名称翻译等功能依赖它。获取方式：

1. 向美国国立医学图书馆（NLM）申请 UMLS 授权（免费，学术用途）：
   https://uts.nlm.nih.gov/uts/
2. 或用上游 README 提供的数据库下载链接：
   https://drive.google.com/file/d/1BmnzCv2hjU49vXxBv_kI4FUae-lIAdz0/view?usp=sharing
3. 若你保留了当年的容器导出（如 `media-1119-export.tar`），
   直接解压其中的 `umls/databases/umls.db` 即可。

放置位置：`umls/databases/umls.db`
