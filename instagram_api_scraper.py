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
from typing import List, Dict, Set, Optional
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
    
    def _fetch_users(self, endpoint: str, max_count: Optional[int] = None) -> List[Dict]:
        """
        Common method to fetch users (followers or following).
        
        Args:
            endpoint: The API endpoint ('followers' or 'following')
            max_count: Maximum number of users to fetch (None for all)
            
        Returns:
            List of user dictionaries
        """
        user_type = endpoint  # Use endpoint as user_type for display purposes
        print(f"Fetching {user_type} for user ID: {self.user_id}")
        
        users = []
        max_id = None
        batch_count = 0
        
        while True:
            # Build URL
            url = f'https://www.instagram.com/api/v1/friendships/{self.user_id}/{endpoint}/'
            params = {'count': 100}
            
            if max_id:
                params['max_id'] = max_id
            
            try:
                batch_count += 1
                current_count = len(users)
                print(f"Fetching batch {batch_count}... (current count: {current_count})")
                
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract users from response
                if 'users' in data:
                    batch_users = data['users']
                    users.extend(batch_users)
                    print(f"  Fetched {len(batch_users)} users in this batch")
                else:
                    print(f"  No users found in response: {data}")
                    break
                
                # Check if we've reached the limit
                if max_count and len(users) >= max_count:
                    users = users[:max_count]
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
        
        print(f"Total {user_type} fetched: {len(users)}")
        return users
    
    def get_followers(self, max_count: Optional[int] = None) -> List[Dict]:
        """
        Fetch all followers of the user.
        
        Args:
            max_count: Maximum number of followers to fetch (None for all)
            
        Returns:
            List of follower dictionaries
        """
        return self._fetch_users('followers', max_count)
    
    def get_following(self, max_count: Optional[int] = None) -> List[Dict]:
        """
        Fetch all users that the user is following.
        
        Args:
            max_count: Maximum number of following to fetch (None for all)
            
        Returns:
            List of following dictionaries
        """
        return self._fetch_users('following', max_count)
    
    def extract_usernames(self, users: List[Dict]) -> List[str]:
        """Extract usernames from user dictionaries."""
        usernames = []
        for user in users:
            if 'username' in user:
                usernames.append(user['username'])
            else:
                print(f"Warning: No username found in user data: {user}")
        
        return usernames