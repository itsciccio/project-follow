#!/usr/bin/env python3
"""
Helper script to read curl command from a text file and save it properly formatted
"""

def read_and_format_curl(input_file='curl_input.txt'):
    """Read curl command from input file and save it properly formatted."""
    
    try:
        # Read the curl command from input file
        with open(input_file, 'r', encoding='utf-8') as f:
            curl_command = f.read().strip()
        
        print(f"[SUCCESS] Read curl command from '{input_file}'")
        
        # Clean up the curl command by removing Windows batch escape characters
        # Replace ^" with " and ^& with & and ^% with %
        cleaned_curl = curl_command.replace('^"', '"').replace('^&', '&').replace('^%', '%')
        
        # Also clean up any remaining ^ characters that might be used as escapes
        cleaned_curl = cleaned_curl.replace('^\\', '\\').replace('^', '')
        
        # Save the cleaned curl command
        with open('instagram_curl.txt', 'w', encoding='utf-8') as f:
            f.write(cleaned_curl)
        
        print("[SUCCESS] Curl command cleaned and saved to 'instagram_curl.txt'")
        print("Now you can run the scraper with:")
        print("python instagram_api_scraper.py --curl-file instagram_curl.txt")
        
    except FileNotFoundError:
        print(f"[ERROR] Input file '{input_file}' not found.")
        print(f"Please create '{input_file}' with your curl command and run this script again.")
        print("\nExample of what to put in curl_input.txt:")
        print("curl ^\"https://www.instagram.com/api/v1/friendships/YOUR_USER_ID/followers/...^\" ^")
        print("-H ^\"x-csrftoken: YOUR_TOKEN^\" ^")
        print("-b ^\"your_cookies_here^\"")
        
    except Exception as e:
        print(f"[ERROR] Error processing curl command: {e}")

def main():
    """Main function to read and format curl command."""
    
    print("Instagram Curl Command Reader & Formatter")
    print("=" * 40)
    print()
    
    # Check if input file exists
    import os
    input_file = 'curl_input.txt'
    
    if not os.path.exists(input_file):
        print(f"[ERROR] Input file '{input_file}' not found.")
        print()
        print("To use this script:")
        print("1. Copy your curl command from Instagram")
        print("2. Paste it into a file called 'curl_input.txt'")
        print("3. Run this script again")
        print()
        print("The script will automatically clean up the formatting and save it to 'instagram_curl.txt'")
        return
    
    # Process the curl command
    read_and_format_curl(input_file)

if __name__ == "__main__":
    main()     