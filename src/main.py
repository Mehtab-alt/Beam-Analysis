import logging
import os
import pandas as pd

from .utils.config_loader import load_config
from .utils.exceptions import ConfigError, AnalysisError
from .civil.beam_analysis import solve_beam
from .visualization.plotter import plot_line_chart
from .reporting.reporter import save_output, save_html_report

logger = logging.getLogger(__name__)

def run_pipeline(config, gui_mode=False):
    """
    Runs the civil engineering analysis pipeline based on the config.
    """
    logger.info("Starting beam analysis pipeline...")
    
    properties = config.get('beam_properties')
    supports = config.get('supports')
    loads = config.get('loads')
    tasks = config.get('analysis_tasks', [])
    output_dir = config.get('global', {}).get('output_dir', 'output/')

    # --- FIX: Ensure the output directory exists ---
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            logger.info(f"Created output directory at: {output_dir}")
        except OSError as e:
            logger.error(f"Failed to create output directory {output_dir}: {e}")
            raise AnalysisError(f"Could not create output directory: {e}")

    if not all([properties, supports, loads, tasks]):
        raise ConfigError("Config is missing one or more of: 'beam_properties', 'supports', 'loads', 'analysis_tasks'.")

    # 1. Core Analysis: Solve the beam problem
    try:
        results_df = solve_beam(properties, supports, loads)
        logger.info("Beam analysis solver finished successfully.")
    except Exception as e:
        logger.error(f"An error occurred during beam analysis: {e}", exc_info=True)
        raise AnalysisError(f"Beam solver failed: {e}")
    
    # --- Prepare for GUI and Reporting ---
    gui_results = {}
    if gui_mode:
        gui_results['beam_results_df'] = {'type': 'dataframe', 'data': results_df, 'name': 'Beam Analysis Results', 'config': config}

    generated_plot_paths = {}

    # 2. Execute Output Tasks (Plotting, Saving, Reporting)
    for i, task in enumerate(tasks):
        task_name = task.get('name', f"Task {i+1}")
        task_type = task.get('type')
        output_file = task.get('output')
        
        if not all([task_type, output_file]):
            logger.warning(f"Skipping task '{task_name}' because 'type' or 'output' is missing.")
            continue
            
        output_path = os.path.join(output_dir, output_file)
        logger.info(f"--- Running Task: '{task_name}' ({task_type}) ---")

        if task_type == 'plot':
            params = task.get('params', {})
            try:
                plot_line_chart(
                    df=results_df,
                    x_col='Position_m',
                    y_col=params['y_col'],
                    title=params.get('title', 'Beam Diagram'),
                    xlabel='Position along beam (m)',
                    ylabel=params.get('ylabel', 'Value'),
                    output_path=output_path
                )
                generated_plot_paths[params.get('title', task_name)] = output_path
                if gui_mode:
                    plot_key = f"{task_name}_plot"
                    gui_results[plot_key] = {'type': 'plot', 'data': results_df, 'params': params, 'name': task_name, 'config': config}
            except KeyError as e:
                logger.error(f"Plotting task '{task_name}' failed. Column not found: {e}")
            except Exception as e:
                logger.error(f"Plotting task '{task_name}' failed: {e}", exc_info=True)

        elif task_type == 'save_csv':
            save_output(results_df, output_path)

        elif task_type == 'save_html_report':
            save_html_report(config, results_df, generated_plot_paths, output_path)

    logger.info("--- Beam analysis pipeline finished ---")
    return gui_results if gui_mode else None