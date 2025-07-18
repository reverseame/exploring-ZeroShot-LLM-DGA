# Exploring the Zero-Shot Potential of Large Language Models for Detecting Algorithmically Generated Domains

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A framework for evaluating Large Language Models in zero-shot detection of Algorithmically Generated Domains (AGDs) used by malware for Command and Control communication.

## Features

* **Zero-shot evaluation** of 9 LLMs from 4 major vendors (OpenAI, Anthropic, Google, Mistral)
* **Binary classification** framework for distinguishing AGDs from legitimate domains
* **Two prompting strategies**: Minimal (P1) and enhanced with lexical features (P2)
* **Comprehensive metrics** including Accuracy, Precision, Recall, F1-score, FPR, TPR, MCC, and Cohen's κ
* **Real time batch processing** with automatic retry mechanism for failed classifications
* **Reproducible experiments** aligned with the published research paper
* **CSV export** for detailed analysis and comparison

## Supported Models

| Provider | Model | Type | API Tag |
|----------|-------|------|---------|
| OpenAI | GPT-4o | Large | `gpt-4o-2024-11-20` |
| OpenAI | GPT-4o-mini | Small | `gpt-4o-mini-2024-07-18` |
| Anthropic | Claude 3.5 Sonnet | Large | `claude-3-5-sonnet-20241022` |
| Anthropic | Claude 3.5 Haiku | Small | `claude-3-5-haiku-20241022` |
| Google | Gemini 1.5 Pro | Large | `gemini-1.5-pro-002` |
| Google | Gemini 1.5 Flash | Small | `gemini-1.5-flash-002` |
| Google | Gemini 1.5 Flash-8B | Small | `gemini-1.5-flash-8b-001` |
| Mistral | Mistral Large | Large | `mistral-large-2411` |
| Mistral | Mistral Small | Small | `mistral-small-2409` |

## Installation

The framework runs on Python 3.12+. To use the evaluation framework, follow these installation steps:

### Requirements

It is necessary to install the required packages. To do this, execute the following command (it is recommended to use a virtualized Python environment):

```bash
pip3 install -r requirements.txt
```

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/reverseame/exploring-ZeroShot-LLM-DGA
   cd exploring-ZeroShot-LLM-DGA
   ```

2. **Set up API keys:**
   Create a `.secret` file in the root directory with your API keys using the exact format below:
   ```
   API_KEY_OPENAI="your_openai_api_key_here"
   API_KEY_ANTHROPIC="your_anthropic_api_key_here"
   API_KEY_MISTRALAI="your_mistralai_api_key_here"
   API_KEY_GEMINI="your_gemini_api_key_here"
   ```
   **Important**: Use the exact key names shown above and include the quotes around your API keys.

3. **Prepare the datasets:**
   - **Malicious domains**: Place domain family files in `prompts/datasetAGDFamilies/`
     - Each malware family should have its own CSV file (e.g., `conficker.csv`, `cryptolocker.csv`)
     - Each CSV file must contain one domain per line (no headers, no commas between domains)
     - Example format for `family_name.csv`:
       ```
       abc123domain.com
       xyz456domain.org
       random789domain.net
       ```
   - **Legitimate domains**: Place legitimate domains in `prompts/legitimateDomains/domains.csv`
     - One domain per line format (same as malicious domain files)
     - Example format:
       ```
       google.com
       facebook.com
       amazon.com
       ```
## Usage

### Example of use

#### Configuration

The `main.py` file contains the primary execution code. Before running experiments, configure the following parameters:

```python
# Execution configuration
SECOND_TRY = False        # Set to True for retry failed classifications
EXPERIMENT = 1           # Set to 1 or 2 for different experiments
BATCH_SIZE = 125         # Batch size for processing domains
SEND_REQUEST = True      # Set to False to skip LLM requests (analysis only)

# Select models to test (comment/uncomment as needed)
LLMS = [
    OpenAI("gpt-4o-2024-11-20"),
    OpenAI("gpt-4o-mini-2024-07-18"),
    Anthropic("claude-3-5-sonnet-20241022"),
    Anthropic("claude-3-5-haiku-20241022"),
    Gemini("gemini-1.5-pro-002"),
    Gemini("gemini-1.5-flash-002"),
    Gemini("gemini-1.5-flash-8b-001"),
    MistralAI("mistral-large-2411"),
    MistralAI("mistral-small-2409"),
]
```

#### Running Experiments

**Experiment 1 (P1 - Minimal Prompt):**
```bash
# Set EXPERIMENT = 1 in main.py
python main.py
```

**Experiment 2 (P2 - Enhanced Prompt with Lexical Features):**
```bash
# Set EXPERIMENT = 2 in main.py
python main.py
```

#### Workflow Execution

The framework follows a structured workflow:

1. **First Run (`SEND_REQUEST = True` and `SECOND_TRY = False`):**
   - Generates or loads prompts based on experiment configuration
   - Sends classification requests to selected LLMs in batches
   - Saves responses to `output/` directory
   - Analyzes results and generates comprehensive metrics

2. **Retry Run (`SEND_REQUEST = True` and `SECOND_TRY = True`):**
   - Identifies domains that were not properly classified
   - Automatically retries classification for missing domains
   - Continues processing until all domains are classified

3. **Analysis Only (`SEND_REQUEST = False`):**
   - Skips LLM API requests
   - Performs analysis on existing results in `output/` directory

### Experiment Configuration

The experiments are configured through the `experiment_config` dictionary in the `readPrompt()` function. Here's how each experiment is set up:

#### Experiment 1 (P1 - Minimal Prompt)
```python
1: {
    "middle_prompts": [],                    # No additional prompt components
    "final_prompt": "EndBinary.txt",         # Binary classification instructions
    "num_train_samples": 0,                  # Zero-shot (no training examples)
    "num_test_domains": 1000,                # 1,000 domains per malware family
    "num_legitimate_domains": 25000          # 25,000 legitimate domains from Tranco
}
```
- **Prompt Strategy**: Basic classification instructions without domain-specific knowledge
- **Approach**: Minimal prompt formulation for pure zero-shot evaluation

#### Experiment 2 (P2 - Enhanced Prompt)
```python
2: {
    "middle_prompts": ["Prompt1.txt"],       # Includes lexical feature analysis
    "final_prompt": "EndBinary.txt",         # Binary classification instructions  
    "num_train_samples": 0,                  # Zero-shot (no training examples)
    "num_test_domains": 1000,                # 1,000 domains per malware family
    "num_legitimate_domains": 25000          # 25,000 legitimate domains from Tranco
}
```
- **Prompt Strategy**: Enhanced with explicit lexical feature analysis instructions
- **Additional Component**: `Prompt1.txt` contains domain generation pattern analysis

#### Modifying Experiment Configuration

To modify the experiments, update the configuration in `main.py`:

```python
def readPrompt(experiment: int) -> tuple:
    # Configuration for experiments 1 and 2
    experiment_config = {
        1: {
            "middle_prompts": [],                # Add prompt files here for experiment 1
            "final_prompt": "EndBinary.txt",     # Change ending prompt if needed
            "num_train_samples": 0,              # Increase for few-shot (not used in paper)
            "num_test_domains": 1000,            # Domains per family to test
            "num_legitimate_domains": 25000      # Total legitimate domains
        },
        2: {
            "middle_prompts": ["Prompt1.txt"],   # Add/remove prompt components
            "final_prompt": "EndBinary.txt",     # Change ending prompt if needed
            "num_train_samples": 0,              # Increase for few-shot (not used in paper)
            "num_test_domains": 1000,            # Domains per family to test
            "num_legitimate_domains": 25000      # Total legitimate domains
        }
    }
```

**Key parameters to modify:**
- `middle_prompts`: List of prompt files from `prompts/Prompt4Experiments/` to include
- `num_test_domains`: Number of domains to test per malware family
- `num_legitimate_domains`: Total number of legitimate domains to include


### Results

After executing the experiments, the framework generates comprehensive results:

#### Output Files

- **LLM Responses**: `output/{model_name}_EXP{experiment_number}.out`
- **Global Metrics**: `metrics/GLOBAL_EXP{experiment_number}.csv`
- **Malicious Domain Metrics**: `metrics/MALICIOUS_EXP{experiment_number}.csv`
- **Benign Domain Metrics**: `metrics/BENIGN_EXP{experiment_number}.csv`
- **Retry Domains**: `try_again_domains/{model_name}_EXP{experiment_number}.json`

#### Metrics Interpretation

The CSV files contain the following performance metrics:
- `accuracy`: Overall classification accuracy
- `precision`: Precision score for malicious domain detection
- `recall`: Recall score (True Positive Rate)
- `f1_score`: F1-score (harmonic mean of precision and recall)
- `fpr`: False Positive Rate
- `tpr`: True Positive Rate
- `mcc`: Matthews Correlation Coefficient
- `kappa`: Cohen's Kappa Coefficient

## Project Structure

```
├── main.py                    # Main execution script
├── utils/
│   ├── analyzer.py            # Results analysis and metrics calculation
│   ├── generatePrompt.py      # Prompt generation and domain management
│   ├── metrics.py             # Metrics class definition
│   ├── file_utils.py          # File handling utilities
│   └── config.py              # Configuration management
├── models/
│   ├── LLM.py                 # Abstract base class for LLM implementations
│   ├── OpenAI/                # OpenAI API implementation
│   ├── Anthropic/             # Anthropic API implementation
│   ├── Gemini/                # Google Gemini API implementation
│   └── MistralAI/             # Mistral API implementation
├── prompts/                   # Prompt templates and instructions
│   ├── StartingPoints/        # Base prompt templates
│   ├── Prompt4Experiments/    # Experiment-specific prompt components
│   └── EndingPoints/          # Final instruction templates
├── dataset/                   # Generated datasets (auto-created)
├── output/                    # LLM responses (auto-created)
├── metrics/                   # Calculated metrics (auto-created)
├── requirements.txt           # Python dependencies
└── .secret                    # API keys configuration
```

## Troubleshooting

### Common Issues

1. **API Rate Limits**: The script includes automatic retry with 15-second delays for rate limit handling
2. **Missing Domain Classifications**: Use `SECOND_TRY = True` to automatically retry unclassified domains
3. **File Permissions**: Ensure write permissions for `dataset/`, `output/`, and `metrics/` directories
4. **API Key Issues**: Verify your `.secret` file format and key validity

### Error Files

- `format_error.txt`: Contains malformed LLM responses that couldn't be parsed
- `try_again_domains/`: Directory containing domains that need reclassification

## License

Licensed under the [GNU GPLv3](LICENSE) license.

## How to cite

If you are using this software or find our research useful, please cite it as follows:

```bibtex
@InProceedings{pelayobenedet2025zeroshot,
author={Pelayo-Benedet, Tom{\'a}s
and Rodr{\'i}guez, Ricardo J.
and Ga{\~{n}}{\'a}n, Carlos H.},
editor={Egele, Manuel
and Moonsamy, Veelasha
and Gruss, Daniel
and Carminati, Michele},
title={{Poster: Exploring the Zero-Shot Potential of Large Language Models for Detecting Algorithmically Generated Domains}},
booktitle={Detection of Intrusions and Malware, and Vulnerability Assessment},
year={2025},
publisher={Springer Nature Switzerland},
address={Cham},
pages={86--92},
abstract={Domain generation algorithms enable resilient malware communication by generating pseudo-random domain names. While traditional detection relies on task-specific algorithms, the use of Large Language Models (LLMs) to identify Algorithmically Generated Domains (AGDs) remains largely unexplored. This work evaluates nine LLMs from four major vendors in a zero-shot environment, without fine-tuning. The results show that LLMs can distinguish AGDs from legitimate domains, but they often exhibit a bias, leading to high false positive rates and overconfident predictions. Adding linguistic features offers minimal accuracy gains while increasing complexity and errors. These findings highlight both the promise and limitations of LLMs for AGD detection, indicating the need for further research before practical implementation.},
isbn={978-3-031-97623-0}
}
```

## Funding support

Part of this research was supported by the Spanish National Cybersecurity Institute (INCIBE) under *Proyectos Estratégicos de Ciberseguridad -- CIBERSEGURIDAD EINA UNIZAR* and by the Recovery, Transformation and Resilience Plan funds, financed by the European Union (Next Generation).

We extend our gratitude to the DGArchive team for providing the dataset in advance, enabling this research.

![INCIBE_logos](misc/img/INCIBE_logos.jpg)