# Configuration Samples

Configuration samples are pre - defined sets of configurations that serve as examples for users to understand how to set up different aspects of a system. In the context of our project, the [`configuration.samples` directory](https://github.com/Oaklight/cicada/tree/master/configuration.samples) contains various configuration files that can be used as a starting point for different scenarios.

## What's Inside

The [`configuration.samples` directory](https://github.com/Oaklight/cicada/tree/master/configuration.samples) has sub - directories and files related to different types of configurations:

- **Configs Directory**:
  - `coding.yaml`: This configuration file is likely related to the coding - related settings. It might contain parameters for code editors, coding styles, or any specific configurations related to the coding tasks within our system.
  - `core.yaml`: Could be related to the core functionality of the system. It may define settings such as default values for certain operations, initial states, or fundamental configurations that affect the overall behavior of the application.
  - Other files like `describe.yaml`, `feedback.yaml`, `retrieval.yaml`, `tools.yaml` also contain configurations specific to their respective areas. For example, `describe.yaml` might be for settings related to the description generation part of the system, `feedback.yaml` for feedback - related configurations, and so on.
  - Inside the `workflow` sub - directory, there are files like `code - llm.yaml`, `describe - vlm.yaml`, etc. These are related to the workflow configurations, especially when it comes to integrating with different language models or performing specific tasks in a sequence.
- **Prompts Directory**:
  - Similar to the `configs` directory, the `prompts` directory also has files related to different types of prompts. For example, `coding.yaml` in the `prompts` directory might contain specific prompts related to coding tasks, while the files in the `describe` and `feedback` sub - directories of `prompts` are related to the prompts used for description and feedback generation respectively.

## How to Use

1. **Identify Your Use Case**: First, determine which aspect of the system you are trying to configure. For example, if you are working on coding - related tasks, you might look at the `coding.yaml` file in the [`configuration.samples` directory](https://github.com/Oaklight/cicada/tree/master/configuration.samples).
2. **Copy and Modify**: You can copy the relevant configuration file to a location where you can make your customizations. Then, start modifying the values according to your specific requirements. For instance, if the `coding.yaml` file has a parameter for the maximum line length in code, and you want to change it to a different value, you can do so in your copied file.
3. **Refer to Documentation**: Along with the sample configurations, it's important to refer to the overall project documentation. The documentation will provide more context on what each configuration parameter means and how it interacts with other parts of the system. This will help you make informed decisions while customizing the configurations.
