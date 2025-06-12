import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def save_document(file_storage, patient_id):
    """Saves an uploaded document, ensuring a unique filename.
    Returns the filename under which the file was saved.
    Could be extended to save in patient-specific subdirectories.
    """
    original_filename = secure_filename(file_storage.filename)
    # Create a unique filename to avoid overwrites and for better organization
    # For example, using UUID and keeping the extension
    _ , ext = os.path.splitext(original_filename)
    # Ensure the extension, if present, starts with a dot, or handle cases with no extension
    if ext and not ext.startswith('.'):
        ext = '.' + ext
    elif not ext: # Handle files with no extension
        ext = ''

    unique_filename = str(uuid.uuid4()) + ext

    # For now, save directly in UPLOAD_FOLDER.
    # Consider patient-specific subfolders later e.g. os.path.join(current_app.config['UPLOAD_FOLDER'], str(patient_id))
    # Ensure that subfolder exists if you implement it.

    # Construct the path for saving the file
    # The UPLOAD_FOLDER is already an absolute path that includes the instance_path
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)

    # Ensure the upload directory exists (though __init__.py should have created it)
    # This is an additional safeguard, especially if patient-specific subdirs are added later
    upload_dir = os.path.dirname(save_path)
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    file_storage.save(save_path)
    return unique_filename # Return the name it's saved as on the server
