import json
import openai
import srt
import os
import tiktoken

# Limit for the maximum tokens per API call
MAX_TOKENS_PER_CALL = 3000

# Translate each subtitle
translated_subtitles = []

# to split subs
splitter = '++++'

ai_model = 'gpt-3.5-turbo'

encoding = tiktoken.encoding_for_model(ai_model)

current_tokens = 0
current_subtitles = []
user_message = ""  # Initialize an empty user message


def count_tokens(text):
    return len(encoding.encode(text))


def make_dirs(input_folder, output_folder):
    # Create the input folder if it doesn't exist
    os.makedirs(input_folder, exist_ok=True)
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)


def parse_subs(input_file):
    # Read the input .srt file
    with open(input_file, 'r', encoding='utf-8') as file:
        return list(srt.parse(file.read()))


def append_subs(text):
    # Format the text with '++++' separators
    formatted_text = text + '\n++++\n'
    # Return the original text
    return text


def is_too_long():
    return current_tokens + count_tokens(user_message) > MAX_TOKENS_PER_CALL


def reset_count():
    global user_message
    global current_tokens
    user_message = ''
    current_tokens = 0


# Define a function to translate a single subtitle file using GPT-3.5 Turbo with 4K context
def translate(input_file, output_folder, target_lang, api_key):
    # Initialize the OpenAI API client with the "gpt-3.5-turbo" engine
    openai.api_key = api_key

    subtitles = parse_subs(input_file)

    for subtitle in subtitles:

        append_subs(subtitle.content)

        if is_too_long():
            translate_block()
            reset_count()

        # Check if adding the subtitle to the current user message exceeds the token limit
        if current_tokens + count_tokens(subtitle_text) < MAX_TOKENS_PER_CALL:
            # Add the subtitle to the current user message
            user_message += subtitle_text + '\n'
            current_tokens += count_tokens(subtitle_text)
        else:
            # Translate the current user message
            translate_and_save_segment(user_message.strip(), current_subtitles, input_file, output_folder, target_lang)

            # Reset the current user message and tokens for the next segment
            user_message = subtitle_text + '\n'
            current_subtitles = [subtitle]
            current_tokens = count_tokens(subtitle_text)

    if current_subtitles:
        # Translate the remaining subtitles in the last segment
        translate_and_save_segment(user_message.strip(), current_subtitles, input_file, output_folder, target_lang)


def translate_and_save_segment(user_message, subtitles, input_file, output_folder, target_lang):
    # Construct a user message batch with the system message
    system_messages = [{'role': 'system', 'content': f'You are a subtitle translator and you need to translate '
                                                     f'the following subtitles into "{target_lang}" language.'}]
    user_message = [{'role': 'user', 'content': user_message}]
    message = system_messages + user_message

    completion = openai.ChatCompletion.create(
        model=ai_model,
        messages=message
    )

    response = completion.choices[0].message.content

    try:
        response = json.loads(response)['choices'][0]['message']['content']
    except:
        print("[] Things went badly!, check results!")
        pass

    translated_text = response.strip()

    # Split the translated text into individual subtitles
    translated_subtitles = translated_text.split('\n')

    for idx, subtitle in enumerate(subtitles):
        if idx < len(translated_subtitles):
            subtitle.content = translated_subtitles[idx]

    # Construct the output file path
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_folder, f"{base_name}_{target_lang.upper()}.srt")

    # Write the translated subtitles to the output .srt file
    with open(output_file, 'a', encoding='utf-8') as file:
        file.write(srt.compose(subtitles))
