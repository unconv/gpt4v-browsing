"""
Using syncronous Playwright for visual crawl
"""
import base64
from io import BytesIO
import json
from PIL import Image

from dotenv import load_dotenv
from openai import OpenAI
from playwright.sync_api import sync_playwright


class URLNotIdentifiedException(Exception):
    """Exception raised when a URL cannot be identified."""


class LinkNotIdentifiedException(Exception):
    """Exception raised when a LINK cannot be identified."""


WELCOME_MESSAGE = """
###########################################
# GPT4V-Browsing by Unconventional Coding #
###########################################

GPT: How can I assist you today?
"""

SYSTEM_MESSAGE = """
You are a website crawler. You will be given instructions on what to do by
browsing. You are connected to a web browser and you will be given the
screenshot of the website you are on. The links on the website will be
highlighted in red in the screenshot. Always read what is in the screenshot.
Don't guess link names.

You can go to a specific URL by answering with the following JSON format:
{"url": "url goes here"}

You can click links on the website by referencing the text inside of the
link/button, by answering in the following JSON format: {"click": "Text in
link"}. Use a unique part of the website link text in the link, do no makeup you own or inference.

Once you are on a URL and you have found the answer to the user's question, you
can answer with a regular message.

In the beginning, go to a direct URL that you think might contain the answer to
the user's question. Prefer to go directly to sub-urls like
'https://google.com/search?q=search' if applicable. Prefer to use Google for
simple queries. If the user provides a direct URL, go to that one.
"""

VISION_HELPER_MESSAGE = """
Here\'s the screenshot of the website you are on right now. You can click on
links with {"click": "Link text"} or you can crawl to another URL if this one is
incorrect. Please take care, links are very important, so always use a unique
part of the website link text in the link, do no makeup you own or inference. If
you find the answer to the user\'s question, you can respond normally."""

MESSAGES = [{"role": "system", "content": SYSTEM_MESSAGE}]


if __name__ == "__main__":
    load_dotenv()

    model = OpenAI()
    model.timeout = 10

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()

        # Get all new pages (including popups) in the context
        def handle_page(page):
            page.wait_for_load_state()
            print(page.title())

        context.on("page", handle_page)

        page = context.new_page()
        # page.goto(url, wait_until="networkidle")
        page.set_viewport_size({"width": 1024, "height": 768})

        print(WELCOME_MESSAGE)

        prompt = input("You: ")

        MESSAGES.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        URL = "https://bbc.com/news"
        SCREENSHOT_BASE_64 = None
        QUALITY = 42

        while True:
            if URL:
                print("Crawling " + URL)
                page.goto(URL, wait_until="networkidle")

                # Update all links to have a 1px solid red border
                page.evaluate(
                    """() => {
                    const links = document.querySelectorAll('a');
                    links.forEach(link => {
                        link.style.border = '1px solid red';
                    });
                }"""
                )
                screenshot_bytes = page.screenshot(
                    full_page=True, type="jpeg", quality=QUALITY
                )

                # Compress the image further using Pillow
                img = Image.open(BytesIO(screenshot_bytes))
                # Convert to black and white
                bw_img = img.convert("L")
                img_buffer = BytesIO()
                bw_img.save(img_buffer, format="JPEG", quality=QUALITY)
                compressed_bytes = img_buffer.getvalue()

                # Save the same image directly to disk
                bw_img.save("screenshot.jpg", "JPEG", quality=QUALITY)
                SCREENSHOT_BASE_64 = base64.b64encode(compressed_bytes).decode("utf-8")
                URL = None

            if SCREENSHOT_BASE_64:
                MESSAGES.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": f"data:image/jpeg;base64,${SCREENSHOT_BASE_64}",
                            },
                            {
                                "type": "text",
                                "text": VISION_HELPER_MESSAGE,
                            },
                        ],
                    }
                )

                SCREENSHOT_BASE_64 = None
                continue

            print("Calling LLM ...")
            LLM_RESPONSE = model.chat.completions.create(
                model="gpt-4-vision-preview",
                max_tokens=1024,
                messages=MESSAGES,
            )
            print("LLM Call Complete.")

            message = LLM_RESPONSE.choices[0].message
            message_text = message.content

            if '{"url":' in message_text:
                URL = json.loads(message_text)["url"]
                MESSAGES.append(
                    {
                        "role": "assistant",
                        "content": URL,
                    }
                )
                continue

            if '{"click":' in message_text:
                try:
                    click_text = json.loads(message_text)["click"]
                    MESSAGES.append(
                        {
                            "role": "assistant",
                            "content": click_text,
                        }
                    )

                    # link = page.get_by_text(click_text)
                    # link.click(timeout=30000)
                    page.get_by_role("link >> visible=true").get_by_text(
                        click_text
                    ).first.click(force=True)

                    # Update all links to have a 1px solid red border
                    page.evaluate(
                        """() => {
                        const links = document.querySelectorAll('a');
                        links.forEach(link => {
                            link.style.border = '1px solid red';
                        });
                    }"""
                    )
                    QUALITY = 42
                    screenshot_bytes = page.screenshot(
                        full_page=True, type="jpeg", quality=QUALITY
                    )

                    # Compress the image further using Pillow
                    img = Image.open(BytesIO(screenshot_bytes))
                    # Convert to black and white
                    bw_img = img.convert("L")
                    img_buffer = BytesIO()
                    bw_img.save(img_buffer, format="JPEG", quality=QUALITY)
                    compressed_bytes = img_buffer.getvalue()

                    # Save the same image directly to disk
                    bw_img.save("screenshot.jpg", "JPEG", quality=QUALITY)
                    SCREENSHOT_BASE_64 = base64.b64encode(compressed_bytes).decode(
                        "utf-8"
                    )
                    continue

                # pylint: disable=broad-exception-caught
                except Exception as err:
                    print(f"ERROR: Clicking failed [{err}]")

                    MESSAGES.append(
                        {
                            "role": "user",
                            "content": "ERROR: I was unable to click that element",
                        }
                    )
                    SCREENSHOT_BASE_64 = None
                    continue

            MESSAGES.append(
                {
                    "role": "assistant",
                    "content": message_text,
                }
            )
            print("GPT: " + message_text)

            prompt = input("You: ")

            MESSAGES.append(
                {
                    "role": "user",
                    "content": prompt,
                }
            )
