# LLM Graph

基于语言模型的知识图谱构建与问答系统。

## Quick Start

在根目录下创建`.env`文件，内容如下：

```env
OPENAI_API_KEY=sk-your-OPENAI_API_KEY
OPENAI_BASE_URL=<https://api.openai.com/v1>
```

执行如下命令：

```bash
pip install -r requirements.txt

cd src
python main.py
```



## 技术方案

1. 基于[Marker](https://github.com/VikParuchuri/marker)的PDF图文抽取

    ```bash
    marker_single ../papers/2312.11970v1.pdf examples/paper --batch_multiplier 2 --max_pages 10 --langs English
    ```

2. 使用开源多模态大模型的图文实体抽取和对齐

    含文字的图片，全文检索文字片段连同图片一同发给LLM，提取实体，然后对齐
    实体/关系，辅助溯源的属性，比如images, chunkid

3. 结构溯源

    实体/关系，辅助溯源的属性，比如images, chunkid，

## Coming Soon

1. Benchmark
   1. 数据集： 科技论文，CS论文，NLP论文，CV论文，医学论文， 维基百科，en/zh
   2. 评测标准：实体抽取，关系抽取，实体对齐，关系对齐，准确性
2. 多轮迭代抽取
3. 实体聚类合并,附加原文