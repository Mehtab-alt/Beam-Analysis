import pandas as pd
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend for thread safety
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)

def plot_line_chart(df, x_col, y_col, title, xlabel, ylabel, output_path=None):
    """
    Creates and saves a line chart from a DataFrame. Ideal for SFD, BMD, etc.

    Args:
        df (pd.DataFrame): DataFrame containing the data to plot.
        x_col (str): The column name for the x-axis.
        y_col (str): The column name for the y-axis.
        title (str): The title of the plot.
        xlabel (str): The label for the x-axis.
        ylabel (str): The label for the y-axis.
        output_path (str, optional): Path to save the plot. If None, not saved.
    """
    if not isinstance(df, pd.DataFrame):
        logger.error("Input data for plotting is not a valid pandas DataFrame.")
        return
    
    if y_col not in df.columns:
        logger.error(f"Column '{y_col}' for plotting not found in DataFrame. Available: {df.columns.tolist()}")
        return

    logger.info(f"Generating line chart: '{title}' and saving to {output_path}")

    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df[x_col], df[y_col], color='b', label=y_col)
    ax.fill_between(df[x_col], df[y_col], 0, color='skyblue', alpha=0.4) # Fill to zero axis
    ax.axhline(0, color='black', linewidth=0.8) # Emphasize zero axis
    
    ax.set_title(title, fontsize=16, weight='bold')
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, which='both', linestyle='--', alpha=0.7)
    # ax.legend() # Often not needed for SFD/BMD
    fig.tight_layout()

    if output_path:
        try:
            fig.savefig(output_path)
            logger.info(f"Plot saved successfully to {output_path}")
        except Exception as e:
            logger.error(f"Error saving plot to {output_path}: {e}", exc_info=True)
    
    plt.close(fig)

# Kept for potential future use, but not part of the core beam analysis.
def plot_bar_chart(df, x_col, y_col, title, xlabel, ylabel, output_path=None):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df[x_col], df[y_col], color='skyblue')
    ax.set_title(title, fontsize=16, weight='bold')
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    fig.tight_layout()
    if output_path: fig.savefig(output_path)
    plt.close(fig)