import argparse
import logging
import os

from src.main import run_pipeline
from src.utils.config_loader import load_config
from src.utils.logging_config import setup_logging
from src.utils.exceptions import AnalysisError, ConfigError

def main():
    """
    Main entry point for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="A command-line tool for civil engineering beam analysis.")
    parser.add_argument(
        '--config', type=str, default='config.yaml', help='Path to the configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--output-dir', type=str, help='Path to the output directory (overrides config file setting)'
    )
    parser.add_argument(
        '--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level (overrides config file setting)'
    )
    parser.add_argument(
        '--tasks', nargs='+', help='Specify which analysis tasks to run by name (e.g., "Shear Force Diagram")'
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        if not config:
            # load_config logs the error, so we can just exit
            return

        # Override config settings with command-line arguments if provided
        if args.output_dir:
            config['global']['output_dir'] = args.output_dir
        if args.log_level:
            config['logging']['level'] = args.log_level
        if args.tasks:
            # Filter tasks based on provided names
            filtered_tasks = [task for task in config.get('analysis_tasks', []) if task.get('name') in args.tasks]
            config['analysis_tasks'] = filtered_tasks

        # Setup logging based on config file or command-line argument
        log_cfg = config.get('logging', {})
        output_dir = config.get('global', {}).get('output_dir', 'output/')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        log_file_name = log_cfg.get('file')
        log_file_path = os.path.join(output_dir, log_file_name) if log_file_name else None

        setup_logging(log_cfg.get('level', 'INFO'), log_file_path)

        run_pipeline(config, gui_mode=False)

    except (ConfigError, AnalysisError) as e:
        logging.critical(f"Pipeline failed: {e}")
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()