#!/usr/bin/env python3
"""
Instagram API Scraper
Uses Instagram's internal API to fetch followers and following lists.

This script can fetch:
1. All followers of a user
2. All users that a user is following
3. Handle pagination automatically
4. Save data in multiple formats

Note: This uses Instagram's internal API which may change. Use responsibly.
"""

import requests
import json
import time
import csv
import os
from typing import List, Dict, Set, Optional
from pathlib import Path
import argparse
from urllib.parse import urlparse, parse_qs
import re


class InstagramAPIScraper:
    def __init__(self, user_id: str, csrf_token: str, **kwargs):
        """
        Initialize the scraper with authentication details.
        
        Args:
            user_id: Instagram user ID (numeric)
            csrf_token: Instagram CSRF token
            **kwargs: Additional credentials like x_ig_www_claim, x_web_session_id, cookies, etc.
        """
        self.user_id = user_id
        self.csrf_token = csrf_token
        self.session = requests.Session()
        
        # Set up headers based on the Instagram API format
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-GB,en-MT;q=0.9,en-US;q=0.8,en;q=0.7',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-full-version-list': '"Not;A=Brand";v="99.0.0.0", "Google Chrome";v="139.0.7258.155", "Chromium";v="139.0.7258.155"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"19.0.0"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': kwargs.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'),
            'x-asbd-id': kwargs.get('x_asbd_id', '359341'),
            'x-csrftoken': csrf_token,
            'x-ig-app-id': kwargs.get('x_ig_app_id', '936619743392459'),
            'x-ig-www-claim': kwargs.get('x_ig_www_claim', ''),
            'x-requested-with': 'XMLHttpRequest',
            'x-web-session-id': kwargs.get('x_web_session_id', ''),
            'referer': kwargs.get('referer', f'https://www.instagram.com/user/followers/'),
            'sec-ch-prefers-color-scheme': 'dark',
            'priority': 'u=1, i'
        }
        
        # Update session with headers
        self.session.headers.update(self.headers)
        
        # Set cookies if provided
        if kwargs.get('cookies'):
            self._set_cookies_from_string(kwargs['cookies'])
        
        # Rate limiting
        self.request_delay = 2  # seconds between requests
    
    def _set_cookies_from_string(self, cookie_string: str):
        """Parse cookie string and set cookies in the session."""
        try:
            # Parse the cookie string
            cookies = {}
            for cookie in cookie_string.split(';'):
                cookie = cookie.strip()
                if '=' in cookie:
                    name, value = cookie.split('=', 1)
                    cookies[name.strip()] = value.strip()
            
            # Set cookies in the session
            self.session.cookies.update(cookies)
            print(f"Set {len(cookies)} cookies in session")
            
        except Exception as e:
            print(f"Warning: Could not parse cookies: {e}")
    
    def get_followers(self, max_count: Optional[int] = None) -> List[Dict]:
        """
        Fetch all followers of the user.
        
        Args:
            max_count: Maximum number of followers to fetch (None for all)
            
        Returns:
            List of follower dictionaries
        """
        print(f"Fetching followers for user ID: {self.user_id}")
        
        followers = []
        max_id = None
        count = 0
        
        while True:
            # Build URL
            url = f'https://www.instagram.com/api/v1/friendships/{self.user_id}/followers/'
            params = {'count': 100}
            
            if max_id:
                params['max_id'] = max_id
            
            try:
                print(f"Fetching batch {len(followers) // 100 + 1}... (current count: {len(followers)})")
                
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract users from response
                if 'users' in data:
                    batch_users = data['users']
                    followers.extend(batch_users)
                    print(f"  Fetched {len(batch_users)} users in this batch")
                else:
                    print(f"  No users found in response: {data}")
                    break
                
                # Check if we've reached the limit
                if max_count and len(followers) >= max_count:
                    followers = followers[:max_count]
                    print(f"  Reached maximum count: {max_count}")
                    break
                
                # Check if there are more pages
                if 'next_max_id' in data and data['next_max_id']:
                    max_id = data['next_max_id']
                    print(f"  Next max_id: {max_id[:20]}...")
                else:
                    print("  No more pages available")
                    break
                
                # Rate limiting
                time.sleep(self.request_delay)
                
            except requests.exceptions.RequestException as e:
                print(f"  Error fetching batch: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"  Error parsing JSON response: {e}")
                break
            except Exception as e:
                print(f"  Unexpected error: {e}")
                break
        
        print(f"Total followers fetched: {len(followers)}")
        return followers
    
    def get_following(self, max_count: Optional[int] = None) -> List[Dict]:
        """
        Fetch all users that the user is following.
        
        Args:
            max_count: Maximum number of following to fetch (None for all)
            
        Returns:
            List of following dictionaries
        """
        print(f"Fetching following for user ID: {self.user_id}")
        
        following = []
        max_id = None
        count = 0
        
        while True:
            # Build URL
            url = f'https://www.instagram.com/api/v1/friendships/{self.user_id}/following/'
            params = {'count': 100}
            
            if max_id:
                params['max_id'] = max_id
            
            try:
                print(f"Fetching batch {len(following) // 100 + 1}... (current count: {len(following)})")
                
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract users from response
                if 'users' in data:
                    batch_users = data['users']
                    following.extend(batch_users)
                    print(f"  Fetched {len(batch_users)} users in this batch")
                else:
                    print(f"  No users found in response: {data}")
                    break
                
                # Check if we've reached the limit
                if max_count and len(following) >= max_count:
                    following = following[:max_count]
                    print(f"  Reached maximum count: {max_count}")
                    break
                
                # Check if there are more pages
                if 'next_max_id' in data and data['next_max_id']:
                    max_id = data['next_max_id']
                    print(f"  Next max_id: {max_id[:20]}...")
                else:
                    print("  No more pages available")
                    break
                
                # Rate limiting
                time.sleep(self.request_delay)
                
            except requests.exceptions.RequestException as e:
                print(f"  Error fetching batch: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"  Error parsing JSON response: {e}")
                break
            except Exception as e:
                print(f"  Unexpected error: {e}")
                break
        
        print(f"Total following fetched: {len(following)}")
        return following
    
    def extract_usernames(self, users: List[Dict]) -> List[str]:
        """Extract usernames from user dictionaries."""
        usernames = []
        for user in users:
            if 'username' in user:
                usernames.append(user['username'])
            elif 'user' in user and 'username' in user['user']:
                usernames.append(user['user']['username'])
        
        return usernames
    
    def save_data(self, data: List[Dict], filename: str, format_type: str = 'json') -> None:
        """Save data to file in specified format."""
        if format_type == 'json':
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif format_type == 'csv':
            if data and len(data) > 0:
                # Get all possible fields
                all_fields = set()
                for user in data:
                    all_fields.update(user.keys())
                
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=sorted(all_fields))
                    writer.writeheader()
                    writer.writerows(data)
        
        print(f"Data saved to {filename}")
    
    def save_usernames_only(self, usernames: List[str], filename: str) -> None:
        """Save only usernames to a text file (one per line)."""
        with open(filename, 'w', encoding='utf-8') as f:
            for username in usernames:
                f.write(f"{username}\n")
        
        print(f"Usernames saved to {filename}")


def extract_credentials_from_curl(curl_command: str) -> Dict[str, str]:
    """
    Extract credentials from a curl command.
    
    Args:
        curl_command: The curl command string
        
    Returns:
        Dictionary with user_id, csrf_token, and other necessary credentials
    """
    credentials = {}
    
    # Extract user_id from URL
    url_match = re.search(r'friendships/(\d+)/followers', curl_command)
    if url_match:
        credentials['user_id'] = url_match.group(1)
    
    # Extract csrf_token from X-CSRFToken header
    csrf_match = re.search(r'x-csrftoken: ([^\n\r\\"]+)', curl_command, re.IGNORECASE)
    if csrf_match:
        credentials['csrf_token'] = csrf_match.group(1).strip()
    
    # Extract csrf_token from cookies if not found in headers
    if 'csrf_token' not in credentials:
        cookie_csrf_match = re.search(r'csrf_token=([^;]+)', curl_command)
        if cookie_csrf_match:
            credentials['csrf_token'] = cookie_csrf_match.group(1).strip()
    
    # Extract session_id from cookies
    session_match = re.search(r'sessionid=(\d+%3A[^;]+)', curl_command)
    if session_match:
        credentials['session_id'] = session_match.group(1)
    
    # Extract ds_user_id from cookies
    ds_user_match = re.search(r'ds_user_id=(\d+)', curl_command)
    if ds_user_match:
        credentials['ds_user_id'] = ds_user_match.group(1)
    
    # Extract X-IG-WWW-Claim from header
    claim_match = re.search(r'x-ig-www-claim: ([^\n\r\\"]+)', curl_command, re.IGNORECASE)
    if claim_match:
        credentials['x_ig_www_claim'] = claim_match.group(1).strip()
    
    # Extract X-Web-Session-ID from header
    web_session_match = re.search(r'x-web-session-id: ([^\n\r\\"]+)', curl_command, re.IGNORECASE)
    if web_session_match:
        credentials['x_web_session_id'] = web_session_match.group(1).strip()
    
    # Extract X-IG-App-ID from header
    app_id_match = re.search(r'x-ig-app-id: ([^\n\r\\"]+)', curl_command, re.IGNORECASE)
    if app_id_match:
        credentials['x_ig_app_id'] = app_id_match.group(1).strip()
    
    # Extract X-ASBD-ID from header
    asbd_match = re.search(r'x-asbd-id: ([^\n\r\\"]+)', curl_command, re.IGNORECASE)
    if asbd_match:
        credentials['x_asbd_id'] = asbd_match.group(1).strip()
    
    # Extract User-Agent from header
    user_agent_match = re.search(r'user-agent: ([^\n\r\\"]+)', curl_command, re.IGNORECASE)
    if user_agent_match:
        credentials['user_agent'] = user_agent_match.group(1).strip()
    
    # Extract Referer from header
    referer_match = re.search(r'referer: ([^\n\r\\"]+)', curl_command, re.IGNORECASE)
    if referer_match:
        credentials['referer'] = referer_match.group(1).strip()
    
    # Extract cookies string for cookie-based authentication
    cookie_match = re.search(r'-b "([^"]+)"', curl_command)
    if cookie_match:
        credentials['cookies'] = cookie_match.group(1)
    
    return credentials


def main():
    parser = argparse.ArgumentParser(description='Instagram API Scraper')
    parser.add_argument('--user-id', help='Instagram user ID (numeric)')
    parser.add_argument('--session-id', help='Instagram session ID')
    parser.add_argument('--csrf-token', help='Instagram CSRF token')
    parser.add_argument('--curl-file', help='File containing curl command')
    parser.add_argument('--max-count', type=int, help='Maximum number of users to fetch')
    parser.add_argument('--output-dir', default='instagram_data', help='Output directory')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both', help='Output format')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests in seconds')
    
    args = parser.parse_args()
    
    # Create output directory
    Path(args.output_dir).mkdir(exist_ok=True)
    
    # Get credentials
    if args.curl_file:
        # Read curl command from file
        with open(args.curl_file, 'r') as f:
            curl_command = f.read()
        credentials = extract_credentials_from_curl(curl_command)
    else:
        # Use command line arguments
        credentials = {
            'user_id': args.user_id,
            'session_id': args.session_id,
            'csrf_token': args.csrf_token
        }
    
    # Validate credentials
    required_fields = ['user_id', 'csrf_token']
    missing_fields = [field for field in required_fields if not credentials.get(field)]
    
    if missing_fields:
        print(f"Missing required credentials: {missing_fields}")
        print("Please provide either --curl-file or all individual credential arguments")
        return
    
    print("Credentials extracted:")
    print(f"User ID: {credentials['user_id']}")
    print(f"CSRF Token: {credentials['csrf_token'][:20]}...")
    if credentials.get('x_ig_www_claim'):
        print(f"X-IG-WWW-Claim: {credentials['x_ig_www_claim'][:20]}...")
    if credentials.get('x_web_session_id'):
        print(f"X-Web-Session-ID: {credentials['x_web_session_id']}")
    print()
    
    # Create scraper with all available credentials
    scraper = InstagramAPIScraper(
        user_id=credentials['user_id'],
        csrf_token=credentials['csrf_token'],
        x_ig_www_claim=credentials.get('x_ig_www_claim', ''),
        x_web_session_id=credentials.get('x_web_session_id', ''),
        x_ig_app_id=credentials.get('x_ig_app_id', '936619743392459'),
        x_asbd_id=credentials.get('x_asbd_id', '359341'),
        user_agent=credentials.get('user_agent', ''),
        referer=credentials.get('referer', ''),
        cookies=credentials.get('cookies') # Pass cookies if available
    )
    
    # Set delay
    scraper.request_delay = args.delay
    
    try:
        # Fetch followers
        print("=" * 50)
        followers = scraper.get_followers(max_count=args.max_count)
        
        if followers:
            # Save followers data
            if args.format in ['json', 'both']:
                scraper.save_data(followers, f"{args.output_dir}/followers.json", 'json')
            if args.format in ['csv', 'both']:
                scraper.save_data(followers, f"{args.output_dir}/followers.csv", 'csv')
            
            # Save usernames only
            usernames = scraper.extract_usernames(followers)
            scraper.save_usernames_only(usernames, f"{args.output_dir}/followers.txt")
        
        print()
        
        # Fetch following
        print("=" * 50)
        following = scraper.get_following(max_count=args.max_count)
        
        if following:
            # Save following data
            if args.format in ['json', 'both']:
                scraper.save_data(following, f"{args.output_dir}/following.json", 'json')
            if args.format in ['csv', 'both']:
                scraper.save_data(following, f"{args.output_dir}/following.csv", 'csv')
            
            # Save usernames only
            usernames = scraper.extract_usernames(following)
            scraper.save_usernames_only(usernames, f"{args.output_dir}/following.txt")
        
        print()
        print("=" * 50)
        print("Data collection completed!")
        print(f"Output directory: {args.output_dir}")
        
        if followers and following:
            print(f"Followers: {len(followers)}")
            print(f"Following: {len(following)}")
            
            # Now you can use the existing analyzer
            print("\nYou can now run the follower analyzer:")
            print(f"python instagram_follower_analyzer.py --followers {args.output_dir}/followers.txt --following {args.output_dir}/following.txt")
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        print("Please check your credentials and try again")


if __name__ == "__main__":
    main() 