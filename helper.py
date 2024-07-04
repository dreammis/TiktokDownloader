import os
import random
import time

import requests
from tqdm import tqdm

from conf import proxies

browser_useragent = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.3',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.47',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.3',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.43',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.4',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.3',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.3',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.81',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.8',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.65 Safari/537.3',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
]


def random_ua():
    """
	return User-Agent string
	"""
    return random.choice(browser_useragent)


def get_content(url: str, output_name: str, retry_count=0, max_retries=5):
    """
    Download content from URL with progress bar, support for resuming download, retry mechanism, and checks for completed download.

    :param url: URL of the content to be downloaded
    :param output_name: Local file path to save the downloaded content
    :param retry_count: Current retry attempt
    :param max_retries: Maximum number of retry attempts
    :return: Boolean indicating the success of the download
    """
    if url.lower().endswith('.mp3'):
        return False  # Skip download if URL is an MP3 file

    if retry_count > max_retries:
        print("Reached maximum retry limit, stopping retries.")
        return False

    try:
        # Check if the file already exists and its size
        if os.path.exists(output_name):
            start = os.path.getsize(output_name)
        else:
            start = 0

        # Make a HEAD request to get the total size of the file
        head_res = requests.head(url)
        if not head_res.ok:
            print(f"Failed to retrieve file info: {head_res.status_code}")
            return False

        total_size = int(head_res.headers.get('content-length', 0))
        if start >= total_size:
            print(f"File already completely downloaded: {output_name}")
            return True

        # Set headers for partial download if needed
        headers = {'Range': f'bytes={start}-'} if start else {}
        res = requests.get(url, headers=headers, stream=True)

        with open(output_name, "ab") as file:
            with tqdm(total=total_size, initial=start, unit='B', unit_scale=True, desc=output_name) as progress:
                for chunk in res.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
                        progress.update(len(chunk))

        # Check if download is complete
        if os.path.getsize(output_name) < total_size:
            print("Download incomplete, will retry.")
            return get_content(url, output_name, retry_count + 1, max_retries)
        return True

    except requests.RequestException as e:
        print(f"Download failed due to an exception, retrying... ({retry_count + 1}/{max_retries})")
        return get_content(url, output_name, retry_count + 1, max_retries)
