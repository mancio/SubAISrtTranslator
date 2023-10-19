import concurrent.futures
import re
import time
import random

import openai
import srt
import os

# ai_model = 'gpt-4'
ai_model = 'gpt-3.5-turbo'
# ai_model = 'gpt-3.5-turbo-0301'

subtitles = []


def make_dirs(input_folder, output_folder):
    # Create the input folder if it doesn't exist
    os.makedirs(input_folder, exist_ok=True)
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)


def clean_string(text):
    # Define a regular expression pattern to match non-standard tags or formats
    non_standard_pattern = re.compile(r'<[^>]*>')

    # Remove non-standard tags from the input string
    cleaned_string = non_standard_pattern.sub('', text)

    return cleaned_string


def parse_subs(input_file):
    # Read the input .srt file
    with open(input_file, 'r', encoding='utf-8') as file:
        return list(srt.parse(file.read()))


def prepare_path(input_file, output_folder, target_lang):
    # Construct the output file path
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    return os.path.join(output_folder, f"{base_name}_{target_lang.upper()}.srt")


def save_output(output_file, subs):
    # Write the translated subtitles to the output .srt file
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(srt.compose(subs))


def run_model(message):
    return openai.ChatCompletion.create(
        model=ai_model,
        messages=message,
        temperature=0,
        max_tokens=50,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )


def translate_subtitle(user_message, input_language, target_language):
    system_role = [{'role': 'system', 'content': f'Please translate every subtitle I will send you '
                                                 f'from {input_language} to {target_language}. '
                                                 f'Do not be creative. Just repeat the same text in case '
                                                 f'you cannot translate. Translate offensive words.'}]
    user_role = [{'role': 'user', 'content': user_message}]

    message = system_role + user_role

    time.sleep(random.uniform(0.1, 0.3))

    attempts = 4

    for _ in range(attempts):
        try:
            completion = run_model(message)
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"An error occurred: {e}")
            if attempts > 0:
                print("Retrying...")
                time.sleep(1)
            else:
                return "missing translation"


def translate_concurrent(index, subtitle, input_language, target_lang):
    translated_subtitle = translate_subtitle(clean_string(subtitle.content), input_language, target_lang)
    print("sub number: " + str(index) + " translated")
    return index, translated_subtitle


# Define a function to translate a single subtitle file using GPT-3.5 Turbo with 4K context
def translate(input_file, output_folder, input_language, target_lang, api_key):
    openai.api_key = api_key

    global subtitles
    subtitles = parse_subs(input_file)

    max_threads = 10

    # Create a ThreadPoolExecutor with the specified maximum number of threads
    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        # Submit translation tasks for each subtitle
        translation_tasks = [executor.submit(translate_concurrent, index, subtitle, input_language, target_lang)
                             for index, subtitle
                             in enumerate(subtitles)]

        # Wait for all tasks to complete and collect the results
        for future in concurrent.futures.as_completed(translation_tasks):
            index, translated_subtitle = future.result()
            subtitles[index].content = translated_subtitle

    output_file = prepare_path(input_file, output_folder, target_lang)

    save_output(output_file, subtitles)
