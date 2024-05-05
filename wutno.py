import os
import sys
import time
import logging
import re
from groq import Groq

# Setup logging
logging.basicConfig(filename='game_systems_log.log', level=logging.INFO)

def initialize_client(api_key):
    try:
        return Groq(api_key=api_key)
    except Exception as e:
        logging.error(f"Initialization failed: {e}")
        raise SystemExit(e)

def read_file(filepath):
    try:
        with open(filepath, encoding='utf-8') as file:
            return file.read().strip()
    except Exception as e:
        logging.error(f"Failed to read {filepath}: {e}")
        raise

def request_api(client, input_text, model, retries=3):
    retry_delay = 2
    for _ in range(retries):
        try:
            response = client.chat.completions.create(messages=[{"role": "user", "content": input_text}], model=model)
            return response.choices[0].message.content
        except Exception as e:
            wait_time = float(re.search(r'(\d+\.\d+)s', str(e)).group(1)) if 'rate_limit_exceeded' in str(e) else retry_delay
            logging.warning(f"API limit hit, retrying in {wait_time}s.")
            time.sleep(wait_time)
    raise Exception("API request failed after maximum retries.")

def write_to_file(directory, filename, content):
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, 'w', encoding='utf-8') as file:
        file.write(content)
    logging.info(f"Written: {path}")

def refine_code(client, prompt, initial_code):
    model_order = [('Llama3-70b-8192', 2), ('Mixtral-8x7b-32768', 2), ('Llama3-70b-8192', 2), ('Llama3-70b-8192', 1), ('Mixtral-8x7b-32768', 1), ('Llama3-70b-8192', 1), ('Llama3-8b-8192', 4), ('Llama3-70b-8192', 3)]
    code = initial_code
    iteration = 0

    # Process all but the final iteration
    for model, count in model_order:
        for _ in range(count):
            code = request_api(client, f"Suggest improvements based on:\n{prompt}\nCode:\n{code}", model)
            write_to_file('game_systems_info', f'refined_code_{iteration}.txt', code)
            iteration += 1

    # Final refinement using Llama3-70b-8192
    final_model = 'Llama3-70b-8192'
    final_count = 2
    for _ in range(final_count):
        code = request_api(client, f"Suggest improvements based on:\n{prompt}\nCode:\n{code}", final_model)
        write_to_file('game_systems_info', f'refined_code_{iteration}.txt', code)
        iteration += 1

    return code

def main():
    client = initialize_client("GET YOUR OWN API KEY FROM GROQ, ITS EASY")
    input_file = sys.argv[1] if len(sys.argv) > 1 else "prompt.txt"
    prompt_content = read_file(input_file)
    initial_code = f"# Initial template based on: {prompt_content}"
    final_code = refine_code(client, prompt_content, initial_code)
    write_to_file('game_systems_info', 'final_code.txt', final_code)
    logging.info("Refinement process completed.")

if __name__ == "__main__":
    main()
