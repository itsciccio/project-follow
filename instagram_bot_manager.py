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
import yaml
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path

# Suppress Chrome logs at environment level
os.environ['WDM_LOG_LEVEL'] = '0'  # Suppress webdriver-manager logs
os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Import Instagram scraper for actual analysis
from instagram_api_scraper import InstagramAPIScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress unwanted logs
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('webdriver_manager').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

# Suppress Chrome/Chromium logs
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Suppress specific selenium warnings
logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(logging.WARNING)
logging.getLogger('selenium.webdriver.common.service').setLevel(logging.WARNING)
logging.getLogger('selenium.webdriver.chrome.service').setLevel(logging.WARNING)

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
        self.scraper = None  # Persistent Instagram scraper instance
        
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
            
            # Essential options for stability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            
            # Suppress browser logs and reduce noise
            chrome_options.add_argument("--log-level=3")  # Only show fatal errors
            chrome_options.add_argument("--silent")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--disable-hang-monitor")
            chrome_options.add_argument("--disable-prompt-on-repost")
            chrome_options.add_argument("--disable-domain-reliability")
            chrome_options.add_argument("--disable-component-extensions-with-background-pages")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-translate")
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-client-side-phishing-detection")
            chrome_options.add_argument("--disable-component-update")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-print-preview")
            chrome_options.add_argument("--disable-speech-api")
            chrome_options.add_argument("--hide-scrollbars")
            chrome_options.add_argument("--mute-audio")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--no-pings")
            chrome_options.add_argument("--no-zygote")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--enable-unsafe-swiftshader")
            
            # Anti-detection options
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
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
            cookie_selectors = [
                "//button[contains(text(), 'Allow all cookies')]",  # Instagram specific
                "//button[contains(text(), 'Accept All')]",
                "//button[contains(text(), 'Accept')]",
                "//button[@data-testid='cookie-accept-all']"
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
            logger.info(f"Bot {self.bot_id}: Navigating to Instagram main page...")
            # Navigate to Instagram main page first to handle cookie consent
            self.driver.get("https://www.instagram.com/")
            time.sleep(3)

            logger.info(f"Bot {self.bot_id}: Handling cookie consent...")
            # Handle cookie consent dialog if present
            self._handle_cookie_consent()

            logger.info(f"Bot {self.bot_id}: Attempting login...")
            
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
            time.sleep(10)
            
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
                
                # Invalidate scraper since session data changed
                self.invalidate_scraper()
                
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
                
                # Invalidate scraper since session data changed
                self.invalidate_scraper()
                
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
    
    def get_scraper(self, target_user_id: str) -> InstagramAPIScraper:
        """
        Get or create persistent Instagram scraper for this bot.
        
        Args:
            target_user_id: Instagram user ID to analyze
            
        Returns:
            InstagramAPIScraper: Configured scraper instance
        """
        # Check if we need to create or update scraper
        if not self.scraper or not self.is_logged_in:
            bot_data = self.get_session_data()
            if not bot_data:
                raise ValueError("Bot session data not available")
            
            # Create new scraper with current session data
            self.scraper = InstagramAPIScraper(
                user_id=bot_data['user_id'],  # Bot's user ID
                csrf_token=bot_data['csrf_token'],
                x_ig_www_claim='',  # Can be extracted from session if needed
                x_web_session_id='',  # Can be extracted from session if needed
                cookies=f"sessionid={bot_data['session_id']}; csrftoken={bot_data['csrf_token']}"
            )
            
            logger.info(f"Bot {self.bot_id}: Created new Instagram scraper")
        
        # Update target user for this analysis
        self.scraper.user_id = target_user_id
        
        return self.scraper
    
    def invalidate_scraper(self):
        """Invalidate the scraper when session data changes."""
        if self.scraper:
            self.scraper = None
            logger.info(f"Bot {self.bot_id}: Scraper invalidated due to session change")
    
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
        
        # Cleanup scraper if it exists
        if self.scraper:
            self.scraper = None
            
        logger.info(f"Bot {self.bot_id}: Cleaned up")


class InstagramBotSlaveManager:
    """
    Manager for multiple Instagram bot slaves.
    Provides HTTP API for the main server to request bot sessions.
    Now includes job queue management for better resource utilization.
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
        
        self.bot_slaves = {}
        self.monitoring_thread = None
        self.is_monitoring = False
        
        # Job queue management
        self.job_queue = []  # Queue of pending jobs waiting for bots
        self.active_jobs = {}  # Currently running jobs {job_id: bot_id}
        self.completed_jobs = {}  # Recently completed jobs {job_id: job_data}
        self.job_processing_thread = None
        self.is_processing_jobs = False
        
        # Flask app for HTTP API
        self.app = Flask(__name__)
        self._setup_routes()
        
        # Load and initialize bot slaves from configuration
        self._initialize_bot_slaves()
        
        # Start job processing
        self._start_job_processing()
        
        # Start cleanup thread for old completed jobs
        self._start_cleanup_thread()
    
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
    
    def submit_job(self, job_data: dict) -> dict:
        """
        Submit a job to the queue system.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            Dict with job_id and queue position
        """
        job_id = job_data.get('job_id', str(uuid.uuid4()))
        job_data['job_id'] = job_id
        job_data['submitted_at'] = datetime.now().isoformat()
        job_data['status'] = 'queued'
        
        # Add to queue
        self.job_queue.append(job_data)
        
        logger.info(f"Job {job_id} submitted to queue (position: {len(self.job_queue)})")
        
        return {
            'job_id': job_id,
            'status': 'queued',
            'position_in_queue': len(self.job_queue),
            'estimated_wait_time': self._estimate_wait_time()
        }
    
    def _start_job_processing(self):
        """Start the job processing thread."""
        if self.is_processing_jobs:
            return
        
        self.is_processing_jobs = True
        self.job_processing_thread = threading.Thread(
            target=self._process_job_queue,
            daemon=True
        )
        self.job_processing_thread.start()
        logger.info("Started job processing thread")
    
    def _start_cleanup_thread(self):
        """Start the cleanup thread for old completed jobs."""
        cleanup_thread = threading.Thread(
            target=self._cleanup_old_jobs,
            daemon=True
        )
        cleanup_thread.start()
        logger.info("Started job cleanup thread")
    
    def _cleanup_old_jobs(self):
        """Clean up old completed jobs to prevent memory buildup."""
        while True:
            try:
                # Clean up jobs older than 1 hour
                cutoff_time = datetime.now() - timedelta(hours=1)
                jobs_to_remove = []
                
                for job_id, job_data in self.completed_jobs.items():
                    completed_at = job_data.get('completed_at')
                    if completed_at:
                        try:
                            job_time = datetime.fromisoformat(completed_at)
                            if job_time < cutoff_time:
                                jobs_to_remove.append(job_id)
                        except:
                            # If we can't parse the date, remove it
                            jobs_to_remove.append(job_id)
                
                # Remove old jobs
                for job_id in jobs_to_remove:
                    del self.completed_jobs[job_id]
                
                if jobs_to_remove:
                    logger.info(f"Cleaned up {len(jobs_to_remove)} old completed jobs")
                
                # Sleep for 30 minutes before next cleanup
                time.sleep(1800)
                
            except Exception as e:
                logger.error(f"Error in job cleanup: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    def _process_job_queue(self):
        """Process jobs from the queue when bots become available."""
        while self.is_processing_jobs:
            try:
                if self.job_queue:
                    # Try to assign a bot to the next job
                    bot_data = self.get_available_bot()
                    if bot_data:
                        # Get the next job from queue
                        job_data = self.job_queue.pop(0)
                        job_id = job_data['job_id']
                        
                        # Assign bot to job
                        self.active_jobs[job_id] = bot_data['bot_id']
                        
                        # Update job status
                        job_data['status'] = 'processing'
                        job_data['assigned_bot'] = bot_data['bot_id']
                        job_data['started_at'] = datetime.now().isoformat()
                        
                        # Start processing the job with the assigned bot
                        logger.info(f"Job {job_id} assigned to bot {bot_data['bot_id']}")
                        self._process_job_with_bot(job_data, bot_data)
                    else:
                        # No bots available, wait a bit
                        time.sleep(2)
                else:
                    # No jobs in queue, wait a bit
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in job processing: {e}")
                time.sleep(5)
    
    def _process_job_with_bot(self, job_data: dict, bot_data: dict):
        """
        Process a job using the assigned bot.
        This method performs the actual Instagram analysis.
        """
        job_id = job_data['job_id']
        target_user_id = job_data['target_user_id']
        job_type = job_data.get('job_type', 'analyze')
        
        try:
            logger.info(f"Processing job {job_id} with bot {bot_data['bot_id']}")
            
            # Get the bot slave instance
            bot_id = bot_data['bot_id']
            bot_slave = self.bot_slaves.get(bot_id)
            
            if not bot_slave:
                raise ValueError(f"Bot {bot_id} not found")
            
            # Mark bot as busy
            bot_slave.is_busy = True
            bot_slave.last_activity = datetime.now()
            
            # Perform Instagram analysis based on job type
            if job_type == 'analyze_not_following_back':
                result = self._analyze_not_following_back(bot_slave, target_user_id)
            else:  # Default to regular analyze
                previous_followers = job_data.get('previous_followers', [])
                result = self._analyze_followers(bot_slave, target_user_id, previous_followers)
            
            # Update job status with results
            job_data['status'] = 'completed'
            job_data['result'] = result
            job_data['completed_at'] = datetime.now().isoformat()
            
            # Store in completed jobs for status tracking
            self.completed_jobs[job_id] = job_data
            
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            job_data['status'] = 'failed'
            job_data['error'] = str(e)
            job_data['failed_at'] = datetime.now().isoformat()
            
            # Store failed job in completed jobs for status tracking
            self.completed_jobs[job_id] = job_data
        
        finally:
            # Release the bot
            if bot_id in self.bot_slaves:
                self.bot_slaves[bot_id].is_busy = False
                self.bot_slaves[bot_id].last_activity = datetime.now()
            
            # Remove from active jobs
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
    
    def _analyze_followers(self, bot_slave, target_user_id: str, previous_followers: list = None) -> dict:
        """Analyze followers using the bot slave."""
        try:
            logger.info(f"Analyzing followers for user {target_user_id}")
            
            # Get persistent scraper for this bot
            scraper = bot_slave.get_scraper(target_user_id)
            
            # Fetch data using bot account
            followers = scraper.extract_usernames(scraper.get_followers())
            following = scraper.extract_usernames(scraper.get_following())

            # Get bot data for result
            bot_data = bot_slave.get_session_data()

            # Format result
            result = {
                'target_user_id': target_user_id,
                'followers_count': len(followers),
                'following_count': len(following),
                'followers': followers,
                'following': following,
                'analysis_completed_at': datetime.now().isoformat(),
                'bot_account_used': bot_data['bot_id'],
                'analysis_type': 'followers'
            }
            
            # Compare with previous followers to find unfollowers
            if previous_followers:                
                previous_set = set(previous_followers)
                current_set = set(followers)
                unfollowers = list(current_set - previous_set)
                result['unfollowers'] = unfollowers
            
            logger.info(f"Follower analysis completed.")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing followers: {e}")
            raise
    
    def _analyze_not_following_back(self, bot_slave, target_user_id: str) -> dict:
        """Analyze users who don't follow back using the bot slave."""
        try:
            logger.info(f"Analyzing users who don't follow back for user {target_user_id}")
            
            # Get persistent scraper for this bot
            scraper = bot_slave.get_scraper(target_user_id)
            
            # Get bot data for result
            bot_data = bot_slave.get_session_data()
            
            # Fetch current followers
            followers = scraper.get_followers()
            following = scraper.get_following()
            not_following_back = self._find_non_follow_backs(
                scraper.extract_usernames(followers), 
                scraper.extract_usernames(following))
            
            # Format result
            result = {
                'target_user_id': target_user_id,
                'followers_count': len(followers),
                'not_following_back_count': len(not_following_back),
                'not_following_back': not_following_back,
                'analysis_completed_at': datetime.now().isoformat(),
                'bot_account_used': bot_data['bot_id'],
                'analysis_type': 'not_following_back'
            }
            
            logger.info(f"Not following back analysis completed: {len(not_following_back)} users found who don't follow back")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing users who don't follow back: {e}")
            raise
    
    def _find_non_follow_backs(self, followers: list, following: list) -> list:
        """Find users who don't follow back"""
        follower_set = set(followers)
        following_set = set(following)
        not_following_back = list(following_set - follower_set)
        
        return not_following_back
    
    def get_job_status(self, job_id: str) -> Optional[dict]:
        """Get the status of a specific job."""
        logger.debug(f"Getting status for job {job_id}")
        logger.debug(f"Queue length: {len(self.job_queue)}, Active jobs: {len(self.active_jobs)}, Completed jobs: {len(self.completed_jobs)}")
        
        # Check if job is in queue
        for job in self.job_queue:
            if job['job_id'] == job_id:
                logger.debug(f"Job {job_id} found in queue")
                return {
                    'job_id': job_id,
                    'status': 'queued',
                    'position_in_queue': self.job_queue.index(job) + 1,
                    'estimated_wait_time': self._estimate_wait_time(),
                    'message': 'Job is waiting in queue for available bot'
                }
        
        # Check if job is active
        if job_id in self.active_jobs:
            logger.debug(f"Job {job_id} found in active jobs")
            return {
                'job_id': job_id,
                'status': 'processing',
                'assigned_bot': self.active_jobs[job_id],
                'position_in_queue': 0,
                'message': 'Job is currently being processed by bot'
            }
        
        # Check if job is completed
        if job_id in self.completed_jobs:
            job_data = self.completed_jobs[job_id]
            logger.debug(f"Job {job_id} found in completed jobs with status: {job_data.get('status')}")
            return {
                'job_id': job_id,
                'status': job_data.get('status', 'completed'),
                'result': job_data.get('result'),
                'error': job_data.get('error'),
                'completed_at': job_data.get('completed_at'),
                'message': 'Job has been completed'
            }
        
        logger.debug(f"Job {job_id} not found anywhere")
        return None
    
    def complete_job(self, job_id: str):
        """Mark a job as completed and release the bot."""
        if job_id in self.active_jobs:
            bot_id = self.active_jobs[job_id]
            self.release_bot(bot_id)
            del self.active_jobs[job_id]
            logger.info(f"Job {job_id} completed, bot {bot_id} released")
    
    def _estimate_wait_time(self) -> int:
        """Estimate wait time in seconds based on queue length and bot availability."""
        if not self.job_queue:
            return 0
        
        # Simple estimation: assume each job takes 5 minutes on average
        avg_job_time = 300  # 5 minutes
        available_bots = len([b for b in self.bot_slaves.values() if not b.is_busy and b.is_healthy()])
        
        if available_bots == 0:
            # If no bots available, estimate based on queue length
            return len(self.job_queue) * avg_job_time
        else:
            # If bots available, estimate based on queue position
            return (len(self.job_queue) - 1) * avg_job_time // available_bots
    
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
            """Request an available bot session (legacy endpoint)."""
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
        
        @self.app.route('/api/job/submit', methods=['POST'])
        def submit_job():
            """Submit a job to the queue system."""
            try:
                data = request.json
                if not data:
                    return jsonify({'error': 'No job data provided'}), 400
                
                result = self.submit_job(data)
                return jsonify(result)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/job/status/<job_id>', methods=['GET'])
        def get_job_status_endpoint(job_id):
            """Get the status of a specific job."""
            try:
                status = self.get_job_status(job_id)
                if status:
                    return jsonify(status)
                else:
                    # Job not found - return 200 with appropriate status
                    return jsonify({
                        'job_id': job_id,
                        'status': 'not_found',
                        'message': 'Job not found in queue or completed jobs'
                    }), 200
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/job/complete', methods=['POST'])
        def complete_job():
            """Mark a job as completed."""
            try:
                data = request.json
                if not data or 'job_id' not in data:
                    return jsonify({'error': 'job_id required'}), 400
                
                self.complete_job(data['job_id'])
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/queue/status', methods=['GET'])
        def get_queue_status():
            """Get the current queue status."""
            try:
                return jsonify({
                    'queue_length': len(self.job_queue),
                    'active_jobs': len(self.active_jobs),
                    'available_bots': len([b for b in self.bot_slaves.values() if not b.is_busy and b.is_healthy()]),
                    'total_bots': len(self.bot_slaves)
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
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
        self.is_processing_jobs = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        if self.job_processing_thread:
            self.job_processing_thread.join(timeout=5)
        
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
