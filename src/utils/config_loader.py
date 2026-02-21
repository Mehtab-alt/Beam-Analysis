import yaml
import logging

logger = logging.getLogger(__name__)

def load_config(config_path="config.yaml"):
    """
    Loads the YAML configuration file.

    Args:
        config_path (str): The path to the configuration file.

    Returns:
        dict: The configuration settings.
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration loaded successfully from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found at {config_path}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        return None