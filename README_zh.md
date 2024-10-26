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

* 设置 MiniGPT-3D 环境

```bash
cd MiniGPT-3D

# 优先使用mamba，如果未安装，则使用conda
mamba env create -f environment.yml
# conda env create -f environment.yml

conda activate minigpt_3d
bash env_install.sh

# 下载预训练模型权重，到MiniGPT-3D目录下
# 需要git-lfs与aria2c，如果未安装，请通过conda/mamba安装
# mamba install -c conda-forge git-lfs aria2c
../tools/hfd.sh YuanTang96/MiniGPT-3D --tool aria2c -x 16 --exclude config.json --exclude README.md --exclude .gitattributes
```

## 具体组件

### to_pointcloud/convert.py

`convert.py` 脚本用于将3D模型转换为点云数据。提供了step -> obj (mesh) -> ply (point cloud) 的转换功能。该组件包含其他支持函数等。该脚本可作为独立脚本使用，也可以作为其他脚本的一部分。

```bash
usage: convert.py [-h] (--step_file STEP_FILE | --obj_file OBJ_FILE)

options:
  -h, --help            show this help message and exit
  --step_file STEP_FILE
  --obj_file OBJ_FILE
```

### to_pointcloud/snapshots.py

`snapshots.py` 脚本用于生成3D模型的预览快照。支持交互式预览和保存快照。该脚本可作为独立脚本使用，也可以作为其他脚本的一部分。在交互模式下，用户可通过拖动鼠标来旋转模型；在保存模式下，用户可指定快照的名称和保存路径，每一份mesh会保存14个视角的快照。

```bash
usage: snapshots.py [-h] (--obj_file OBJ_FILE | --step_file STEP_FILE) [-o OUT_PATH] [-r RESOLUTION RESOLUTION]
                    [-d DIRECTION] (-p | -s)

options:
  -h, --help            show this help message and exit
  --obj_file OBJ_FILE
  --step_file STEP_FILE
  -o OUT_PATH, --out_path OUT_PATH
  -r RESOLUTION RESOLUTION, --resolution RESOLUTION RESOLUTION
  -d DIRECTION, --direction DIRECTION
  -p, --preview
  -s, --snapshots
```
