# CodeCad-RAG

[中文](./README_zh.md) | [English](./README.md)

## Repository structure

Repositories contain the following main directories and files:

* 'data': A data directory containing point cloud data and model data.
* 'env_install.sh': Environment installation script.
* 'requirements.txt': A list of dependent libraries for the project.
* 'to_pointcloud': Contains a script to convert the 3D model into a point cloud.
* 'MiniGPT-3D': Point cloud description component
* 'tools': Contains helper scripts.

## How to set up the environment

### Download the codebase and subcomponents

```bash
git clone https://github.com/Oaklight/codecad-rag.git
cd codecad-rag
git submodule update --init --recursive
```

### Install dependencies

* Option 1: Install Conda Virtual Environment:

```bash
conda env create -f environment.yml
conda activate codecad
```

* Option 2: Use pip and install the dependencies in the requirements.txt:

```bash
# Create a virtual environment codecad
python -m venv codecad
# Activate the virtual environment
source codecad/bin/activate
# Install dependencies
pip install -r requirements.txt
```

### Set up other related environments

```bash
bash env_install.sh
```

## convert.py script

The 'convert.py' script is used to convert the 3D model into point cloud data. Here is a detailed description and usage of the script

### features

'convert.py' provides step-> obj (mesh) -> ply (point cloud) conversion. This component contains other supporting functions such as computation of centroids, inertial tensors, spindles, and so on.
