#!/usr/bin/env python3
"""
Instagram Follower Analysis - Complete Workflow Runner
Runs all three steps in sequence: curl formatting → data scraping → follower comparison
"""

import os
import sys
import subprocess
import time

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"[RUNNING] {description}")
    print(f"{'='*60}")
    print(f"Running: {command}")
    print()
    
    try:
        # Run command with real-time output (no capture_output to avoid hanging)
        result = subprocess.run(command, shell=True)
        
        if result.returncode == 0:
            print(f"\n[SUCCESS] {description} completed successfully!")
            return True
        else:
            print(f"\n[ERROR] {description} failed with exit code {result.returncode}!")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Error running {description}: {e}")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists and return status."""
    if os.path.exists(filepath):
        print(f"[SUCCESS] {description} found: {filepath}")
        return True
    else:
        print(f"[ERROR] {description} not found: {filepath}")
        return False

def main():
    """Main workflow runner."""
    print("Instagram Follower Analysis - Complete Workflow")
    print("=" * 60)
    print("This script will run all three steps automatically:")
    print("1. Format curl command from curl_input.txt")
    print("2. Scrape Instagram data")
    print("3. Compare followers and generate analysis")
    print()
    
    # Check prerequisites
    print("[CHECKING] Checking prerequisites...")
    if not check_file_exists("curl_input.txt", "Input curl file"):
        print("\n[ERROR] Please create 'curl_input.txt' with your Instagram curl command first!")
        print("See README.md for instructions on how to get your curl command.")
        return False
    
    if not check_file_exists("save_curl_and_run.py", "Curl formatter script"):
        print("\n[ERROR] Missing 'save_curl_and_run.py' script!")
        return False
    
    if not check_file_exists("instagram_api_scraper.py", "Instagram scraper script"):
        print("\n[ERROR] Missing 'instagram_api_scraper.py' script!")
        return False
    
    if not check_file_exists("compare_followers.py", "Follower comparison script"):
        print("\n[ERROR] Missing 'compare_followers.py' script!")
        return False
    
    print("\n[SUCCESS] All prerequisites found!")
    
    # Step 1: Format curl command
    print("\n" + "="*60)
    print("STEP 1: Formatting curl command...")
    print("="*60)
    
    if not run_command("python save_curl_and_run.py", "Curl command formatting"):
        print("\n[ERROR] Step 1 failed! Cannot continue.")
        return False
    
    # Check if instagram_curl.txt was created
    if not check_file_exists("instagram_curl.txt", "Formatted curl file"):
        print("\n[ERROR] Step 1 failed! Formatted curl file not created.")
        return False
    
    # Step 2: Scrape Instagram data
    print("\n" + "="*60)
    print("STEP 2: Scraping Instagram data...")
    print("="*60)
    print("NOTE: This step can take several minutes depending on the number of users.")
    print("The script will show real-time progress from the Instagram scraper.")
    print()
    
    # Ask user for scraping preferences
    print("Scraping Options:")
    print("1. Full scrape (all followers/following)")
    print("2. Limited scrape (for testing)")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == "2":
        max_count = input("Enter maximum number of users to collect (e.g., 100): ").strip()
        try:
            max_count = int(max_count)
            scraper_command = f"python instagram_api_scraper.py --curl-file instagram_curl.txt --max-count {max_count}"
            print(f"\n[INFO] Limited scrape selected: maximum {max_count} users")
        except ValueError:
            print("Invalid number, using default limited scrape (100 users)")
            scraper_command = "python instagram_api_scraper.py --curl-file instagram_curl.txt --max-count 100"
            print("\n[INFO] Limited scrape selected: maximum 100 users")
    else:
        scraper_command = "python instagram_api_scraper.py --curl-file instagram_curl.txt"
        print("\n[INFO] Full scrape selected: collecting all users")
    
    print("\n[INFO] Starting Instagram scraper... This may take several minutes.")
    print("You'll see real-time progress below:")
    print("-" * 40)
    
    if not run_command(scraper_command, "Instagram data scraping"):
        print("\n[ERROR] Step 2 failed! Cannot continue.")
        return False
    
    # Check if data files were created
    if not check_file_exists("instagram_data/followers.txt", "Followers data"):
        print("\n[ERROR] Step 2 failed! Followers data not created.")
        return False
    
    if not check_file_exists("instagram_data/following.txt", "Following data"):
        print("\n[ERROR] Step 2 failed! Following data not created.")
        return False
    
    # Step 3: Compare followers
    print("\n" + "="*60)
    print("STEP 3: Comparing followers and generating analysis...")
    print("="*60)
    
    if not run_command("python compare_followers.py", "Follower comparison"):
        print("\n[ERROR] Step 3 failed!")
        return False
    
    # Check final output
    if not check_file_exists("instagram_data/users_not_following_back.txt", "Analysis results"):
        print("\n[ERROR] Step 3 failed! Analysis results not created.")
        return False
    
    # Success summary
    print("\n" + "="*60)
    print("ALL STEPS COMPLETED SUCCESSFULLY!")
    print("="*60)
    
    # Show file sizes and basic stats
    try:
        with open("instagram_data/followers.txt", "r") as f:
            follower_count = len(f.readlines())
        
        with open("instagram_data/following.txt", "r") as f:
            following_count = len(f.readlines())
        
        with open("instagram_data/users_not_following_back.txt", "r") as f:
            not_following_count = len(f.readlines())
        
        print(f"\nFinal Results:")
        print(f"   • Followers collected: {follower_count}")
        print(f"   • Following collected: {following_count}")
        print(f"   • Users not following back: {not_following_count}")
        
    except Exception as e:
        print(f"Could not read result statistics: {e}")
    
    print(f"\nYour data is saved in the 'instagram_data/' directory")
    print(f"Analysis results: 'instagram_data/users_not_following_back.txt'")
    print(f"\nWorkflow completed successfully!")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n[SUCCESS] All done! You can now review your results.")
        else:
            print("\n[ERROR] Workflow failed. Please check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Workflow interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1) 