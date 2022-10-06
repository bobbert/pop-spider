import os

def create_filepath(filepath):
    """Create nested directory path"""
    if os.path.exists(filepath):
        return True
    else:
        try:
            os.makedirs(filepath)
            return True
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

def remove_files_recursively(filepath):
    """Removes all files recursively in folder, while keeping folders intact"""
    for root, dirs, files in os.walk(filepath):
        for f in files:
            os.unlink(os.path.join(root, f))
