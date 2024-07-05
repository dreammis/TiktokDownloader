import os
import random
import time

import requests
from tqdm import tqdm

from conf import proxies
from utils.file_format import check_file
from utils.request_retry import requests_retry_session

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
        response = requests_retry_session().get(url, stream=True, timeout=(10, 30))

        if response.status_code == 200:
            # 尝试获取响应头中的文件名
            total_size_in_bytes = int(response.headers.get('content-length', 0))
            progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)

            content_length = int(response.headers.get('content-length', 0))

            # 增加判断是否图书文件已存在，避免重复工作
            if check_file(output_name):
                print(f"文件已存在: {output_name}")
                progress_bar.close()
                return True

            # Check if file already exists and resume download if partial file exists
            existing_size = os.path.getsize(output_name) if os.path.exists(output_name) else 0
            if existing_size < content_length:
                with open(output_name, 'ab') as file, tqdm(total=content_length, initial=existing_size, unit='iB',
                                                           unit_scale=True) as progress_bar:
                    for chunk in response.iter_content(chunk_size=1024):
                        file.write(chunk)
                        progress_bar.update(len(chunk))
                progress_bar.close()

            # Verify download integrity
            if os.path.getsize(output_name) != content_length:
                print(f"Download incomplete or corrupted: {output_name}")
                return get_content(url, output_name, retry_count + 1)  # Retry download
            print(f"Download successful: {output_name}")
            return True
        else:
            print("下载失败，状态码：", response.status_code)

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        if retry_count < max_retries:
            return get_content(url, output_name, retry_count + 1, max_retries)
        else:
            print("Failed after retrying.")
            return False
