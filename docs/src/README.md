# GPT4 Vision Web Crawling

This is a GPT4 Vision API and Puppeteer powered tool that can answer questions based on website screenshots. You ask it a question and it will browse to a website and take a screenshot. Then it will use GPT4 Vision API to answer the question based on the screenshot.

## JavaScript version

The JavaScript version (`vision_crawl.js`) is able to not only open a URL directly, but it can also click on links on pages.

```shell
$ npm install
$ node vision_crawl.js
```

## Python version

The Python version (`vision_crawl.py`) is the original version, that only opens one URL at a time directly. The Python version uses JavaScript too, for the Puppeteer part.

```shell
$ npm install
$ pip install -r requirements.txt
$ python3 vision_crawl.py
```

## Examples

You can ask stuff like this, for example:

- "What is the weather like in California?"
- "What are the latest news in the world?"
- "What is the current stock price of Tesla?"
- "How many subscribers does Unconventional Coding have on YouTube?"
