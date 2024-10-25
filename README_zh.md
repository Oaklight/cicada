# CodeCad-RAG

[中文](./README_zh.md) | [English](./README.md)

## 仓库结构

仓库包含以下主要目录和文件：

* `data`：数据目录，包含点云数据和模型数据。
* `env_install.sh`：环境安装脚本。
* `requirements.txt`：项目依赖库列表。
* `to_pointcloud`：包含将3D模型转换为点云的脚本。
* `MiniGPT-3D`：点云描述组件
* `tools`：包含辅助脚本。

## 如何设置环境

### 下载代码库以及子组件

```bash
git clone https://github.com/Oaklight/codecad-rag.git
cd codecad-rag
git submodule update --init --recursive
```

### 安装依赖库

* 选项1：安装conda虚拟环境：

```bash
conda env create -f environment.yml
conda activate codecad
```

* 选项2：使用pip，安装requirements.txt中的依赖库：

```bash
# 创建虚拟环境codecad
python -m venv codecad
# 激活虚拟环境
source codecad/bin/activate
# 安装依赖库
pip install -r requirements.txt
```

### 设置其他相关环境

```bash
bash env_install.sh
```

## convert.py脚本

`convert.py` 脚本用于将3D模型转换为点云数据。以下是该脚本的详细说明和用法

### 功能

`convert.py` 提供了step -> obj (mesh) -> ply (point cloud) 的转换功能。该组件包含其他支持函数，如计算质心、惯性张量、主轴等。
