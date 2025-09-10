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
import logging
import threading
import requests
import yaml
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from pathlib import Path
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

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
    
    def _find_chrome_binary(self):
        """Find Chrome binary on Windows."""
        import platform
        
        if platform.system() != "Windows":
            return None
            
        # Common Chrome installation paths on Windows
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', ''))
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                logger.info(f"Found Chrome at: {path}")
                return path
        
        logger.error("Chrome not found in common locations")
        return None

    def _setup_browser(self):
        """Setup Chrome browser without persistent user data directory."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            
            # Windows compatibility options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            
            # DevTools and automation options
            chrome_options.add_argument("--remote-debugging-port=0")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option("detach", True)
            
            # User agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")
            
            # Window size
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Find Chrome binary
            chrome_binary = self._find_chrome_binary()
            if chrome_binary:
                chrome_options.binary_location = chrome_binary
            
            # Use webdriver-manager to automatically handle ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info(f"Bot {self.bot_id}: Browser initialized")
            
        except Exception as e:
            error_msg = str(e)
            if "cannot find Chrome binary" in error_msg:
                logger.error(f"Bot {self.bot_id}: Chrome browser not found!")
                logger.error("Please install Google Chrome from: https://www.google.com/chrome/")
                logger.error("Or install Chrome via winget: winget install Google.Chrome")
            else:
                logger.error(f"Bot {self.bot_id}: Failed to setup browser: {e}")
            raise
    
    def _handle_cookie_consent(self):
        """Handle cookie consent dialog if present."""
        try:
            # Common selectors for cookie consent buttons
            cookie_selectors = [  # Instagram specific
                "//button[contains(text(), 'Allow all cookies')]",  # Exact Instagram text
                "//button[contains(text(), 'Allow All Cookies')]",
                "//button[contains(text(), 'Accept All')]",
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'Allow all')]",
                "//button[contains(text(), 'Allow All')]",
                "//button[@data-testid='cookie-accept-all']",
                "//button[contains(@class, 'cookie-accept')]",
                "//button[contains(@class, 'accept-all')]"
            ]
            
            wait = WebDriverWait(self.driver, 5)
            
            for selector in cookie_selectors:
                try:
                    cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    cookie_button.click()
                    logger.info(f"Bot {self.bot_id}: Clicked cookie consent button")
                    time.sleep(3)
                    return
                except TimeoutException:
                    continue
            
            logger.info(f"Bot {self.bot_id}: No cookie consent dialog found")
            
        except Exception as e:
            logger.warning(f"Bot {self.bot_id}: Error handling cookie consent: {e}")
    
    def login(self) -> bool:
        """Login to Instagram."""
        try:
            logger.info(f"Bot {self.bot_id}: Attempting login...")
            
            # Navigate to Instagram main page first to handle cookie consent
            self.driver.get("https://www.instagram.com/")
            time.sleep(3)
            
            # Handle cookie consent dialog if present
            self._handle_cookie_consent()
            
            # Now navigate to login page
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
            
            try:
                # Extract session data
                cookies = self.driver.get_cookies()
                csrf_token = self._extract_csrf_token(cookies)
                session_id = self._extract_session_id(cookies)
                user_id = self._extract_user_id_from_session(session_id)
                
                logger.info(f"Bot {self.bot_id}: Extracted session data - CSRF: {csrf_token is not None}, SessionID: {session_id is not None}, UserID: {user_id is not None}")
                
                # Check if we have valid session data
                if not csrf_token or not session_id:
                    logger.error(f"Bot {self.bot_id}: Invalid session data - missing CSRF token or session ID")
                    return False
                
                # Update session data
                self.session_data = {
                    'csrf_token': csrf_token,
                    'session_id': session_id,
                    'user_id': user_id,
                    'last_login': datetime.now().isoformat()
                }
                
                self.is_logged_in = True
                self.last_activity = datetime.now()
                
                # Save session data
                self._save_session_data()
                
                logger.info(f"Bot {self.bot_id}: Login successful")
                return True
                
            except Exception as session_error:
                logger.error(f"Bot {self.bot_id}: Error extracting session data: {session_error}")
                return False
                
        except Exception as e:
            logger.error(f"Bot {self.bot_id}: Login error: {e}")
            return False
    
    def refresh_session(self) -> bool:
        """Refresh the session."""
        try:
            logger.info(f"Bot {self.bot_id}: Refreshing session...")
            
            # Check if current session is still valid
            if self._is_session_valid():
                # Update session data with current cookies
                cookies = self.driver.get_cookies()
                csrf_token = self._extract_csrf_token(cookies)
                session_id = self._extract_session_id(cookies)
                user_id = self._extract_user_id_from_session(session_id)
                
                self.session_data = {
                    'csrf_token': csrf_token,
                    'session_id': session_id,
                    'user_id': user_id,
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
            
            # Handle cookie consent dialog if present
            self._handle_cookie_consent()
            
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
            logger.info(f"Bot {self.bot_id}: Session data saved successfully")
        except Exception as e:
            logger.error(f"Bot {self.bot_id}: Failed to save session data: {e}")
            raise
    
    def restart(self) -> bool:
        """Restart the bot by closing current session and creating a new one."""
        try:
            logger.info(f"Bot {self.bot_id}: Restarting bot...")
            
            # Cleanup current session
            self.cleanup()
            
            # Reset state
            self.is_logged_in = False
            self.session_data = {}
            self.last_activity = None
            self.is_busy = False
            
            # Setup new browser
            self._setup_browser()
            
            # Attempt login with new session
            if self.login():
                logger.info(f"Bot {self.bot_id}: Restart successful")
                return True
            else:
                logger.error(f"Bot {self.bot_id}: Restart failed - login unsuccessful")
                return False
                
        except Exception as e:
            logger.error(f"Bot {self.bot_id}: Restart error: {e}")
            return False
    
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
    
    def __init__(self, config_file: str = "bot_config.yaml", config_dir: str = "bot_config"):
        """
        Initialize the bot slave manager.
        
        Args:
            config_file: Path to YAML configuration file
            config_dir: Directory to store bot configurations
        """
        self.config_file = Path(config_file)
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Hardcoded settings - no configuration needed
        self.port = 5001
        self.health_check_interval = 1800  # 30 minutes
        self.headless = True
        
        self.bot_slaves = {}
        self.monitoring_thread = None
        self.is_monitoring = False
        
        # Flask app for HTTP API
        self.app = Flask(__name__)
        self._setup_routes()
        
        # Load and initialize bot slaves from configuration
        self._initialize_bot_slaves()
    
    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        try:
            if not self.config_file.exists():
                logger.error(f"Configuration file not found: {self.config_file}")
                logger.info("Please create bot_config.yaml with your bot credentials")
                return {}
            
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Configuration loaded from {self.config_file}")
            return config
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def _initialize_bot_slaves(self):
        """Initialize bot slaves from configuration."""
        bots_config = self.config.get('bots', [])
        
        if not bots_config:
            logger.warning("No bots configured in bot_config.yaml")
            return
        
        logger.info(f"Initializing {len(bots_config)} bot slaves from configuration...")
        
        for bot_config in bots_config:
            if not bot_config.get('enabled', True):
                logger.info(f"Skipping disabled bot: {bot_config.get('id', 'unknown')}")
                continue
            
            bot_id = bot_config.get('id')
            username = bot_config.get('username')
            password = bot_config.get('password')
            description = bot_config.get('description', 'No description')
            
            if not all([bot_id, username, password]):
                logger.error(f"Invalid bot configuration: {bot_config}")
                continue
            
            logger.info(f"Adding bot slave: {bot_id} ({description})")
            
            try:
                # Create bot slave
                bot_slave = InstagramBotSlave(
                    bot_id=bot_id,
                    username=username,
                    password=password,
                    config_dir=str(self.config_dir)
                )
                
                # Attempt login
                if bot_slave.login():
                    self.bot_slaves[bot_id] = bot_slave
                    logger.info(f"✅ Bot {bot_id} added and logged in successfully")
                else:
                    logger.warning(f"⚠️ Initial login failed for bot {bot_id}, attempting restart...")
                    if bot_slave.restart():
                        self.bot_slaves[bot_id] = bot_slave
                        logger.info(f"✅ Bot {bot_id} restarted and logged in successfully")
                    else:
                        logger.error(f"❌ Failed to login bot {bot_id} even after restart")
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize bot {bot_id}: {e}")
        
        logger.info(f"Successfully initialized {len(self.bot_slaves)} bot slaves")
    
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
                logger.warning(f"Initial login failed for bot slave {bot_id}, attempting restart...")
                if bot_slave.restart():
                    self.bot_slaves[bot_id] = bot_slave
                    self._save_bot_configurations()
                    logger.info(f"Bot slave {bot_id} restarted and logged in successfully")
                    return True
                else:
                    logger.error(f"Failed to login bot slave {bot_id} even after restart")
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
    
    def start_monitoring(self, check_interval: int = None):
        """Start monitoring bot health."""
        if self.is_monitoring:
            return
        
        if check_interval is None:
            check_interval = self.health_check_interval
        
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
                # Create a copy of items to avoid modifying dict during iteration
                bots_to_check = list(self.bot_slaves.items())
                for bot_id, bot_slave in bots_to_check:
                    if not bot_slave.is_healthy() and not bot_slave.is_busy:
                        logger.warning(f"Bot {bot_id} unhealthy, attempting refresh")
                        if not bot_slave.refresh_session():
                            logger.warning(f"Bot {bot_id} refresh failed, attempting restart")
                            if not bot_slave.restart():
                                logger.error(f"Bot {bot_id} restart failed, removing from pool")
                                if bot_id in self.bot_slaves:
                                    del self.bot_slaves[bot_id]
                
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
    print("Instagram Bot Manager")
    print("=" * 30)
    
    # Check if configuration file exists
    config_file = "bot_config.yaml"
    if not Path(config_file).exists():
        print(f"❌ Configuration file not found: {config_file}")
        print("Please create bot_config.yaml with your bot credentials")
        print("Copy bot_config.yaml.example and update with your credentials")
        return
    
    # Initialize manager with configuration
    print(f"Loading configuration from {config_file}...")
    manager = InstagramBotSlaveManager(config_file=config_file)
    
    if not manager.bot_slaves:
        print("❌ No bot slaves were successfully initialized")
        print("Please check your bot_config.yaml file and bot credentials")
        return
    
    print(f"✅ Successfully initialized {len(manager.bot_slaves)} bot slaves")
    print("🌐 Bot manager running on port 5001")
    print("📡 Main API server should connect to: http://localhost:5001")
    print("Press Ctrl+C to stop")
    print("=" * 30)
    
    # Start the manager
    manager.run()


if __name__ == "__main__":
    main()
