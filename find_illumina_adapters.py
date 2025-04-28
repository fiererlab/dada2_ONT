"""

find_illumina_adapters.py: find the location and occurence frequency of illumina adapters in 
ONT MinION data. 
	Input: .fastq file
	Output: a .txt file containing amplicon metrics

"""
__author__ = "Mobeen & the Robot"
__year__ = "2025"
__credits__ = ["Mobeen & the Robot"]

import argparse
import gzip
import statistics
import matplotlib.pyplot as plt
import os

def calculate_mismatches(sequence, query, start_pos):
    """
    Calculate the number of mismatches between the query and the sequence at a given position.
    Parameters:
        sequence (str): The sequence from the FASTQ file.
        query (str): The search query string.
        start_pos (int): The start position where the query is found.
    Returns:
        int: The number of mismatches.
    """
    # Extract the subsequence from the sequence
    subsequence = sequence[start_pos-1:start_pos-1+len(query)]
    mismatches = sum(1 for a, b in zip(subsequence, query) if a != b)
    return mismatches

def analyze_fastq(fastq_file, search_string):
    """
    Analyze a FASTQ file to identify sequences containing a specific string and calculate mismatches.
    Parameters:
        fastq_file (str): Path to the zipped FASTQ file (.fastq.gz).
        search_string (str): The string to search for in the sequences.
    Returns:
        dict: Results containing total sequences, count of matches, percentage,
              mismatch statistics, median start position, median end position, and start positions for histograms.
    """
    total_sequences = 0
    count_found = 0
    count_multiple_occurrences = 0  # To track sequences with more than one occurrence of the query
    one_mismatch_count = 0
    two_or_more_mismatches_count = 0
    start_positions = []  # To store start positions of found queries
    end_positions = []  # To store end positions of found queries

    with gzip.open(fastq_file, "rt") as f:
        while True:
            header = f.readline().strip()
            if not header:
                break
            sequence = f.readline().strip()
            f.readline()  # Skip "+"
            f.readline()  # Skip quality scores
            total_sequences += 1

            # Count the occurrences of the query in the sequence
            query_count = sequence.count(search_string)

            if query_count > 0:
                count_found += 1
                if query_count > 1:
                    count_multiple_occurrences += 1  # Count if query occurs more than once
                start_pos = sequence.find(search_string) + 1  # 1-based index
                end_pos = start_pos + len(search_string) - 1  # End position of the match
                mismatches = calculate_mismatches(sequence, search_string, start_pos)

                # Store the start and end positions for plotting and median calculations
                start_positions.append(start_pos)
                end_positions.append(end_pos)

                # Classify based on mismatches
                if mismatches == 1:
                    one_mismatch_count += 1
                elif mismatches >= 2:
                    two_or_more_mismatches_count += 1

    # Median and average calculations
    median_start_pos = statistics.median(start_positions) if start_positions else None
    median_end_pos = statistics.median(end_positions) if end_positions else None
    average_match_length = len(search_string)  # For fixed-length queries, this is constant

    percentage_found = (count_found / total_sequences) * 100 if total_sequences > 0 else 0
    percentage_multiple_occurrences = (count_multiple_occurrences / total_sequences) * 100 if total_sequences > 0 else 0
    percentage_one_mismatch = (one_mismatch_count / count_found) * 100 if count_found > 0 else 0
    percentage_two_or_more_mismatches = (two_or_more_mismatches_count / count_found) * 100 if count_found > 0 else 0

    return {
        "total_sequences": total_sequences,
        "count_found": count_found,
        "percentage_found": percentage_found,
        "percentage_multiple_occurrences": percentage_multiple_occurrences,
        "percentage_one_mismatch": percentage_one_mismatch,
        "percentage_two_or_more_mismatches": percentage_two_or_more_mismatches,
        "start_positions": start_positions,  # Added to return start positions for histogram
        "median_start_position": median_start_pos,
        "median_end_position": median_end_pos,
        "average_match_length": average_match_length
    }

def plot_histogram(start_positions, query, output_histograms):
    """
    Generate a histogram of the start positions and save it as a PNG file.
    Parameters:
        start_positions (list): List of start positions where the query was found.
        query (str): The query string for labeling.
        output_histograms (str): The directory to save PNG histogram files.
    """
    if start_positions:
        plt.hist(start_positions, bins=20, color='skyblue', edgecolor='black')
        plt.title(f"Histogram of Start Positions for Query '{query}'")
        plt.xlabel("Start Position")
        plt.ylabel("Frequency")
        plt.grid(True)
        plt.tight_layout()

        # Ensure the output directory exists
        if not os.path.exists(output_histograms):
            os.makedirs(output_histograms)

        # Save the plot as a PNG file in the specified directory
        plt.savefig(os.path.join(output_histograms, f"{query}_start_positions_histogram.png"))
        plt.close()

def write_results_to_file(results, output_file):
    """
    Write the results of the analysis to a text file.
    Parameters:
        results (dict): The results dictionary containing analysis data.
        output_file (str): The path of the output text file.
    """
    with open(output_file, 'w') as f:
        for query, res in results.items():
            f.write(f"Results for Query: '{query}'\n")
            f.write(f"Total sequences: {res['total_sequences']}\n")
            f.write(f"Sequences containing '{query}': {res['count_found']}\n")
            f.write(f"Percentage containing '{query}': {res['percentage_found']:.2f}%\n")
            f.write(f"Percentage of sequences where '{query}' occurs more than once: {res['percentage_multiple_occurrences']:.2f}%\n")
            f.write(f"Percentage with 1 mismatch: {res['percentage_one_mismatch']:.2f}%\n")
            f.write(f"Percentage with 2 or more mismatches: {res['percentage_two_or_more_mismatches']:.2f}%\n")
            f.write(f"Median start position: {res['median_start_position']}\n")
            f.write(f"Median end position: {res['median_end_position']}\n")
            f.write(f"Average match length: {res['average_match_length']}\n")
            f.write("\n")

def main():
    parser = argparse.ArgumentParser(description="Analyze a FASTQ file for specific query strings.")
    parser.add_argument("--fastq_file", type=str, required=True, help="Path to the FASTQ file (.fastq.gz).")
    parser.add_argument("--query", type=str, nargs="+", required=True, help="Space-delimited list of query strings.")
    parser.add_argument("--results", type=str, default="results.txt", help="Path to output results file (default: results.txt).")
    parser.add_argument("--output_histograms", type=str, default="output", help="Directory to save PNG histogram files (default: output).")

    args = parser.parse_args()
    fastq_file = args.fastq_file
    queries = args.query
    results_file = args.results  # Updated variable name to match new argument
    output_histograms = args.output_histograms  # Update variable name to match new argument

    results = {}
    
    for query in queries:
        print(f"Analyzing for query: '{query}'")
        result = analyze_fastq(fastq_file, query)
        results[query] = result
        
        print(f"Total sequences: {result['total_sequences']}")
        print(f"Sequences containing '{query}': {result['count_found']}")
        print(f"Percentage containing '{query}': {result['percentage_found']:.2f}%")
        print(f"Percentage of sequences where '{query}' occurs more than once: {result['percentage_multiple_occurrences']:.2f}%")
        print(f"Percentage with 1 mismatch: {result['percentage_one_mismatch']:.2f}%")
        print(f"Percentage with 2 or more mismatches: {result['percentage_two_or_more_mismatches']:.2f}%")
        print(f"Median start position: {result['median_start_position']}")
        print(f"Median end position: {result['median_end_position']}")
        print(f"Average match length: {result['average_match_length']}")

        # Generate and save histogram
        plot_histogram(result['start_positions'], query, output_histograms)

    # Write all results to the specified output file
    write_results_to_file(results, results_file)  # Use updated argument name here
    print(f"Results written to {results_file}")

if __name__ == "__main__":
    main()
