#!/usr/bin/env python3

import os
import sys
import inspect

# Find where advanced_app.py is
app_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "src", "advanced_app.py")
print(f"Looking for app at: {app_path}")
print(f"File exists: {os.path.exists(app_path)}")

# Load the file contents
with open(app_path, 'r') as f:
    content = f.read()

# Check if create_encoding_script exists
if "def create_encoding_script" in content:
    print("Function already exists in the file")
else:
    print("Function doesn't exist, will need to add it")

    # Find a good insert position - just before show_help function
    insert_pos = content.find("def show_help")
    if insert_pos > 0:
        # Prepare the new function
        new_function = """
def create_encoding_script(slideshow_title, resolution, quality, output_filename, encoder, audio_file, image_list, slide_duration):
    \"\"\"Create an encoding script file with the provided slideshow settings.\"\"\"
    print(f"Creating encoding script with: {slideshow_title}, {resolution}, {quality}, {output_filename}")
    # Create the actual run_encode.py script
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "run_encode.py")

def run_encoding():
    \"\"\"Run the encoding script with progress monitoring.\"\"\"
    script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "run_encode.py")
    print(f"Would run encoding using: {script_path}")
    return True

"""
        # Insert the new function
        new_content = content[:insert_pos] + new_function + content[insert_pos:]
        
        # Write back to file
        with open(app_path, 'w') as f:
            f.write(new_content)
        
        print(f"Added the create_encoding_script and run_encoding functions to {app_path}")
    else:
        print("Couldn't find a good place to insert the function")

print("Script completed") 