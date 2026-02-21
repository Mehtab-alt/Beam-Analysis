import logging

logger = logging.getLogger(__name__)

def validate_tasks(tasks):
    """
    Validates the structure of the analysis tasks from the config.

    Args:
        tasks (list): A list of task dictionaries from the config file.

    Returns:
        list: A list of valid tasks.
    """
    if not isinstance(tasks, list):
        logger.error("'analysis_tasks' should be a list in the config file.")
        return []

    valid_tasks = []
    required_keys = ['name', 'type', 'params', 'output']

    for i, task in enumerate(tasks):
        task_name = task.get('name', f'task_{i+1}')
        missing_keys = [key for key in required_keys if key not in task]

        if missing_keys:
            logger.error(
                f"Task '{task_name}' is missing required keys: {missing_keys}. Skipping."
            )
            continue
        
        valid_tasks.append(task)
    
    return valid_tasks