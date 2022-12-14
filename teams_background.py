#!/usr/bin/python3
import requests
import openai
from datetime import datetime
import sys
from typing import Optional
from PIL import Image


opeai_api_key = 'YOUR_OPENAI_API_KEY'
background_image_path = '/Users/YOUR_USER/Library/Application Support/Microsoft/Teams/Backgrounds/Uploads/'
background_image_name = 'YOUR_CUSTOM_IMAGE_NAME'

background_original_image_name = 'original-' + background_image_name

# Generated images can have a size of 256x256, 512x512, or 1024x1024 pixels
# https://beta.openai.com/docs/guides/images/generations
opeai_max_size = '1024x1024'


def retrieve_prompt() -> Optional[str]:
    response = requests.post('https://www.aiprompt.io/prompts/')
    if response.status_code != 200:
        return None

    json = response.json()
    if 'prompt' not in json:
        return None

    return json['prompt']


def log_prompt(prompt: str):
    with open(background_image_path + 'last_ai_prompt.log', 'wb') as f:
        f.write(str.encode(prompt))


def log_error(error_msg: str):
    now = datetime.now()
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    with open(background_image_path + 'ai_error.log', 'a') as f:
        f.write(date_time + ': ' + error_msg)


def is_prompt_safe(prompt: str) -> bool:
    response = openai.Moderation.create(
        input=prompt,
        api_key=opeai_api_key
    )
    if 'results' not in response or not response["results"]:
        log_error('An error occurred during the prompt moderation')
        return False

    output = response["results"][0]
    return 'flagged' in output and not output.flagged


def retrieve_image_url(prompt: str) -> Optional[str]:
    openai.api_key = opeai_api_key
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size=opeai_max_size
    )

    if 'data' not in response or not response['data'] or 'url' not in response['data'][0]:
        return None

    return response['data'][0]['url']


def save_image(image_url: str):
    with open(background_image_path + background_original_image_name, 'wb') as f:
        f.write(requests.get(image_url).content)


def resize_and_crop_image():
    with Image.open(background_image_path + background_original_image_name) as image:
        width = image.size[0]
        height = image.size[1]

        aspect = width / float(height)

        ideal_width = 1920
        ideal_height = 1080

        ideal_aspect = ideal_width / float(ideal_height)

        if aspect > ideal_aspect:
            # Crops the left and right edges
            new_width = int(ideal_aspect * height)
            offset = (width - new_width) / 2
            resize = (int(offset), 0, int(width) - offset, height)
        else:
            # Crops the top and bottom
            new_height = int(width / ideal_aspect)
            offset = (height - new_height) / 2
            resize = (0, int(offset), width, int(height - offset))

        resized_image = image.crop(resize).resize((ideal_width, ideal_height), Image.Resampling.LANCZOS)
        resized_image.save(background_image_path + background_image_name)


def main():
    prompt = retrieve_prompt()
    log_prompt(prompt)

    if prompt is None:
        log_error('Cannot retrieve prompt')
        return

    if not is_prompt_safe(prompt):
        log_error('Image contains dangerous content')
        return

    url = retrieve_image_url(prompt)
    if url is None:
        log_error('Cannot retrieve an image from OpenAI')
        return

    save_image(url)
    resize_and_crop_image()


if __name__ == '__main__':
    sys.exit(main())
