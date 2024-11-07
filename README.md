# CodeCad-RAG

[中文](./README_zh.md) | [English](./README.md)

## Repository Structure

The repository contains the following main directories and files:

* `data`: Data directory, containing point cloud data and model data.
* `env_install.sh`: Environment installation script.
* `requirements.txt`: List of project dependencies.
* `geometry_pipeline`: Contains scripts to convert 3D models to point clouds.
* `MiniGPT-3D`: Point cloud description component.
* `tools`: Contains auxiliary scripts.

## How to Set Up the Environment

### Download the Code Repository and Subcomponents

```bash
git clone https://github.com/Oaklight/codecad-rag.git
cd codecad-rag
git submodule update --init --recursive
```

### Install Dependencies

* Option 1: Install conda virtual environment:

```bash
conda env create -f environment.yml
conda activate codecad
```

* Option 2: Use pip to install dependencies from requirements.txt:

```bash
# Create virtual environment codecad
python -m venv codecad
# Activate virtual environment
source codecad/bin/activate
# Install dependencies
pip install -r requirements.txt
```

### Set Up Other Related Environments

* Set up MiniGPT-3D environment

```bash
cd MiniGPT-3D

# Prefer using mamba, if not installed, use conda
mamba env create -f environment.yml
# conda env create -f environment.yml

conda activate minigpt_3d
bash env_install.sh

# Download pre-trained model weights to the MiniGPT-3D directory
# Requires git-lfs and aria2c, if not installed, install via conda/mamba
# mamba install -c conda-forge git-lfs aria2c
../tools/hfd.sh YuanTang96/MiniGPT-3D --tool aria2c -x 16 --exclude config.json --exclude README.md --exclude .gitattributes
```

## Specific Components

### geometry_pipeline/convert.py

`convert.py` script is used to convert 3D models to point cloud data. It provides the conversion functions from step -> obj (mesh) -> ply (point cloud). The component includes other supporting functions. The script can be used as a standalone script or as part of another script.

```bash
usage: convert.py [-h] (--step_file STEP_FILE | --obj_file OBJ_FILE)

options:
  -h, --help            show this help message and exit
  --step_file STEP_FILE
  --obj_file OBJ_FILE
```

### geometry_pipeline/snapshots.py

`snapshots.py` script is used to generate preview snapshots of 3D models. It supports interactive preview and snapshot saving. The script can be used as a standalone script or as part of another script. In interactive mode, users can rotate the model by dragging the mouse; in save mode, users can specify the snapshot name and save path, with each mesh saving snapshots from 14 different angles.

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
