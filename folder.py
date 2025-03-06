import os
import sys
import configparser
import webbrowser
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import platform

# Добавляем проверку для Windows
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def save_page_as_html(session, url, folder):
    try:
        domain = urlparse(url).netloc
        if not domain:
            domain = url.split('//')[1].split('/')[0]
        
        filename = f"{domain}.html"
        filepath = os.path.join(folder, filename)
        
        async with session.get(url) as response:
            content = await response.text()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        return filepath
    except Exception as e:
        print("Error saving HTML: " + str(e))
        return None

def read_urls_from_ini(script_dir):
    try:
        config = configparser.RawConfigParser()
        ini_path = os.path.join(script_dir, 'Search.ini')
        config.read(ini_path)
        return config['URLs']
    except Exception as e:
        print("Error reading Search.ini: " + str(e))
        return None
    
def check_html_content(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().lower()
            # Расширенный список фраз, указывающих на отсутствие результатов
            no_result_phrases = [
                "not found",
                "no results",
                "nothing matched",
                "nothing found",
                "no matches found",
                "0 results",
                "zero results",
                "couldn't find",
                "it seems we cannot find",
                "something's wrong here",
                "sorry, but nothing matched your search terms",
                "no results found",
                "nothing found",
                "no posts were found",
                "no search results were found here",
                "результаты не найдены",
                "it seems we can't find what you're looking for",
                "найдено 0 результатов",
                "no results",
                "no results found"
            ]
            # Проверяем каждую фразу
            for phrase in no_result_phrases:
                if phrase in content:
                    print(f"Found '{phrase}' in results, skipping...")
                    return False
            return True
    except Exception as e:
        print("Error checking content: " + str(e))
        return True  # В случае ошибки всё равно открываем

async def process_urls(urls, folder_name, installer_folder):
    url_results = []
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = []
        for name, base_url in urls.items():
            parts = base_url.split('%s')
            if len(parts) > 1:
                search_url = folder_name.join(parts)
            else:
                parts = base_url.split('%S')
                if len(parts) > 1:
                    search_url = folder_name.join(parts)
                else:
                    search_url = base_url
                    
            print("Processing: " + search_url)
            tasks.append(save_page_as_html(session, search_url, installer_folder))
            url_results.append((name, search_url))
        
        saved_files = await asyncio.gather(*tasks, return_exceptions=True)
        
        for (name, url), filepath in zip(url_results, saved_files):
            if isinstance(filepath, str) and os.path.exists(filepath):
                print("Successfully saved page for " + name)
                if check_html_content(filepath):
                    webbrowser.open(url)
                else:
                    print(f"Not opening {name} - no results found")
            else:
                print(f"Failed to save page for {name}")

async def async_main():
    try:
        tc_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
        
        if tc_path.endswith('D') or tc_path.endswith('C'):
            tc_path = tc_path[:-1]
        
        folder_name = os.path.basename(tc_path.rstrip('\\'))
        
        print("Working in directory: " + tc_path)
        print("Selected folder: " + folder_name)

        if not os.path.exists(tc_path):
            print("Error: Directory does not exist: " + tc_path)
            return
            
        if not os.access(tc_path, os.W_OK):
            print("No write permissions in: " + tc_path)
            return
            
        installer_folder = os.path.join(tc_path, "Installer")
        try:
            os.makedirs(installer_folder, exist_ok=True)
            print("Created/accessed Installer folder in: " + installer_folder)
            
            if folder_name:
                script_dir = os.path.dirname(os.path.realpath(__file__))
                urls = read_urls_from_ini(script_dir)
                if urls:
                    await process_urls(urls, folder_name, installer_folder)
            else:
                print("Could not determine folder name from path.")
                    
        except OSError as e:
            print("Error working with directory: " + str(e))
            return
            
    except Exception as e:
        print("Error: " + str(e))

def main():
    try:
        if platform.system() == 'Windows':
            # Для Windows используем специальный запуск
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(async_main())
    finally:
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
