# CICADA: 协作智能 CAD 自动化设计代理

[中文](./README_zh.md) | [English](./README_en.md)

欢迎使用**CICADA**，协作智能 CAD 自动化设计代理。CICADA 是一个前沿框架，旨在通过智能自动化和协作来简化和增强 CAD 设计流程。本仓库包含 CICADA 的核心模块和工具，支持与 CAD 工作流的无缝集成。

📖 **文档**: 访问我们的官方文档站点，探索全面的指南、教程和 API 参考：[CICADA 文档](https://cicada.lab.oaklight.cn)

有关快速设置和使用说明，请继续阅读以下内容。

---

## 仓库结构

仓库按以下主要模块组织：

- **core**: 核心工具和框架共享功能。
- **geometry_pipeline**: 处理和转换 3D 模型的工具，包括点云生成和快照。
- **describe**: 生成和管理 3D 模型描述性元数据的组件。
- **coding**: CAD 自动化的代码生成、执行和调试工具。
- **feedbacks**: 分析并提供设计迭代反馈的模块。
- **retrieval**: 检索和管理文档、模型数据和设计资源的工具。
- **workflow**: CICADA 自动化工作流的编排和代理管理。

---

## 环境设置

### 先决条件

在设置 CICADA 之前，请确保已安装以下内容：

- **Python 3.10+**
- **Conda** 或 **pip**（用于依赖管理）

### 安装步骤（快速开始）

```bash
# 首先激活你的venv或conda环境
pip install cicada-agent
```

#### CodeCAD 模块

```bash
pip install cicada-agent[codecad]
```

### 安装步骤（开发者）

#### 1. 克隆仓库

```bash
git clone https://github.com/Oaklight/cicada.git
cd cicada
```

#### 2. 安装依赖

建议使用 conda 或其他工具为 CICADA 创建一个独立的开发环境

```bash
conda env create -f environment.yml
conda activate cicada
```

然后将本地仓库安装为 pip 包，记得需要[all]来构建文档

```bash
pip install -e . # 仅安装`core`功能
pip install -e .[codecad] # 安装codecad相关功能
pip install -e .[all] # 安装所有功能
```

#### 3. 更新 API 密钥

配置文件中的 API 密钥已弃用。更新`config.yaml`或每个模块中的`config/*.yaml`中的`api_key`和`api_base_url`：

---

## 关键模块及使用

### `geometry_pipeline`

- **`convert.py`**: 将 3D 模型（STEP, OBJ, STL）转换为点云数据（PLY）或其他格式。

  ```bash
  python geometry_pipeline/convert.py --step_file <path_to_step_file> --convert_step2obj
  ```

  **选项**:  
  `--convert_step2obj`, `--convert_obj2pc`, `--convert_step2stl`, `--convert_obj2stl`, `--convert_stl2obj`, `--convert_stl2pc`, `--reaxis_gravity`

- **`snapshots.py`**: 从多个角度生成 3D 模型的预览快照。
  ```bash
  python geometry_pipeline/snapshots.py --step_file <path_to_step_file> --snapshots
  ```
  **选项**:  
  `--obj_file`, `--step_file`, `--stl_file`, `-o OUTPUT_DIR`, `-r RESOLUTION`, `-d DIRECTION`, `-p`, `--reaxis_gravity`

### `describe`

- **`describer_v2.py`**: 使用高级语言模型生成 3D 模型的描述性元数据。
  ```bash
  python describe/describer_v2.py "描述3D模型" --config <path_to_config> --prompts <path_to_prompts>
  ```
  **选项**:  
  `--config CONFIG`, `--prompts PROMPTS`, `-img REF_IMAGES`, `-o OUTPUT`

### `coding`

- **`coder.py`**: 根据设计目标生成 CAD 脚本。
  ```bash
  python coding/coder.py "设计一个机械零件" --config <path_to_config> --prompts <path_to_prompts>
  ```
  **选项**:  
  `--config CONFIG`, `--master_config_path MASTER_CONFIG_PATH`, `--prompts PROMPTS`, `-o OUTPUT_DIR`

### `feedbacks`

- **`visual_feedback.py`**: 分析设计渲染图像与设计目标的对比。
  ```bash
  python feedbacks/visual_feedback.py --design_goal "设计一个机械零件" --rendered_images <path_to_images>
  ```
  **选项**:  
  `--config CONFIG`, `--prompts PROMPTS`, `--reference_images REFERENCE_IMAGES`, `--rendered_images RENDERED_IMAGES`

### `retrieval`

- **`tools/build123d_retriever.py`**: 检索和管理 CAD 工具和库的文档。

  ```bash
  python retrieval/tools/build123d_retriever.py [--force-rebuild] [--interactive] [--metric {l2,cosine}] [--query QUERY] [--debug]
  ```

  **选项**:  
  `--force-rebuild`: 强制重建数据库。  
  `--interactive`: 以交互模式运行，询问多个问题。  
  `--metric {l2,cosine}`: 用于相似性搜索的距离度量。  
  `--query QUERY`: 在数据库中搜索的查询文本。  
  `--debug`: 启用调试模式以获取详细日志。

  **示例**:  
  交互模式:

  ```bash
  python retrieval/tools/build123d_retriever.py --interactive
  ```

  单次查询:

  ```bash
  python retrieval/tools/build123d_retriever.py --query "如何拉伸一个形状？"
  ```

### `workflow`

- **`codecad_agent.py`**: 编排 CAD 设计的自动化工作流。

  ```bash
  python workflow/codecad_agent.py "设计一个机械零件" --config <path_to_config> --prompts <path_to_prompts>
  ```

  **选项**:  
  `--config CONFIG`: 配置文件路径。  
  `--prompts PROMPTS`: 提示文件路径。  
  `-img REF_IMAGES`: 参考图像路径（可选）。  
  `-o OUTPUT_DIR`: 保存输出文件的目录（可选）。

  **示例**:

  ```bash
  python workflow/codecad_agent.py "设计一个机械零件" --config workflow/config/code-llm.yaml --prompts workflow/prompts/code-llm.yaml -o output/
  ```

---

## 贡献

我们欢迎社区的贡献！如果您想为 CICADA 做出贡献，请按照以下步骤操作：

1. Fork 仓库。
2. 为您的功能或修复创建一个新分支。
3. 提交一个包含更改详细描述的拉取请求。

---

## 许可证

CICADA 根据**MIT 许可证**授权。更多详情，请参阅[LICENSE](./LICENSE)文件。

---

## 联系

如有问题、反馈或支持，请通过[GitHub Issues](https://github.com/Oaklight/cicada/issues)发布或联系**[dingpeng]@@uchicago[dot]edu**。

---

## 引用

如果您在研究中使用了 Cicada，请考虑引用：

```bibtex
@software{Cicada,
  author = {Peng Ding},
  title = {Cicada: Collaborative Intelligent CAD Automation Design Agent},
  month = {January},
  year = {2025},
  url = {https://github.com/Oaklight/cicada}
}
```

---

**CICADA** — 通过智能自动化革新 CAD 设计。 🚀
