import logging
from typing import Literal

import httpx

# Set up logging
logger = logging.getLogger(__name__)


def fetch_content(
    url,
    return_format: Literal["text", "markdown", "html", "screenshot"] = "markdown",
    disable_gfm: Literal[False, True, "table"] = False,
    bypass_cache=False,
    with_generated_alt=False,
    remove_images=False,
    timeout=None,
    json_response=True,
    with_links_summary=False,
    with_images_summary=False,
):
    """
    Fetch content from a specified URL using the r.jina.ai API.

    :param url: The URL to fetch content from.
    :param return_format: The format of the returned content, options are 'text', 'markdown', 'html', 'screenshot'.
    :param json_response: Boolean flag to toggle JSON response format.
    :param bypass_cache: Boolean flag to bypass cache.
    :param disable_gfm: Boolean flag to disable Github Flavored Markdown or 'table' mode.
    :param remove_images: Boolean flag to remove all images from the response.
    :param timeout: Timeout in seconds for waiting the webpage to load.
    :param with_generated_alt: Boolean flag to include generated alt text for images.
    :param with_links_summary: Boolean flag to include a summary of all links at the end.
    :param with_images_summary: Boolean flag to include a summary of all images at the end.
    :return: The fetched content in the specified format.
    """
    api_url = f"https://r.jina.ai/{url}"
    headers = {"X-Return-Format": return_format}

    if bypass_cache:
        headers["X-No-Cache"] = "true"

    if remove_images:
        headers["X-Retain-Images"] = "none"

    if disable_gfm is not False:
        headers["X-No-Gfm"] = "true" if disable_gfm == True else "table"

    if timeout is not None:
        headers["X-Timeout"] = str(timeout)

    if with_generated_alt:
        headers["X-With-Generated-Alt"] = "true"

    if with_links_summary:
        headers["X-With-Links-Summary"] = "true"

    if with_images_summary:
        headers["X-With-Images-Summary"] = "true"

    if json_response:
        headers["Accept"] = "application/json"

    try:
        response = httpx.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        content = response.text
        logger.info(
            f"Successfully fetched content from: {url} in {return_format} format"
        )
    except httpx.RequestError as e:
        content = f"error: {str(e)}"
        logger.error(f"Failed to fetch content from {url}. Error: {str(e)}")
    return content


# Example usage:
if __name__ == "__main__":

    from cicada.core.utils import setup_logging

    setup_logging()

    url = "https://thgilkao.github.io/picx-images-hosting/IMG_20230913_211233.jpg"  # @param {type:"string"}
    content_format = "markdown"  # @param ["text", "markdown", "html", "screenshot"]
    json_response = False  # @param {type:"boolean"}
    bypass_cache = False  # @param {type:"boolean"}
    disable_gfm = True  # @param {type:"boolean"}
    remove_images = False  # @param {type:"boolean"}
    timeout = 60  # @param {type:"integer"}
    with_generated_alt = True  # @param {type:"boolean"}
    with_links_summary = True  # @param {type:"boolean"}
    with_images_summary = True  # @param {type:"boolean"}

    fetched_content = fetch_content(
        url,
        return_format=content_format,
        json_response=json_response,
        bypass_cache=bypass_cache,
        disable_gfm=disable_gfm,
        remove_images=remove_images,
        timeout=timeout,
        with_generated_alt=with_generated_alt,
        with_links_summary=with_links_summary,
        with_images_summary=with_images_summary,
    )
    logger.info("\nFetched Content:\n")
    logger.info(fetched_content)
