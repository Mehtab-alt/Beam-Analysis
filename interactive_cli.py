import argparse
import logging
import os

from src.main import run_pipeline
from src.utils.config_loader import load_config
from src.utils.logging_config import setup_logging
from src.utils.exceptions import AnalysisError, ConfigError

def get_user_input():
    """
    Prompts the user for input to configure the analysis.
    """
    print("--- Civil Engineering Beam Analysis: Interactive CLI ---")
    
    # Get config file path
    config_path = input("Enter the path to the configuration file (default: config.yaml): ").strip()
    if not config_path:
        config_path = 'config.yaml'

    try:
        config = load_config(config_path)
        if not config:
            print("Failed to load configuration. Exiting.")
            return None
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return None

    # Get output directory
    output_dir_default = config.get('global', {}).get('output_dir', 'output/')
    output_dir = input(f"Enter the output directory (default: {output_dir_default}): ").strip()
    if output_dir:
        config['global']['output_dir'] = output_dir
    else:
        config['global']['output_dir'] = output_dir_default

    # Get log level
    log_level_default = config.get('logging', {}).get('level', 'INFO')
    print(f"Available log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    log_level = input(f"Enter the logging level (default: {log_level_default}): ").strip().upper()
    if log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        config['logging']['level'] = log_level
    else:
        config['logging']['level'] = log_level_default

    # Get tasks to run
    available_tasks = [task.get('name', f"Task {i+1}") for i, task in enumerate(config.get('analysis_tasks', []))]
    if available_tasks:
        print("Available analysis tasks:")
        for i, task_name in enumerate(available_tasks):
            print(f"  {i+1}. {task_name}")
        
        task_indices_input = input("Enter the numbers of the tasks to run (comma-separated, e.g., 1,3 or 'all'): ").strip()
        if task_indices_input.lower() == 'all' or not task_indices_input:
            # Run all tasks, no change needed
            pass
        else:
            try:
                selected_indices = [int(i.strip()) - 1 for i in task_indices_input.split(',')]
                selected_tasks = [config['analysis_tasks'][i] for i in selected_indices if 0 <= i < len(config['analysis_tasks'])]
                config['analysis_tasks'] = selected_tasks
                if not selected_tasks:
                    print("No valid tasks selected. Running all tasks.")
                    # Revert to all tasks if none selected
                    config['analysis_tasks'] = [task for task in config.get('analysis_tasks', [])]
            except ValueError:
                print("Invalid input for task selection. Running all tasks.")
    else:
        print("No analysis tasks found in the configuration.")
    
    return config

def main():
    """
    Main entry point for the interactive command-line interface.
    """
    config = get_user_input()
    if not config:
        return

    try:
        # Setup logging based on config
        log_cfg = config.get('logging', {})
        output_dir = config.get('global', {}).get('output_dir', 'output/')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        log_file_name = log_cfg.get('file')
        log_file_path = os.path.join(output_dir, log_file_name) if log_file_name else None

        setup_logging(log_cfg.get('level', 'INFO'), log_file_path)

        print("\n--- Starting Analysis ---")
        run_pipeline(config, gui_mode=False)
        print("--- Analysis Complete ---")

    except (ConfigError, AnalysisError) as e:
        logging.critical(f"Pipeline failed: {e}")
        print(f"Pipeline failed: {e}")
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()