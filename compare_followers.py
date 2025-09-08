#!/usr/bin/env python3
"""
Compare followers.txt and following.txt to find users who don't follow back.
Outputs the results to a text file.
"""

def load_usernames(filename):
    """Load usernames from a text file (one per line)."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            # Remove empty lines and whitespace
            usernames = [line.strip() for line in f if line.strip()]
        return set(usernames)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return set()
    except Exception as e:
        print(f"Error reading '{filename}': {e}")
        return set()

def compare_followers_following(followers_file, following_file, output_file):
    """Compare followers and following lists and save results."""
    
    print("Loading followers and following data...")
    
    # Load the data
    followers = load_usernames(followers_file)
    following = load_usernames(following_file)
    
    if not followers:
        print("No followers data loaded. Exiting.")
        return
    
    if not following:
        print("No following data loaded. Exiting.")
        return
    
    print(f"Loaded {len(followers)} followers")
    print(f"Loaded {len(following)} following")
    print()
    
    # Find users who don't follow back
    not_following_back = following - followers
    
    # Find mutual followers
    mutual_followers = followers.intersection(following)
    
    # Find users you don't follow back
    you_dont_follow_back = followers - following
    
    # Display summary
    print("=" * 60)
    print("FOLLOWER ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Total Followers: {len(followers)}")
    print(f"Total Following: {len(following)}")
    print(f"Mutual Followers: {len(mutual_followers)}")
    print(f"Users Who Don't Follow Back: {len(not_following_back)}")
    print(f"Users You Don't Follow Back: {len(you_dont_follow_back)}")
    print()
    
    # Calculate percentages
    if followers:
        mutual_percentage = (len(mutual_followers) / len(followers)) * 100
        print(f"Mutual Follow Rate: {mutual_percentage:.1f}%")
        print(f"One-way Following Rate: {100 - mutual_percentage:.1f}%")
        print()
    
    # Save the list of users who don't follow back (always create the file)
    print(f"Saving {len(not_following_back)} users who don't follow back to '{output_file}'...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        if not_following_back:
            # Sort alphabetically and write one username per line
            for username in sorted(not_following_back):
                f.write(f"{username}\n")
        # If empty, create empty file (no content)
    
    print(f"✅ List saved to '{output_file}'")
    print()
    
    if not_following_back:
        # Show first 20 users as preview
        print("First 20 users who don't follow back:")
        print("-" * 40)
        for i, username in enumerate(sorted(not_following_back)[:20]):
            print(f"{i+1:2d}. {username}")
        
        if len(not_following_back) > 20:
            print(f"... and {len(not_following_back) - 20} more")
    else:
        print("✅ All users you follow also follow you back!")
    
    print()
    print("=" * 60)
    print("Analysis complete!")
    print(f"Results saved to: {output_file}")

def main():
    """Main function to run the comparison."""
    
    # File paths
    followers_file = "instagram_data/followers.txt"
    following_file = "instagram_data/following.txt"
    output_file = "instagram_data/users_not_following_back.txt"
    
    print("Instagram Follower Comparison Tool")
    print("=" * 40)
    print()
    
    # Check if files exist
    import os
    if not os.path.exists(followers_file):
        print(f"❌ Error: '{followers_file}' not found in current directory")
        print("Please make sure both 'followers.txt' and 'following.txt' are in the current directory.")
        return
    
    if not os.path.exists(following_file):
        print(f"❌ Error: '{following_file}' not found in current directory")
        print("Please make sure both 'followers.txt' and 'following.txt' are in the current directory.")
        return
    
    print(f"📁 Found followers file: {followers_file}")
    print(f"📁 Found following file: {following_file}")
    print(f"📝 Output will be saved to: {output_file}")
    print()
    
    # Run the comparison
    compare_followers_following(followers_file, following_file, output_file)

if __name__ == "__main__":
    main() 