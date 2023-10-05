import sys
import os
from functions import make_dirs, translate

# Get the OpenAI API key from command line arguments
api_key = sys.argv[1]

input_folder = "input"  # Folder containing the input .srt files
output_folder = "output"  # Folder to save translated .srt files
input_language = "Italian"
target_lang = "Polish"  # Target language code (e.g., "fr" for French)

if __name__ == "__main__":

    make_dirs(input_folder, output_folder)

    # Assuming you have only one .srt file in the input folder
    input_files = [f for f in os.listdir(input_folder) if f.endswith('.srt')]
    input_file = os.path.join(input_folder, input_files[0])

    translate(input_file, output_folder, input_language, target_lang, api_key)

    print("Subtitles translated and saved to the", output_folder, "folder.")


