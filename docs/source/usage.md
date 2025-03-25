# Usage

This page explains how to set up and use the **CICADA** framework.

---

## Setting Up the Environment

### Prerequisites

Before setting up CICADA, ensure you have the following installed:

- **Python 3.10+**
- **pip** (for dependency management)
- **conda/mamba** (for environment isolation)

### Installation Steps (Quick Start)

The following installs you the core modules of cicada:

- `cicada.core`
- `cicada.retrieval`
- `cicada.tools`

```bash
# activate your venv or conda env first
pip install cicada-agent # this installs the "core" modules
```

For CodeCAD related modules

- `cicada.coding`
- `cicada.describe`
- `cicada.feedback`
- `cicada.geometry_pipeline`
- `cicada.workflows`

```bash
pip install cicada-agent[codecad]
```

### Installation Steps (For Developers)

#### Core Installation

Core module provides the fundamental functionalities of CICADA framework.

```bash
git clone https://github.com/Oaklight/cicada.git
cd cicada

# Using Conda (Recommended)
conda env create -f environment.yml
conda activate cicada

# Or using pip
python -m venv cicada
source cicada/bin/activate
pip install -r requirements.txt
```

#### CodeCAD Installation

CodeCAD module focuses on CAD code generation and execution. It requires additional dependencies:

```bash
# Install core dependencies first (see Core Installation)
# Then install CodeCAD specific dependencies
pip install -r src/cicada/coding/requirements.txt
```

#### Update API Keys

The provided API keys in the config files are deprecated. Update the `api_key` and `api_base_url` in `config.yaml` or `config/*.yaml` in each module.

---

## Key Modules and Usage

### `geometry_pipeline`

- **`convert.py`**: Converts 3D models (STEP, OBJ, STL) to point cloud data (PLY) or other formats.

  ```bash
  python geometry_pipeline/convert.py --step_file <path_to_step_file> --convert_step2obj
  ```

  **Options**:  
  `--convert_step2obj`, `--convert_obj2pc`, `--convert_step2stl`, `--convert_obj2stl`, `--convert_stl2obj`, `--convert_stl2pc`, `--reaxis_gravity`

- **`snapshots.py`**: Generates preview snapshots of 3D models from multiple angles.

  ```bash
  python geometry_pipeline/snapshots.py --step_file <path_to_step_file> --snapshots
  ```

  **Options**:  
  `--obj_file`, `--step_file`, `--stl_file`, `-o OUTPUT_DIR`, `-r RESOLUTION`, `-d DIRECTION`, `-p`, `--reaxis_gravity`

### `describe`

- **`describer_v2.py`**: Generates descriptive metadata for 3D models using advanced language models.

  ```bash
  python describe/describer_v2.py "Describe the 3D model" --config <path_to_config> --prompts <path_to_prompts>
  ```

  **Options**:  
  `--config CONFIG`, `--prompts PROMPTS`, `-img REF_IMAGES`, `-o OUTPUT`

### `coding`

- **`coder.py`**: Generates CAD scripts based on design goals.

  ```bash
  python coding/coder.py "Design a mechanical part" --config <path_to_config> --prompts <path_to_prompts>
  ```

  **Options**:  
  `--config CONFIG`, `--master_config_path MASTER_CONFIG_PATH`, `--prompts PROMPTS`, `-o OUTPUT_DIR`

### `feedbacks`

- **`visual_feedback.py`**: Analyzes rendered images of a design against the design goal.

  ```bash
  python feedbacks/visual_feedback.py --design_goal "Design a mechanical part" --rendered_images <path_to_images>
  ```

  **Options**:  
  `--config CONFIG`, `--prompts PROMPTS`, `--reference_images REFERENCE_IMAGES`, `--rendered_images RENDERED_IMAGES`

### `retrieval`

- **`tools/build123d_retriever.py`**: Retrieves and manages documentation for CAD tools and libraries.

  ```bash
  python retrieval/tools/build123d_retriever.py [--force-rebuild] [--interactive] [--metric {l2,cosine}] [--query QUERY] [--debug]
  ```

  **Options**:  
  `--force-rebuild`: Force rebuild the database.  
  `--interactive`: Run in interactive mode to ask multiple questions.  
  `--metric {l2,cosine}`: Distance metric to use for similarity search.  
  `--query QUERY`: Query text to search in the database.  
  `--debug`: Enable debug mode for detailed logging.

  **Examples**:  
  Interactive mode:

  ```bash
  python retrieval/tools/build123d_retriever.py --interactive
  ```

  Single query:

  ```bash
  python retrieval/tools/build123d_retriever.py --query "How to extrude a shape?"
  ```

### `workflow`

- **`codecad_agent.py`**: Orchestrates the automation workflows for CAD design.

  ```bash
  python workflow/codecad_agent.py "Design a mechanical part" --config <path_to_config> --prompts <path_to_prompts>
  ```

  **Options**:  
  `--config CONFIG`: Path to the configuration file.  
  `--prompts PROMPTS`: Path to the prompts file.  
  `-img REF_IMAGES`: Path to reference images (optional).  
  `-o OUTPUT_DIR`: Directory to save output files (optional).

  **Example**:

  ```bash
  python workflow/codecad_agent.py "Design a mechanical part" --config workflow/config/code-llm.yaml --prompts workflow/prompts/code-llm.yaml -o output/
  ```
