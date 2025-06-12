"""
Main script for LLM evaluation experiments - Binary Classification (Experiments 1 & 2).
This program manages prompt generation, sending requests to different language models,
and analyzing their responses for binary domain classification tasks.
"""

import os
import math

# Models - Import different LLM implementations
from models.Gemini.Gemini import Gemini
from models.OpenAI.OpenAI import OpenAI
from models.Anthropic.Anthropic import Anthropic
from models.MistralAI.MistralAI import MistralAI

# Personal libraries - Import utility modules
from utils.generatePrompt import PromptGenerator
from utils.file_utils import save_to_text_file, load_from_text_file
from utils.analyzer import Analyzer

# Execution configuration
SECOND_TRY = False        # Flag to indicate if this is a second classification attempt
EXPERIMENT = 2           # ID of the experiment to run (1 or 2)
BATCH_SIZE = 125         # Batch size for processing domains
SEND_REQUEST = False      # Flag to control whether to send requests to LLMs

# List of available LLMs - Comment/uncomment to select models for testing
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

# Core configuration constants
DATASET_DIR = "dataset/"                  # Directory for storing datasets
SECOND_TRY_DOMAINS = "try_again_domains"  # Directory for domains needing reclassification
METRICS_DIR = "metrics/"                  # Directory for storing metrics
OUTPUT_DIR = "output"                     # Directory for results

# Initialize core components
GENERATOR = PromptGenerator(
    "prompts/",
    "prompts/datasetAGDFamilies",
    "prompts/legitimateDomains/domains.csv"
)
ANALYZER = Analyzer("prompts/datasetAGDFamilies","prompts/legitimateDomains/domains.csv")

def readPrompt(experiment: int) -> tuple:
    """
    Reads or generates prompts for binary classification experiments (1 or 2).

    Parameters:
    - experiment (int): The experiment number (1 or 2).

    Returns:
    - tuple: A tuple containing:
        - explanationPrompt (str): The explanation prompt.
        - samplesPromptList (list): The list of sample prompts.

    Raises:
    - ValueError: If the experiment is not 1 or 2.
    """

    # Validate experiment number
    if experiment not in [1, 2]:
        raise ValueError(f"'experiment' with value {experiment} must be 1 or 2")

    # Create necessary directories
    os.makedirs(DATASET_DIR, exist_ok=True)
    os.makedirs(SECOND_TRY_DOMAINS, exist_ok=True)

    # Configuration for experiments 1 and 2
    experiment_config = {
        1: {
            "middle_prompts": [],
            "final_prompt": "EndBinary.txt",
            "num_train_samples": 0,
            "num_test_domains": 1000,
            "num_legitimate_domains": 25000
        },
        2: {
            "middle_prompts": ["Prompt1.txt"],
            "final_prompt": "EndBinary.txt",
            "num_train_samples": 0,
            "num_test_domains": 1000,
            "num_legitimate_domains": 25000
        }
    }

    config = experiment_config[experiment]

    # Define paths for saving/loading prompts
    explanation_prompt_path = os.path.join(DATASET_DIR, str(experiment), "prompt.json")
    samples_prompt_list_path = os.path.join(DATASET_DIR, str(experiment), "samples.json")

    os.makedirs(os.path.join(DATASET_DIR, str(experiment)), exist_ok=True)

    # Modify path for second try scenarios
    if SECOND_TRY:
        samples_prompt_list_path = os.path.join(SECOND_TRY_DOMAINS, f"{LLMS[0].model}_EXP{str(EXPERIMENT)}.json")

    # Try to load existing prompts
    explanationPrompt = load_from_text_file(explanation_prompt_path)
    samplesPromptList = load_from_text_file(samples_prompt_list_path)

    # Generate new prompts if needed
    if explanationPrompt is None or samplesPromptList is None:
        explanationPrompt, samplesPromptList = GENERATOR.generate_prompt(
            starting_prompt="StartBase.txt",
            middle_prompts=config["middle_prompts"],
            final_prompt=config["final_prompt"],
            num_train_samples=config["num_train_samples"],
            num_test_domains=config["num_test_domains"],
            num_legitimate_domains=config["num_legitimate_domains"]
        )
        # Save generated prompts
        save_to_text_file(explanation_prompt_path, explanationPrompt)
        save_to_text_file(samples_prompt_list_path, samplesPromptList)
    
    return explanationPrompt, samplesPromptList



def main():
    """
    Main function that executes the binary classification experiment flow:
    1. Creates necessary directories
    2. Reads or generates prompts for experiments 1 or 2
    3. Executes requests on configured LLMs
    4. Analyzes results and generates metrics
    """
    # Validate experiment number
    if EXPERIMENT not in [1, 2]:
        print(f"Error: EXPERIMENT must be 1 or 2, got {EXPERIMENT}")
        return

    # Initialize directory structure
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DATASET_DIR, exist_ok=True)

    # Get prompts for the selected experiment
    (explanationPrompt, samplesPromptList) = readPrompt(experiment=EXPERIMENT)

    if SEND_REQUEST:
        # Process each configured LLM
        for llm in LLMS:
            model_name = llm.model
            conversation_history = llm.craftConversationHistory(explanationPrompt, "yes")

            print("-"*15)
            print("Executing model: " + model_name)
            print("-"*15)

            if SECOND_TRY:
                # Handle reclassification of domains
                output_file = os.path.join(OUTPUT_DIR, f"{model_name}_EXP{str(EXPERIMENT)}.out")
                try_again_path = os.path.join(SECOND_TRY_DOMAINS, f"{model_name}_EXP{str(EXPERIMENT)}.json")
                all_classified = ANALYZER.check_domains(file_path=output_file, output_path=try_again_path)
                
                # Continue processing until all domains are classified
                while not all_classified:
                    samples_prompt_list_path = os.path.join(SECOND_TRY_DOMAINS, f"{LLMS[0].model}_EXP{str(EXPERIMENT)}.json")
                    samplesPromptList = load_from_text_file(samples_prompt_list_path)
                    print("Total size of re-testing dataset: " + str(len(samplesPromptList)))
                    
                    # Process domains in batches
                    for i in range(0, len(samplesPromptList), BATCH_SIZE):
                        chunk = samplesPromptList[i:i + BATCH_SIZE]
                        samplesPrompt = GENERATOR.create_prompt_from_domain_list(chunk)

                        # Calculate and display progress
                        len_chunck = len(samplesPrompt.split(","))
                        i_max = math.ceil(len(samplesPromptList) / BATCH_SIZE)
                        print(f"Processing chunk {i // BATCH_SIZE + 1}/{i_max} with {len_chunck} domains")

                        # Get LLM response and save results
                        response, _ = llm.chat(samplesPrompt, conversation_history)
                        with open(output_file, 'a', encoding='utf-8') as f:
                            f.write(samplesPrompt + "\n")
                            f.write("-" * 15 + "\n")
                            f.write(response + "\n")
                            f.write("*" * 15 + "\n")
                        
                        # Check if all domains are now classified
                        all_classified = ANALYZER.check_domains(file_path=output_file, output_path=try_again_path)
                    
            else:  
                # First-time processing of domains
                print("Total size of testing dataset: " + str(len(samplesPromptList)))
                
                # Process domains in batches
                for i in range(0, len(samplesPromptList), BATCH_SIZE):
                    chunk = samplesPromptList[i:i + BATCH_SIZE]
                    samplesPrompt = GENERATOR.create_prompt_from_domain_list(chunk)

                    # Calculate and display progress
                    len_chunck = len(samplesPrompt.split(","))
                    i_max = math.ceil(len(samplesPromptList) / BATCH_SIZE)
                    print(f"Processing chunk {i // BATCH_SIZE + 1}/{i_max} with {len_chunck} domains")

                    # Get LLM response
                    response, _ = llm.chat(samplesPrompt, conversation_history)

                    # Save results to output file
                    output_file = os.path.join(OUTPUT_DIR, f"{model_name}_EXP{str(EXPERIMENT)}.out")
                    with open(output_file, 'a', encoding='utf-8') as f:
                        f.write(samplesPrompt + "\n")
                        f.write("-" * 15 + "\n")
                        f.write(response + "\n")
                        f.write("*" * 15 + "\n")
    
    # Analyze results for each LLM
    for llm in LLMS:
        model_name = llm.model
        print("-"*15)
        print("Stats model: " + model_name)
        print("-"*15)
        
        # Define paths for analysis
        file_path = os.path.join(OUTPUT_DIR, f"{model_name}_EXP{str(EXPERIMENT)}.out")
        try_again_path = os.path.join(SECOND_TRY_DOMAINS, f"{model_name}_EXP{str(EXPERIMENT)}.json")

        # Only analyze if all domains were correctly processed
        if ANALYZER.check_domains(file_path=file_path, output_path=try_again_path):
            # Handle binary classification analysis
            (malicious_metrics, benign_metrics, overall_metrics) = ANALYZER.analyze(file_path=file_path, size=100000)
            
            # Create metrics directory
            os.makedirs(METRICS_DIR, exist_ok=True)
            
            # Save overall metrics
            metrics_path = os.path.join(METRICS_DIR, f"GLOBAL_EXP{str(EXPERIMENT)}.csv")
            file_exists = os.path.isfile(metrics_path)
            with open(metrics_path, mode='a') as file:
                if not file_exists:
                    file.write("model,"+overall_metrics.csv_header() + '\n')
                file.write(model_name+","+overall_metrics.to_csv() + '\n')
            
            # Save malicious domain metrics
            metrics_path = os.path.join(METRICS_DIR, f"MALICIOUS_EXP{str(EXPERIMENT)}.csv")
            file_exists = os.path.isfile(metrics_path)
            with open(metrics_path, mode='a') as file:
                if not file_exists:
                    file.write("model,"+malicious_metrics.csv_header() + '\n')
                file.write(model_name+","+malicious_metrics.to_csv() + '\n')
            
            # Save benign domain metrics
            metrics_path = os.path.join(METRICS_DIR, f"BENIGN_EXP{str(EXPERIMENT)}.csv")
            file_exists = os.path.isfile(metrics_path)
            with open(metrics_path, mode='a') as file:
                if not file_exists:
                    file.write("model,"+benign_metrics.csv_header() + '\n')
                file.write(model_name+","+benign_metrics.to_csv() + '\n')
        else:
            print(f"Some domains didn't get classified, please review {try_again_path}")

if __name__ == "__main__":
    main()