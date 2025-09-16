
import os
import re
import logging
from typing import List

import cloudscraper
import json
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.types import Message

from config import LOGGER

logger = LOGGER("auto_accept.py")

class AnimepaheDownloader:
    """Main downloader class for animepahe.si - same as CLI version"""
    
    def __init__(self, debug=False):
        self.debug = debug
        
        # Create cloudscraper session with proper headers
        self.session = cloudscraper.create_scraper()
        self.session.headers.update({
            'authority': 'animepahe.si',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'en-US,en;q=0.9',
            'cookie': '__ddg2_=;',
            'dnt': '1',
            'sec-ch-ua': '"Not A(Brand)";v="99", "Microsoft Edge";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'x-requested-with': 'XMLHttpRequest',
            'referer': 'https://animepahe.si',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        })
        
        if debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")
    
    def step_2(self, s, seperator, base=10):
        """Helper function for Kwik link bypass"""
        mapped_range = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/"
        numbers = mapped_range[0:base]
        max_iter = 0
        for index, value in enumerate(s[::-1]):
            max_iter += int(value if value.isdigit() else 0) * (seperator**index)
        mid = ''
        while max_iter > 0:
            mid = numbers[int(max_iter % base)] + mid
            max_iter = (max_iter - (max_iter % base)) / base
        return mid or '0'

    def step_1(self, data, key, load, seperator):
        """First step in Kwik link bypass"""
        payload = ""
        i = 0
        seperator = int(seperator)
        load = int(load)
        while i < len(data):
            s = ""
            while data[i] != key[seperator]:
                s += data[i]
                i += 1
            for index, value in enumerate(key):
                s = s.replace(value, str(index))
            payload += chr(int(self.step_2(s, seperator, 10)) - load)
            i += 1
        payload = re.findall(
            r'action="([^\"]+)" method="POST"><input type="hidden" name="_token"\s+value="([^\"]+)', payload
        )[0]
        return payload

    def bypass_kwik(self, link: str):
        """Bypass Kwik.si link to get direct download URL using cloudscraper"""
        try:
            logger.debug(f"Bypassing kwik link: {link}")
            
            # Create a fresh session for kwik to avoid cookie conflicts  
            kwik_session = cloudscraper.create_scraper()
            
            # Set proper headers for kwik requests
            kwik_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            resp = kwik_session.get(link, headers=kwik_headers)
            logger.debug(f"Initial response status: {resp.status_code}")
            
            # Extract bypass parameters
            matches = re.findall(r'\("(\S+)",\d+,"(\S+)",(\d+),(\d+)', resp.text)
            if not matches:
                logger.debug("No bypass parameters found in kwik page")
                return None
            
            data, key, load, seperator = matches[0]
            logger.debug(f"Bypass params: data={data[:50]}..., key={key}, load={load}, separator={seperator}")
            
            url, token = self.step_1(data=data, key=key, load=load, seperator=seperator)
            logger.debug(f"Decoded URL: {url}, token: {token[:20]}...")
            
            post_data = {"_token": token}
            post_headers = kwik_headers.copy()
            post_headers.update({
                'referer': link,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://kwik.si'
            })
            
            resp = kwik_session.post(url=url, data=post_data, headers=post_headers, allow_redirects=False)
            
            logger.debug(f"POST response status: {resp.status_code}")
            logger.debug(f"POST response headers: {dict(resp.headers)}")
            
            # Check for location header (case insensitive)
            for header_name, header_value in resp.headers.items():
                if header_name.lower() == 'location':
                    logger.debug(f"Got direct download URL: {header_value}")
                    return header_value
            
            # If no location header, check for other redirect indicators
            if resp.status_code in [301, 302, 303, 307, 308]:
                logger.debug("Got redirect status but no location header")
            elif resp.status_code == 419:
                logger.debug("Got 419 error - possible CSRF token issue")
            
            logger.debug("No location header found in response")
            return None
            
        except Exception as e:
            logger.debug(f"Error bypassing Kwik link: {e}")
            import traceback
            logger.debug(f"Full traceback: {traceback.format_exc()}")
            return None

    def extract_kwik_link(self, pahe_url: str):
        """Extract Kwik.si link from Pahe download page using cloudscraper"""
        try:
            logger.debug(f"Extracting kwik link from: {pahe_url}")
            response = self.session.get(pahe_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Check both script tags and iframes for kwik links (should be kwik.si/f/ not /e/)
            for element in soup.find_all(['script', 'iframe']):
                if element.name == 'script' and element.get('type') == 'text/javascript':
                    match = re.search(r'https://kwik\.si/f/[\w\d]+', element.text)
                else:
                    match = re.search(r'https://kwik\.si/f/[\w\d]+', str(element))
                if match:
                    kwik_link = match.group(0)
                    logger.debug(f"Found kwik link: {kwik_link}")
                    return kwik_link
            
            logger.debug("No kwik.si/f/ link found")
            return None
        
        except Exception as e:
            logger.debug(f"Error extracting Kwik link from Pahe: {e}")
            return None

    def search_anime(self, query: str):
        """Search for anime on animepahe.si"""
        logger.info(f"Searching for anime: {query}")
        search_url = f"https://animepahe.si/api?m=search&q={query.replace(' ', '+')}"
        
        try:
            response = self.session.get(search_url)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for anime in data.get('data', []):
                results.append({
                    'title': anime.get('title', ''),
                    'type': anime.get('type', ''),
                    'episodes': anime.get('episodes', ''),
                    'status': anime.get('status', ''),
                    'season': anime.get('season', ''),
                    'year': anime.get('year', ''),
                    'score': anime.get('score', ''),
                    'poster': anime.get('poster', ''),
                    'session': anime.get('session', ''),  # This is the anime slug/ID
                })
            
            logger.info(f"Found {len(results)} anime(s)")
            return results
            
        except Exception as e:
            logger.error(f"Error searching anime: {e}")
            return []

    def get_episodes(self, session_id: str, page: int = 1):
        """Get episodes for a specific anime"""
        logger.debug(f"Getting episodes for session {session_id}, page {page}")
        episodes_url = f"https://animepahe.si/api?m=release&id={session_id}&sort=episode_asc&page={page}"
        
        try:
            response = self.session.get(episodes_url)
            response.raise_for_status()
            data = response.json()
            
            return {
                'episodes': data.get('data', []),
                'current_page': data.get('current_page', 1),
                'last_page': data.get('last_page', 1),
                'total': data.get('total', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting episodes: {e}")
            return {'episodes': [], 'current_page': 1, 'last_page': 1, 'total': 0}

    def get_download_links(self, session_id: str, episode_session: str):
        """Get download links for a specific episode"""
        logger.debug(f"Getting download links for episode session: {episode_session}")
        episode_url = f"https://animepahe.si/play/{session_id}/{episode_session}"
        
        try:
            response = self.session.get(episode_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract all download links from the dropdown menu
            download_links = soup.select("#pickDownload a.dropdown-item")
            
            links = []
            for link in download_links:
                links.append({
                    'text': link.get_text(strip=True),
                    'url': link.get('href', ''),
                })
            
            logger.debug(f"Found {len(links)} download links")
            return links
            
        except Exception as e:
            logger.error(f"Error getting download links: {e}")
            return []

    def get_direct_download_url(self, pahe_download_url: str):
        """Get direct download URL from a Pahe download page URL"""
        try:
            logger.debug(f"Processing download URL: {pahe_download_url}")
            
            # Extract kwik.si/f/ link from the download page
            kwik_link = self.extract_kwik_link(pahe_download_url)
            if not kwik_link:
                logger.warning("No kwik.si/f/ link found on download page")
                return None
            
            # Bypass kwik.si to get direct download URL
            direct_url = self.bypass_kwik(kwik_link)
            if not direct_url:
                logger.warning("Failed to bypass kwik.si link")
                return None
            
            return direct_url
        
        except Exception as e:
            logger.error(f"Error getting direct download URL: {e}")
            return None

    def download_file(self, url: str, output_path: str, progress_callback=None):
        """Download file from direct URL with optional progress callback"""
        try:
            logger.info(f"Downloading file to: {output_path}")
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://kwik.cx/',
                'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5'
            }
            
            with self.session.get(url, headers=headers, stream=True) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if progress_callback and total_size > 0:
                                progress = (downloaded / total_size) * 100
                                progress_callback(progress, downloaded, total_size)
                
                logger.info(f"Download completed: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False



def parse_episode_range(episode_str: str) -> List[int]:
    """Parse episode range from string like '1-5' or '10' or '1,3,5-7'"""
    episodes = []
    
    # Split by comma first
    parts = episode_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # Range format like "1-5"
            try:
                start, end = part.split('-', 1)
                start_ep = int(start.strip())
                end_ep = int(end.strip())
                episodes.extend(range(start_ep, end_ep + 1))
            except ValueError:
                continue
        else:
            # Single episode
            try:
                episodes.append(int(part))
            except ValueError:
                continue
    
    return sorted(list(set(episodes)))  # Remove duplicates and sort