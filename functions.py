import concurrent.futures
import time
import re
import openai
import srt
import os
import tiktoken

# Limit for the maximum tokens per API call
MAX_TOKENS_PER_CALL = 3500

# Translate each subtitle
translated_subtitles = []

# to split subs
splitter = '\n\n'

ai_model = 'gpt-4'

encoding = tiktoken.encoding_for_model(ai_model)

current_tokens = 0
# user_message = ""  # Initialize an empty user message
translated_text = ""
italian_text = ""


# def count_tokens(text):
#     return len(encoding.encode(text))


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


# def append_subs(text):
#     global user_message
#     user_message += splitter + text


# def split_text_to_array():
#     # Split the input text using the delimiter
#     text_list = translated_text.split(splitter)
#
#     return [text.strip() for text in text_list]


# def text_is_too_long():
#     global current_tokens
#     current_tokens += count_tokens(user_message)
#     return current_tokens > MAX_TOKENS_PER_CALL


# def reset_count():
#     global user_message
#     global current_tokens
#     user_message = ""
#     current_tokens = 0


def prepare_path(input_file, output_folder, target_lang):
    # Construct the output file path
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    return os.path.join(output_folder, f"{base_name}_{target_lang.upper()}.srt")


def save_output(output_file, subtitles):
    # Write the translated subtitles to the output .srt file
    with open(output_file, 'a', encoding='utf-8') as file:
        file.write(srt.compose(subtitles))


def run_model(message):
    return openai.ChatCompletion.create(
        model=ai_model,
        messages=message,
        temperature=0,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )


def translate_subtitle(user_message, input_language, target_lang):
    system_role = [{'role': 'system', 'content': f'Translate the following subtitle from "{input_language}" to '
                                                 f'"{target_lang}":'}]
    user_role = [{'role': 'user', 'content': user_message}]

    # global translated_text
    #
    # if not translated_text:
    message = system_role + user_role
    # else:
    #     message = user_role

    # if translated_text:
    # time.sleep(1)

    completion = run_model(message)

    return completion.choices[0].message.content.strip()

    # global italian_text
    # italian_text += user_message


def translate_concurrent(subtitle, input_language, target_lang):
    subtitle.content = translate_subtitle(clean_string(subtitle.content), input_language, target_lang)


# Define a function to translate a single subtitle file using GPT-3.5 Turbo with 4K context
def translate(input_file, output_folder, input_language, target_lang, api_key):
    # Initialize the OpenAI API client with the "gpt-3.5-turbo" engine
    openai.api_key = api_key

    subtitles = parse_subs(input_file)

    # for subtitle in subtitles:
    #     subtitle.content = translate_subtitle(subtitle.content, input_language, target_lang)
    #     print("translated Sub number: " + str(subtitle.index) + " on total of " + str(len(subtitles)))

    # Specify the maximum number of threads (adjust as needed)
    max_threads = 1

    # Create a ThreadPoolExecutor with the specified maximum number of threads
    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        # Submit translation tasks for each subtitle
        translation_tasks = [executor.submit(translate_concurrent, subtitle, input_language, target_lang) for subtitle
                             in subtitles]

        # Wait for all tasks to complete
        concurrent.futures.wait(translation_tasks)

        # append_subs(clean_string(subtitle.content))

    #     if text_is_too_long():
    #         translate_block(input_language, target_lang)
    #         reset_count()
    #
    # if user_message:
    #     translate_block(input_language, target_lang)

    # text_list = split_text_to_array()
    #
    # for idx, subtitle in enumerate(subtitles):
    #     subtitle.content = text_list[idx]

    output_file = prepare_path(input_file, output_folder, target_lang)

    save_output(output_file, subtitles)
