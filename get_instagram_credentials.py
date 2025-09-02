#!/usr/bin/env python3
"""
Instagram Credentials Input - Ultra Simplified
Only asks for session_id and csrf_token, extracts user_id automatically
"""

import os

def extract_user_id_from_session_id(session_id):
    """Extract user ID from session ID (everything before the first %)"""
    try:
        user_id = session_id.split('%')[0]
        if user_id.isdigit():
            return user_id
        else:
            return None
    except:
        return None

def get_essential_credentials():
    """Get only the 2 essential Instagram credentials from user."""
    print("Instagram Credentials Input - Ultra Simplified")
    print("=" * 50)
    print("This tool only needs 2 essential values from you.")
    print("User ID is automatically extracted from your session ID.")
    print()
    
    credentials = {}
    
    print("🔑 ESSENTIAL VALUES (Required):")
    print("-" * 30)
    
    # CSRF Token
    while True:
        csrf_token = input("Enter CSRF Token: ").strip()
        if csrf_token:
            credentials['csrf_token'] = csrf_token
            break
        else:
            print("❌ CSRF Token is required. Try again.")
    
    # Session ID
    while True:
        session_id = input("Enter Session ID: ").strip()
        if session_id:
            # Extract user ID from session ID
            user_id = extract_user_id_from_session_id(session_id)
            if user_id:
                credentials['session_id'] = session_id
                credentials['user_id'] = user_id
                print(f"✅ User ID extracted: {user_id}")
                break
            else:
                print("❌ Could not extract User ID from Session ID. Please check the format.")
                print("   Expected format: 410199922%3AA9IF5q64rDBksn%3A9%3AAYfA7EvS4XvKzqbub0EKcaiMW2w61TJFm8ojtHl2xg")
        else:
            print("❌ Session ID is required. Try again.")
    
    return credentials

def build_complete_curl_request(credentials):
    """Build a complete curl request with all standard headers."""
    
    # Base URL
    base_url = f"https://www.instagram.com/api/v1/friendships/{credentials['user_id']}/followers/?count=12&search_surface=follow_list_page"
    
    # Essential cookies (these are the only values that change between users)
    cookies = f"csrf_token={credentials['csrf_token']}; sessionid={credentials['session_id']}; ds_user_id={credentials['user_id']}"
    
    # Standard headers (these are identical for all users)
    headers = [
        '-H "accept: */*"',
        '-H "accept-language: en-US,en;q=0.9"',
        '-H "priority: u=1, i"',
        '-H "sec-ch-prefers-color-scheme: dark"',
        '-H "sec-ch-ua: \\"Not;A=Brand\\";v=\\"99\\", \\"Google Chrome\\";v=\\"139\\", \\"Chromium\\";v=\\"139\\""',
        '-H "sec-ch-ua-full-version-list: \\"Not;A=Brand\\";v=\\"99.0.0.0\\", \\"Google Chrome\\";v=\\"139.0.7258.155\\", \\"Chromium\\";v=\\"139.0.7258.155\\""',
        '-H "sec-ch-ua-mobile: ?0"',
        '-H "sec-ch-ua-model: \\"\\""',
        '-H "sec-ch-ua-platform: \\"Windows\\""',
        '-H "sec-ch-ua-platform-version: \\"19.0.0\\""',
        '-H "sec-fetch-dest: empty"',
        '-H "sec-fetch-mode: cors"',
        '-H "sec-fetch-site: same-origin"',
        '-H "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"',
        '-H "x-asbd-id: 359341"',
        '-H "x-csrftoken: {csrf_token}"',
        '-H "x-ig-app-id: 936619743392459"',
        '-H "x-ig-www-claim: hmac.AR2_1qTT6hODNI09V_iw11cR_ykq2CmtbRLYlh6bv-9TqsgH"',
        '-H "x-requested-with: XMLHttpRequest"',
        '-H "x-web-session-id: r6j2q9:srvxcp:2d1itp"'
    ]
    
    # Build the complete curl command
    curl_command = f'curl "{base_url}" \\\n'
    curl_command += f'  -b "{cookies}" \\\n'
    
    for header in headers:
        # Replace the csrf_token placeholder in the x-csrftoken header
        if '{csrf_token}' in header:
            header = header.replace('{csrf_token}', credentials['csrf_token'])
        curl_command += f'  {header} \\\n'
    
    # Remove the last backslash and newline
    curl_command = curl_command.rstrip(' \\\n')
    
    return curl_command

def save_credentials(credentials, curl_command):
    """Save the generated curl command."""
    
    # Save the complete curl command
    with open('instagram_curl.txt', 'w', encoding='utf-8') as f:
        f.write(curl_command)
    
    print("\n✅ Credentials saved successfully!")
    print(f"📄 Complete curl command: instagram_curl.txt")
    print(f"🔍 Extracted User ID: {credentials['user_id']}")
    print("\n🚀 You can now run the scraper with:")
    print("python instagram_api_scraper.py --curl-file instagram_curl.txt")

def show_help():
    """Show help on how to find the required values."""
    print("\n📖 HOW TO FIND THESE VALUES:")
    print("=" * 40)
    print("1. Go to Instagram → Your Profile → Followers")
    print("2. Open Developer Tools (F12) → Application tab")
    print("3. Go to Cookies → instagram.com")
    print("4. Look for these two cookies:")
    print()
    print("🔍 REQUIRED COOKIES:")
    print("- csrf_token: Your CSRF token")
    print("- sessionid: Your session ID (contains your user ID)")
    print()
    print("💡 TIP: The session ID format is:")
    print("   USER_ID%3A...rest of session data...")
    print("   Example: 410199922%3AA9IF5q64rDBksn%3A9%3AAYfA7EvS4XvKzqbub0EKcaiMW2w61TJFm8ojtHl2xg")
    print("   User ID: 410199922 (everything before the first %)")
    print()
    print("🔒 SECURITY: These values are sensitive - never share them!")

def main():
    """Main function."""
    print("Instagram Credentials Input Tool")
    print("=" * 40)
    print()
    
    # Check if user wants help
    help_choice = input("Do you need help finding these values? (y/n): ").strip().lower()
    if help_choice in ['y', 'yes']:
        show_help()
        input("\nPress Enter to continue...")
        print("\n" + "="*50 + "\n")
    
    try:
        # Get only the 2 essential credentials
        credentials = get_essential_credentials()
        
        # Generate the complete curl command
        curl_command = build_complete_curl_request(credentials)
        
        # Show preview
        print("\n📋 GENERATED CURL COMMAND PREVIEW:")
        print("-" * 40)
        print(curl_command)
        print("-" * 40)
        
        # Confirm with user
        confirm = input("\nDoes this look correct? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            save_credentials(credentials, curl_command)
        else:
            print("❌ Credentials not saved. Please run the tool again.")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 