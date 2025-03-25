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
pip install cicada-agent # this enables the "core" modules
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

For everything,

```bash
pip install cicada-agent[all]
```

### Installation Steps (For Developers)

```bash
git clone https://github.com/Oaklight/cicada.git
cd cicada

# always recommend to use conda or other tools to create dedicated dev environment
conda env create -f environment.yml
conda activate cicada
```

#### Core Installation

Core module provides the fundamental functionalities of CICADA framework.

```bash
pip install -e . # this installs core modules
```

#### CodeCAD Installation

CodeCAD module focuses on CAD code generation and execution. It requires additional dependencies:

```bash
pip install -e .[codecad]
```

#### Everything Installation

If you want to install all modules and dependencies:

```bash
pip install -e .[all]
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

  <!--

## Configuration Samples

Configuration samples are pre - defined sets of configurations that serve as examples for users to understand how to set up different aspects of a system. In the context of our project, the `configuration.samples` directory contains various configuration files that can be used as a starting point for different scenarios.

### What's Inside

The `configuration.samples` directory has sub - directories and files related to different types of configurations:

- **Configs Directory**:
  - `coding.yaml`: This configuration file is likely related to the coding - related settings. It might contain parameters for code editors, coding styles, or any specific configurations related to the coding tasks within our system.
  - `core.yaml`: Could be related to the core functionality of the system. It may define settings such as default values for certain operations, initial states, or fundamental configurations that affect the overall behavior of the application.
  - Other files like `describe.yaml`, `feedback.yaml`, `retrieval.yaml`, `tools.yaml` also contain configurations specific to their respective areas. For example, `describe.yaml` might be for settings related to the description generation part of the system, `feedback.yaml` for feedback - related configurations, and so on.
  - Inside the `workflow` sub - directory, there are files like `code - llm.yaml`, `describe - vlm.yaml`, etc. These are related to the workflow configurations, especially when it comes to integrating with different language models or performing specific tasks in a sequence.
- **Prompts Directory**:
  - Similar to the `configs` directory, the `prompts` directory also has files related to different types of prompts. For example, `coding.yaml` in the `prompts` directory might contain specific prompts related to coding tasks, while the files in the `describe` and `feedback` sub - directories of `prompts` are related to the prompts used for description and feedback generation respectively.

### How to Use

1. **Identify Your Use Case**: First, determine which aspect of the system you are trying to configure. For example, if you are working on coding - related tasks, you might look at the `coding.yaml` file in the `configuration.samples` directory.
2. **Copy and Modify**: You can copy the relevant configuration file to a location where you can make your customizations. Then, start modifying the values according to your specific requirements. For instance, if the `coding.yaml` file has a parameter for the maximum line length in code, and you want to change it to a different value, you can do so in your copied file.
3. **Refer to Documentation**: Along with the sample configurations, it's important to refer to the overall project documentation. The documentation will provide more context on what each configuration parameter means and how it interacts with other parts of the system. This will help you make informed decisions while customizing the configurations. -->
