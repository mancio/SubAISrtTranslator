import json
import os
import sys
import openai
import srt

# Set up your OpenAI API key
api_key = sys.argv[1]

input_folder = "input"  # Folder containing the input .srt files
output_folder = "output"  # Folder to save translated .srt files
target_lang = "english"  # Target language code (e.g., "fr" for French)
movie_name = "Fantozzi"


def make_dirs():
    # Create the input folder if it doesn't exist
    os.makedirs(input_folder, exist_ok=True)
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)


# Define a function to translate a single subtitle file using GPT-3.5 Turbo with 4K context
def translate_single_srt(input_file):
    # Initialize the OpenAI API client with the "gpt-3.5-turbo" engine
    openai.api_key = api_key

    # Read the input .srt file
    with open(input_file, 'r', encoding='utf-8') as file:
        subtitles = list(srt.parse(file.read()))

    # Translate each subtitle
    translated_subtitles = []
    for subtitle in subtitles:
        # # Translate the subtitle text using GPT-3.5 Turbo with 4K context
        # translation = openai.Completion.create(
        #     engine="davinci",
        #     prompt=f"Translate the following subtitle line in {target_lang}:\n{subtitle.content}",
        #     max_tokens=50  # Adjust the max_tokens as needed for longer subtitles
        # )
        #
        # translated_text = translation.choices[0].text.strip()
        # subtitle.content = translated_text
        # translated_subtitles.append(subtitle)

        # Translate the subtitle text to English using OpenAI API
        messages = [
            {'role': 'system', 'content': f'translate this text to "{target_lang}"'},
            {'role': 'user', 'content': subtitle.content}
        ]
        completion = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages
        )
        result = completion.choices[0].message.content

        try:
            result = json.loads(result)['choices'][0]['message']['content']
        except:
            print("[] Things went badly!, check results!")
            pass

        translated_text = result.strip()
        return translated_text

    # Construct the output file path
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_folder, f"{base_name}_{target_lang.upper()}.srt")

    # Write the translated subtitles to the output .srt file
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(srt.compose(translated_subtitles))


if __name__ == "__main__":
    make_dirs()

    # Assuming you have only one .srt file in the input folder
    input_files = [f for f in os.listdir(input_folder) if f.endswith('.srt')]
    if len(input_files) == 1:
        input_file = os.path.join(input_folder, input_files[0])
        translate_single_srt(input_file)
        print("Subtitles translated and saved to the", output_folder, "folder.")
    else:
        print("Please ensure there is exactly one .srt file in the input folder.")
