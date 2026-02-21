import pandas as pd
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

def _get_html_template(config, results_summary, plot_paths, results_df_html):
    """Generates the full HTML content for the report with inline CSS."""
    
    # --- Inline CSS ---
    css_style = """
    body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; color: #333; }
    .container { max-width: 1000px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 0 15px rgba(0,0,0,0.1); }
    h1, h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    h1 { text-align: center; }
    .section { margin-bottom: 30px; }
    pre { background: #eee; padding: 15px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; }
    table { border-collapse: collapse; width: 100%; margin-top: 20px; }
    th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
    th { background-color: #3498db; color: white; }
    tr:nth-child(even) { background-color: #f2f2f2; }
    .plot-image { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; margin-top: 10px; }
    .footer { text-align: center; margin-top: 40px; font-size: 0.8em; color: #777; }
    """

    # --- Config Sections ---
    beam_props_html = "<ul>" + "".join([f"<li><b>{k.replace('_', ' ').title()}:</b> {v}</li>" for k, v in config.get('beam_properties', {}).items()]) + "</ul>"
    
    supports_html = "<ul>" + "".join([f"<li><b>{s['type'].title()} Support</b> at position {s['position']} m</li>" for s in config.get('supports', [])]) + "</ul>"
    
    loads_html = "<ul>"
    for load in config.get('loads', []):
        if load['type'] == 'point':
            loads_html += f"<li><b>Point Load:</b> {load['magnitude']} N at {load['position']} m</li>"
        elif load['type'] == 'distributed':
            loads_html += f"<li><b>Distributed Load:</b> {load['magnitude']} N/m from {load['start']} m to {load['end']} m</li>"
    loads_html += "</ul>"

    # --- Plots Section ---
    plots_html = ""
    for title, path in plot_paths.items():
        plots_html += f"<h3>{title}</h3><img src='{os.path.basename(path)}' alt='{title}' class='plot-image'>"

    # --- Main Template ---
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{config.get('project_name', 'Beam Analysis Report')}</title>
        <style>{css_style}</style>
    </head>
    <body>
        <div class="container">
            <h1>{config.get('project_name', 'Beam Analysis Report')}</h1>
            <p class="footer">Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

            <div class="section">
                <h2>Input Parameters</h2>
                <h3>Beam Properties</h3>
                {beam_props_html}
                <h3>Supports</h3>
                {supports_html}
                <h3>Loads</h3>
                {loads_html}
            </div>

            <div class="section">
                <h2>Analysis Plots</h2>
                {plots_html}
            </div>

            <div class="section">
                <h2>Key Results</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Maximum Shear Force</td><td>{results_summary['max_shear']:.2f} N</td></tr>
                    <tr><td>Minimum Shear Force</td><td>{results_summary['min_shear']:.2f} N</td></tr>
                    <tr><td>Maximum Bending Moment</td><td>{results_summary['max_moment']:.2f} Nm</td></tr>
                    <tr><td>Minimum Bending Moment</td><td>{results_summary['min_moment']:.2f} Nm</td></tr>
                    <tr><td>Maximum Deflection</td><td>{results_summary['max_deflection'] * 1000:.3f} mm</td></tr>
                </table>
            </div>

            <div class="section">
                <h2>Full Results Data (Sample)</h2>
                {results_df_html}
            </div>
            
            <p class="footer">End of Report</p>
        </div>
    </body>
    </html>
    """
    return html

def save_html_report(config, results_df, plot_paths, output_path):
    """
    Generates a comprehensive HTML report of the analysis.
    
    Args:
        config (dict): The input configuration dictionary.
        results_df (pd.DataFrame): The analysis results.
        plot_paths (dict): A dictionary of plot titles to their file paths.
        output_path (str): The path to save the HTML report.
    """
    logger.info(f"Generating HTML report at {output_path}")
    try:
        # 1. Summarize key results
        results_summary = {
            'max_shear': results_df['Shear_Force_N'].max(),
            'min_shear': results_df['Shear_Force_N'].min(),
            'max_moment': results_df['Bending_Moment_Nm'].max(),
            'min_moment': results_df['Bending_Moment_Nm'].min(),
            'max_deflection': results_df['Deflection_m'].max() if results_df['Deflection_m'].max() > abs(results_df['Deflection_m'].min()) else results_df['Deflection_m'].min()
        }

        # 2. Format a sample of the DataFrame for the HTML table
        results_df_sample = results_df.iloc[::max(1, len(results_df)//20)].round(4)
        results_df_html = results_df_sample.to_html(index=False, classes='results-table')

        # 3. Get the full HTML content
        html_content = _get_html_template(config, results_summary, plot_paths, results_df_html)

        # 4. Write to file
        with open(output_path, 'w') as f:
            f.write(html_content)
        logger.info(f"HTML report saved successfully to {output_path}")

    except Exception as e:
        logger.error(f"Failed to generate HTML report: {e}", exc_info=True)


def save_output(df, output_path):
    """
    Saves a DataFrame to a file, choosing the format based on the extension.
    Now primarily used for simple CSV saving.
    """
    if not isinstance(df, pd.DataFrame):
        logger.error("Input data for report is not a valid pandas DataFrame. Cannot save.")
        return
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"CSV data saved successfully to {output_path}")
    except Exception as e:
        logger.error(f"Error saving CSV to {output_path}: {e}", exc_info=True)