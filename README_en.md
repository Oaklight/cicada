# CICADA: Collaborative Intelligent CAD Automation Design Agent

[中文](./README_zh.md) | [English](./README_en.md)

Welcome to **CICADA**, the Collaborative Intelligent CAD Automation Design Agent. CICADA is a cutting-edge framework designed to streamline and enhance the CAD design process through intelligent automation and collaboration. This repository contains the core modules and utilities that power CICADA, enabling seamless integration with CAD workflows.

📖 **Documentation**: For detailed documentation and tutorials, visit [CICADA Documentation](https://cicada.lab.oaklight.cn).

---

## Repository Structure

The repository is organized into the following main modules:

- **common**: Core utilities and shared functionalities across the framework.
- **geometry_pipeline**: Tools for processing and converting 3D models, including point cloud generation and snapshots.
- **describe**: Components for generating and managing descriptive metadata for 3D models.
- **coding**: Code generation, execution, and debugging tools for CAD automation.
- **feedbacks**: Modules for analyzing and providing feedback on design iterations.
- **retrieval**: Tools for retrieving and management of documentation, model data, and design resources.
- **workflow**: Orchestration of CICADA's automation workflows and agent management.

---

## Setting Up the Environment

### Prerequisites

Before setting up CICADA, ensure you have the following installed:

- **Python 3.9+**
- **Conda** or **pip** (for dependency management)

### Installation Steps (Quick Start)

```bash
# activate your venv or conda env first
pip install cicada-agent
```

### Installation Steps (For Developers)

#### 1. Clone the Repository

```bash
git clone https://github.com/Oaklight/cicada.git
cd cicada
```

#### 2. Install Dependencies

**Option 1: Using Conda (Recommended)**

```bash
conda env create -f environment.yml
conda activate cicada
```

**Option 2: Using pip**

```bash
python -m venv cicada
source cicada/bin/activate
pip install -r requirements.txt
```

#### 3. Update API Keys

The provided API keys in the config files are deprecated. Update the `api_key` and `api_base_url` in `config.yaml` or `config/*.yaml` in each module:

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

---

## Contributing

We welcome contributions from the community! If you'd like to contribute to CICADA, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Submit a pull request with a detailed description of your changes.

---

## License

CICADA is licensed under the **MIT License**. For more details, see the [LICENSE](./LICENSE) file.

---

## Contact

For questions, feedback, or support, please post via [GitHub Issues](https://github.com/Oaklight/cicada/issues) or contact us at **[dingpeng]@@uchicago[dot]edu**.

---

## Citation

If you use Cicada in your research, please consider citing:

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

**CICADA** — Revolutionizing CAD Design with Intelligent Automation. 🚀
