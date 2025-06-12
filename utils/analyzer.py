import os
import math
from utils.metrics import Metrics
from utils.file_utils import save_to_text_file

class Analyzer:
    def __init__(self, malicious_dir: str, benign_file: str):
        """
        Initializes the domain classifier analyzer.

        Args:
            malicious_dir (str): Path to the directory containing files with malicious domains.
            benign_file (str): Path to the file containing benign domains.
        """
        self.malicious_dir = malicious_dir
        self.benign_file = benign_file
        self.format_error_file = "format_error.txt"

    def validate_domains(self, domains: list, classifications: list, output_file: str) -> bool:
        """
        Validates that all domains in the `domains` list are present in the `classifications` list.
        Writes any domains missing from `classifications` to the specified output file.

        Args:
            domains (list): A list of domains to validate.
            classifications (list): A list of classifications where each entry starts with a domain.
            output_file (str): The path to the file where missing domains will be written.

        Returns:
            bool: True if all domains have classification, False if some are missing.
        """
        # Extract the domain names from the classifications list into a set for fast lookups
        classification_domains = {entry.split("|")[0] for entry in classifications}

        ret = True
        data = []

        # Remove duplicates
        unique_domains = list(set(domains))

        for domain in unique_domains:
            # Check if the domain is not in the set of classification domains
            if domain not in classification_domains:
                # Write the missing domain to the output file
                data.append(domain)
                ret = False
        
        if not ret:
            save_to_text_file(filepath=output_file, data=data)
        else:
            if os.path.exists(output_file):
                os.remove(output_file)

        return ret

    def read_file(self, file_path: str) -> tuple:
        """
        Reads the content of a file and extracts the initial domains and classifications.

        Args:
            file_path (str): Absolute or relative path to the file to analyze.

        Returns:
            tuple: A tuple containing two lists:
                - List of initial domains between "***************" and "---------------".
                - List of classifications after "---------------".
        """
        try:
            with open(file_path, 'r') as file:
                content = file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"The file '{file_path}' does not exist.")
        except Exception as e:
            raise Exception(f"Error reading the file '{file_path}': {e}")

        blocks = content.split("***************")
        classifications = []
        domains = []

        for block in blocks:
            if "---------------" in block:
                try:
                    # Extract the part before "---------------" for initial domains
                    before_separator = block.split("---------------", 1)[0]
                    domains.extend(line.strip() for line in before_separator.strip().split(","))
                    # Extract the part after "---------------" for classifications
                    after_separator = block.split("---------------", 1)[1]
                    classifications.extend(line.strip() for line in after_separator.strip().splitlines())
                except IndexError:
                    continue

        return domains, classifications

    def compute_metrics(self, tp: int, fp: int, fn: int, tn: int) -> Metrics:
        """
        Computes performance metrics given the confusion matrix values.

        Args:
            tp (int): True Positives.
            fp (int): False Positives.
            fn (int): False Negatives.
            tn (int): True Negatives.

        Returns:
            Metrics: An instance of the Metrics class containing calculated metrics.
        """
        accuracy = (tp + tn) / (tp + fp + fn + tn) if (tp + fp + fn + tn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        tpr = recall
        if math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)) != 0:
            mcc = ((tp * tn) - (fp * fn)) / math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
        else:
            mcc = 0
        if (tn+fp+fn+tp) != 0:
            p0 = (tn+tp)/(tn+fp+fn+tp)
            pa = ((tn+tp)/(tn+fp+fn+tp))*((tn+fn)/(tn+fp+fn+tp))
            pb = ((fn+tp)/(tn+fp+fn+tp))*((fp+tp)/(tn+fp+fn+tp))
            pe = pa + pb
            if pe != 1:
                kappa = (p0-pe)/(1-pe)
            else:
                kappa = 0
        else:
            kappa = 0

        return Metrics(accuracy, precision, recall, f1_score, fpr, tpr, mcc, kappa)

    def analyze_classifier(self, result_list: list) -> tuple:
        """
        Analyzes the classifier and computes metrics for malicious, benign, and overall domains.

        Args:
            result_list (list): A list of strings in the format "[DOMAIN]|[RESULT]|[CONFIDENCE]".

        Returns:
            tuple: A tuple of three Metrics instances (malicious_metrics, benign_metrics, overall_metrics).
        """
        malicious_domains = set()
        benign_domains = set()
        analyzed_domains = set()

        for file in os.listdir(self.malicious_dir):
            with open(os.path.join(self.malicious_dir, file), 'r') as f:
                malicious_domains.update(line.strip() for line in f)

        with open(self.benign_file, 'r') as f:
            benign_domains.update(line.strip() for line in f)

        # Initialize confusion matrix values
        tp, fn, tn, fp = 0, 0, 0, 0

        # Process each result in the result list
        for result in result_list:
            try:
                domain, classification, _ = result.split('|')
            except ValueError:
                # Write the incorrect line to the error file
                with open(self.format_error_file, 'a') as error_file:
                    error_file.write(f"{result}\n")
                continue
            if domain in analyzed_domains:
                continue
            if domain in malicious_domains:
                if classification == 'Y':  # Correctly classified as malicious
                    tp += 1
                else:  # Incorrectly classified as benign
                    fn += 1
                analyzed_domains.add(domain)
            elif domain in benign_domains:
                if classification == 'N':  # Correctly classified as benign
                    tn += 1
                else:  # Incorrectly classified as malicious
                    fp += 1
                analyzed_domains.add(domain)
            else:
                # Domains that are neither in malicious nor benign lists are ignored
                continue

        # Compute metrics for malicious, benign, and overall domains
        malicious_metrics = self.compute_metrics(tp, 0, fn, 0)
        benign_metrics = self.compute_metrics(tn, 0, fp, 0)
        overall_metrics = self.compute_metrics(tp, fp, fn, tn)

        return malicious_metrics, benign_metrics, overall_metrics

    def check_domains(self, file_path: str, output_path: str) -> bool:
        """
        Checks if all domains have been classified.

        Returns:
            bool: True if all domains have classification, False if some are missing.
        """
        domains, lines_read = self.read_file(file_path)
        return self.validate_domains(domains, lines_read, output_file=output_path)

    def analyze(self, file_path: str, size: int) -> tuple:
        """
        Analyzes a classifier result file and returns metrics for malicious, benign, and overall domains.

        Args:
            file_path (str): Path to the file containing classifier results.
            size (int): Size of the total classifications to use.

        Returns:
            tuple: A tuple of three Metrics instances (malicious_metrics, benign_metrics, overall_metrics).
        """
        domains, lines_read = self.read_file(file_path)
        lines = lines_read[0:size]
        return self.analyze_classifier(result_list=lines)