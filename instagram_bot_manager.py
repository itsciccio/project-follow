#!/usr/bin/env python3
"""
Instagram Bot Slave Manager
A service that manages Instagram bot accounts and provides session data to the main API server.

This service runs as a separate process and provides bot session data to the main API server.
The main API server can request bot sessions when processing jobs.

Architecture:
Main API Server <---> Bot Slave Manager <---> Instagram Bot Accounts
     (jobs)              (session data)         (selenium browsers)
"""

import os
import json
import time
import pickle
import logging
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from pathlib import Path
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstagramBotSlave:
    """
    Individual bot slave that maintains a persistent Instagram session.
    """
    
    def __init__(self, bot_id: str, username: str, password: str, config_dir: str = "bot_config"):
        """
        Initialize a bot slave.
        
        Args:
            bot_id: Unique identifier for this bot
            username: Instagram username
            password: Instagram password
            config_dir: Directory to store bot configuration
        """
        self.bot_id = bot_id
        self.username = username
        self.password = password
        self.config_dir = Path(config_dir) / bot_id
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.driver = None
        self.session_data = {}
        self.is_logged_in = False
        self.last_activity = None
        self.is_busy = False
        
        # Initialize browser
        self._setup_browser()
    
    def _setup_browser(self):
        """Setup Chrome browser with persistent user data directory."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument(f"--user-data-dir={self.config_dir / 'chrome_profile'}")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info(f"Bot {self.bot_id}: Browser initialized")
            
        except Exception as e:
            logger.error(f"Bot {self.bot_id}: Failed to setup browser: {e}")
            raise
    
    def login(self) -> bool:
        """Login to Instagram."""
        try:
            logger.info(f"Bot {self.bot_id}: Attempting login...")
            
            # Navigate to Instagram login page
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(3)
            
            # Wait for login form
            wait = WebDriverWait(self.driver, 10)
            username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            password_input = self.driver.find_element(By.NAME, "password")
            
            # Clear and fill login form
            username_input.clear()
            username_input.send_keys(self.username)
            
            password_input.clear()
            password_input.send_keys(self.password)
            
            # Submit login form
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            if "instagram.com" in self.driver.current_url and "login" not in self.driver.current_url:
                # Extract session data
                cookies = self.driver.get_cookies()
                csrf_token = self._extract_csrf_token(cookies)
                session_id = self._extract_session_id(cookies)
                user_id = self._extract_user_id_from_session(session_id)
                
                # Update session data
                self.session_data = {
                    'csrf_token': csrf_token,
                    'session_id': session_id,
                    'user_id': user_id,
                    'cookies': cookies,
                    'last_login': datetime.now().isoformat()
                }
                
                self.is_logged_in = True
                self.last_activity = datetime.now()
                
                # Save session data
                self._save_session_data()
                
                logger.info(f"Bot {self.bot_id}: Login successful")
                return True
            else:
                logger.error(f"Bot {self.bot_id}: Login failed")
                return False
                
        except Exception as e:
            logger.error(f"Bot {self.bot_id}: Login error: {e}")
            return False
    
    def refresh_session(self) -> bool:
        """Refresh the session."""
        try:
            logger.info(f"Bot {self.bot_id}: Refreshing session...")
            
            # Load existing cookies
            cookies = self._load_session_cookies()
            if not cookies:
                logger.warning(f"Bot {self.bot_id}: No saved cookies, attempting fresh login")
                return self.login()
            
            # Navigate to Instagram and load cookies
            self.driver.get("https://www.instagram.com/")
            
            # Clear existing cookies and load saved ones
            self.driver.delete_all_cookies()
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"Bot {self.bot_id}: Failed to add cookie: {e}")
            
            # Refresh page to apply cookies
            self.driver.refresh()
            time.sleep(3)
            
            # Check if session is still valid
            if self._is_session_valid():
                # Update session data
                new_cookies = self.driver.get_cookies()
                csrf_token = self._extract_csrf_token(new_cookies)
                session_id = self._extract_session_id(new_cookies)
                user_id = self._extract_user_id_from_session(session_id)
                
                self.session_data = {
                    'csrf_token': csrf_token,
                    'session_id': session_id,
                    'user_id': user_id,
                    'cookies': new_cookies,
                    'last_login': datetime.now().isoformat()
                }
                
                self.is_logged_in = True
                self.last_activity = datetime.now()
                
                self._save_session_data()
                
                logger.info(f"Bot {self.bot_id}: Session refreshed successfully")
                return True
            else:
                logger.warning(f"Bot {self.bot_id}: Session invalid, attempting fresh login")
                return self.login()
                
        except Exception as e:
            logger.error(f"Bot {self.bot_id}: Session refresh error: {e}")
            return False
    
    def get_session_data(self) -> Optional[Dict]:
        """Get current session data."""
        if not self.is_logged_in or not self.session_data:
            return None
        
        return {
            'bot_id': self.bot_id,
            'csrf_token': self.session_data['csrf_token'],
            'session_id': self.session_data['session_id'],
            'user_id': self.session_data['user_id'],
            'cookies': self.session_data['cookies'],
            'last_login': self.session_data['last_login']
        }
    
    def is_healthy(self) -> bool:
        """Check if bot is healthy."""
        if not self.is_logged_in:
            return False
        
        # Check if session is not too old (24 hours)
        if self.session_data.get('last_login'):
            last_login = datetime.fromisoformat(self.session_data['last_login'])
            if datetime.now() - last_login > timedelta(hours=24):
                return False
        
        return True
    
    def _is_session_valid(self) -> bool:
        """Check if current browser session is valid."""
        try:
            # Try to access Instagram profile page
            self.driver.get("https://www.instagram.com/")
            time.sleep(2)
            
            # Check if we're redirected to login page
            if "login" in self.driver.current_url:
                return False
            
            # Check for presence of Instagram elements
            try:
                self.driver.find_element(By.CSS_SELECTOR, "[data-testid='user-avatar']")
                return True
            except:
                return False
                
        except Exception as e:
            logger.error(f"Bot {self.bot_id}: Error checking session validity: {e}")
            return False
    
    def _extract_csrf_token(self, cookies: List[Dict]) -> Optional[str]:
        """Extract CSRF token from cookies."""
        for cookie in cookies:
            if cookie['name'] == 'csrftoken':
                return cookie['value']
        return None
    
    def _extract_session_id(self, cookies: List[Dict]) -> Optional[str]:
        """Extract session ID from cookies."""
        for cookie in cookies:
            if cookie['name'] == 'sessionid':
                return cookie['value']
        return None
    
    def _extract_user_id_from_session(self, session_id: str) -> Optional[str]:
        """Extract user ID from session ID."""
        try:
            if session_id and '%' in session_id:
                return session_id.split('%')[0]
        except:
            pass
        return None
    
    def _save_session_data(self):
        """Save session data to file."""
        try:
            data_file = self.config_dir / "session_data.json"
            with open(data_file, 'w') as f:
                json.dump(self.session_data, f, indent=2)
        except Exception as e:
            logger.error(f"Bot {self.bot_id}: Failed to save session data: {e}")
    
    def _load_session_cookies(self) -> Optional[List[Dict]]:
        """Load session cookies from file."""
        try:
            cookie_file = self.config_dir / "cookies.pkl"
            if cookie_file.exists():
                with open(cookie_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.error(f"Bot {self.bot_id}: Failed to load cookies: {e}")
        return None
    
    def cleanup(self):
        """Cleanup resources."""
        if self.driver:
            self.driver.quit()
        logger.info(f"Bot {self.bot_id}: Cleaned up")


class InstagramBotSlaveManager:
    """
    Manager for multiple Instagram bot slaves.
    Provides HTTP API for the main server to request bot sessions.
    """
    
    def __init__(self, config_dir: str = "bot_config", port: int = 5001):
        """
        Initialize the bot slave manager.
        
        Args:
            config_dir: Directory to store bot configurations
            port: Port for the HTTP API
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.port = port
        
        self.bot_slaves = {}
        self.monitoring_thread = None
        self.is_monitoring = False
        
        # Flask app for HTTP API
        self.app = Flask(__name__)
        self._setup_routes()
        
        # Load existing bot configurations
        self._load_bot_configurations()
    
    def add_bot_slave(self, bot_id: str, username: str, password: str) -> bool:
        """
        Add a new bot slave.
        
        Args:
            bot_id: Unique identifier for the bot
            username: Instagram username
            password: Instagram password
            
        Returns:
            bool: True if bot was added successfully
        """
        try:
            # Create bot slave
            bot_slave = InstagramBotSlave(bot_id, username, password, str(self.config_dir))
            
            # Attempt login
            if bot_slave.login():
                self.bot_slaves[bot_id] = bot_slave
                self._save_bot_configurations()
                logger.info(f"Bot slave {bot_id} added and logged in successfully")
                return True
            else:
                logger.error(f"Failed to login bot slave {bot_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add bot slave {bot_id}: {e}")
            return False
    
    def get_available_bot(self) -> Optional[Dict]:
        """
        Get an available bot session.
        
        Returns:
            Dict with session data or None if no bots available
        """
        # Find a healthy, non-busy bot
        for bot_id, bot_slave in self.bot_slaves.items():
            if not bot_slave.is_busy and bot_slave.is_healthy():
                bot_slave.is_busy = True
                bot_slave.last_activity = datetime.now()
                return bot_slave.get_session_data()
        
        # If no healthy bots, try to refresh one
        for bot_id, bot_slave in self.bot_slaves.items():
            if not bot_slave.is_busy:
                logger.info(f"Attempting to refresh bot {bot_id}")
                if bot_slave.refresh_session():
                    bot_slave.is_busy = True
                    bot_slave.last_activity = datetime.now()
                    return bot_slave.get_session_data()
        
        return None
    
    def release_bot(self, bot_id: str):
        """Release a bot back to the pool."""
        if bot_id in self.bot_slaves:
            self.bot_slaves[bot_id].is_busy = False
            self.bot_slaves[bot_id].last_activity = datetime.now()
            logger.info(f"Bot {bot_id} released back to pool")
    
    def start_monitoring(self, check_interval: int = 1800):
        """Start monitoring bot health."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitor_bots,
            args=(check_interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"Started bot monitoring with {check_interval}s interval")
    
    def _monitor_bots(self, check_interval: int):
        """Monitor bot health in a separate thread."""
        while self.is_monitoring:
            try:
                for bot_id, bot_slave in self.bot_slaves.items():
                    if not bot_slave.is_healthy() and not bot_slave.is_busy:
                        logger.warning(f"Bot {bot_id} unhealthy, attempting refresh")
                        bot_slave.refresh_session()
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in bot monitoring: {e}")
                time.sleep(60)
    
    def _setup_routes(self):
        """Setup Flask routes for HTTP API."""
        
        @self.app.route('/api/bot/request', methods=['POST'])
        def request_bot():
            """Request an available bot session."""
            try:
                bot_data = self.get_available_bot()
                if bot_data:
                    return jsonify({
                        'success': True,
                        'bot_data': bot_data
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'No available bots'
                    }), 503
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/bot/release', methods=['POST'])
        def release_bot():
            """Release a bot back to the pool."""
            try:
                data = request.json
                if not data or 'bot_id' not in data:
                    return jsonify({'error': 'bot_id required'}), 400
                
                self.release_bot(data['bot_id'])
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/bot/status', methods=['GET'])
        def get_bot_status():
            """Get status of all bots."""
            try:
                status = {}
                for bot_id, bot_slave in self.bot_slaves.items():
                    status[bot_id] = {
                        'is_logged_in': bot_slave.is_logged_in,
                        'is_busy': bot_slave.is_busy,
                        'is_healthy': bot_slave.is_healthy(),
                        'last_activity': bot_slave.last_activity.isoformat() if bot_slave.last_activity else None
                    }
                
                return jsonify({
                    'total_bots': len(self.bot_slaves),
                    'available_bots': len([b for b in self.bot_slaves.values() if not b.is_busy and b.is_healthy()]),
                    'bots': status
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/bot/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'total_bots': len(self.bot_slaves),
                'monitoring_active': self.is_monitoring
            })
    
    def _save_bot_configurations(self):
        """Save bot configurations to file."""
        try:
            config_file = self.config_dir / "bot_configurations.json"
            configs = {}
            for bot_id, bot_slave in self.bot_slaves.items():
                configs[bot_id] = {
                    'username': bot_slave.username,
                    'created_at': datetime.now().isoformat()
                }
            
            with open(config_file, 'w') as f:
                json.dump(configs, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save bot configurations: {e}")
    
    def _load_bot_configurations(self):
        """Load bot configurations from file."""
        try:
            config_file = self.config_dir / "bot_configurations.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    configs = json.load(f)
                
                # Note: Passwords are not saved for security
                # Bots will need to be re-authenticated
                logger.info(f"Loaded {len(configs)} bot configurations")
                
        except Exception as e:
            logger.error(f"Failed to load bot configurations: {e}")
    
    def run(self, host='0.0.0.0', port=None):
        """Run the bot slave manager HTTP server."""
        if port is None:
            port = self.port
        
        logger.info(f"Starting bot slave manager on {host}:{port}")
        self.start_monitoring()
        
        try:
            self.app.run(host=host, port=port, debug=False)
        except KeyboardInterrupt:
            logger.info("Shutting down bot slave manager...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup all resources."""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        for bot_slave in self.bot_slaves.values():
            bot_slave.cleanup()
        
        logger.info("Bot slave manager cleaned up")


def main():
    """Main function for running the bot slave manager."""
    print("Instagram Bot Slave Manager")
    print("=" * 40)
    
    # Initialize manager
    manager = InstagramBotSlaveManager(port=5001)
    
    # Add bot slaves (you'll need to provide real credentials)
    print("Adding bot slaves...")
    
    # Example: Add a bot slave
    # manager.add_bot_slave("bot_1", "your_bot_username", "your_bot_password")
    
    # Start the manager
    manager.run()


if __name__ == "__main__":
    main()
