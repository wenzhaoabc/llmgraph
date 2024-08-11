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



## 多轮迭代抽取(ccr)

目前添加了对文本中实体和关系的多轮迭代抽取

src.prompts引入CONTINUE_PROMPT, LOOP_PROMPT两个提示词，分别用于继续提取和判断是否提取结束

src.main中添加新类LLMForEntityExctract，用于循环多轮迭代抽取，并保存对话历史

src.main extract_entities_relations函数中添加局部变量max_gleanings（默认为2），即最大迭代次数，可以根据需要改成函数形参

针对文本的多轮提取实体和关系的结果在log中记录init iteration res，  0 iteration res， 1 iteration res

## 合并去重(wwj)

* 实现步骤

  1. 从 entity graph 开始
  2. 构建K-邻近图，根据text embedding连接相似的实体
  3. 在K-邻近图中过滤弱联通分量
  4. 用LLM来评估是否要合并找出的相似实体
  5. 合并Entities，更新Relationships

* 具体实现

  1. Text Embedding

     使用BERT模型生成嵌入向量，目前使用Entity的name属性生成embedding。

  2. Build KNN Graph

     构建K邻近图，根据向量相似连接近似的节点，k的默认大小为5。

  3. Filter Weakly Connected Components

     根据K邻近图中的distance是否小于设定的阈值distance_threshold来判断是否为弱联通分量，阈值默认值为0.2。

  4. Merge Entities

     首先构建 MERGE_PROMPT 作为 system prompt 帮助模型更好理解合并任务，根据找到的若联通分量 components 构建user prompt让 llm 判断是否要合并components。

  5. Update Relationships

     根据合并的Entities来更新Relationships。

## Coming Soon

1. Benchmark
   1. 数据集： 科技论文，CS论文，NLP论文，CV论文，医学论文， 维基百科，en/zh
   2. 评测标准：实体抽取，关系抽取，实体对齐，关系对齐，准确性
2. 多轮迭代抽取
3. 实体聚类合并,附加原文