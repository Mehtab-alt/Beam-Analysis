"""
Custom exception classes for the application.
"""

class DataAnalysisError(Exception):
    """Base exception class for this application."""
    pass

class ConfigError(DataAnalysisError):
    """Exception raised for errors in the configuration file."""
    pass

class DataLoadingError(DataAnalysisError):
    """Exception raised for errors during data loading."""
    pass

class AnalysisError(DataAnalysisError):
    """Exception raised for errors during an analysis task."""
    pass