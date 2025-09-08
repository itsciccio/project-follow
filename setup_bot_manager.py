#!/usr/bin/env python3
"""
Setup Script for Instagram Bot Slaves
Interactive script to set up bot slaves for the slave manager.
"""

import os
import sys
from instagram_bot_slave_manager import InstagramBotSlaveManager

def print_banner():
    """Print setup banner."""
    print("=" * 60)
    print("Instagram Bot Slave Setup")
    print("=" * 60)
    print("This script will help you set up bot slaves for the slave manager.")
    print("Bot slaves maintain persistent Instagram sessions and provide")
    print("session data to the main API server.")
    print("=" * 60)

def add_bot_slave(manager):
    """Add a bot slave to the manager."""
    print("\n🤖 ADDING BOT SLAVE:")
    print("-" * 20)
    
    bot_id = input("Enter bot ID (e.g., 'bot_1'): ").strip()
    if not bot_id:
        print("❌ Bot ID is required!")
        return False
    
    username = input("Enter Instagram username: ").strip()
    if not username:
        print("❌ Username is required!")
        return False
    
    password = input("Enter Instagram password: ").strip()
    if not password:
        print("❌ Password is required!")
        return False
    
    print(f"\nAdding bot slave {bot_id}...")
    success = manager.add_bot_slave(bot_id, username, password)
    
    if success:
        print(f"✅ Bot slave {bot_id} added and logged in successfully!")
        return True
    else:
        print(f"❌ Failed to add bot slave {bot_id}")
        return False

def show_bot_status(manager):
    """Show status of all bot slaves."""
    print("\n📊 BOT SLAVE STATUS:")
    print("-" * 25)
    
    if not manager.bot_slaves:
        print("No bot slaves configured.")
        return
    
    for bot_id, bot_slave in manager.bot_slaves.items():
        status = "🟢 Healthy" if bot_slave.is_healthy() else "🔴 Unhealthy"
        busy = "🔒 Busy" if bot_slave.is_busy else "🆓 Available"
        logged_in = "✅ Logged in" if bot_slave.is_logged_in else "❌ Not logged in"
        
        print(f"Bot {bot_id}:")
        print(f"  Status: {status}")
        print(f"  Availability: {busy}")
        print(f"  Login: {logged_in}")
        if bot_slave.last_activity:
            print(f"  Last Activity: {bot_slave.last_activity}")
        print()

def main():
    """Main setup function."""
    print_banner()
    
    # Initialize bot slave manager
    print("🔧 INITIALIZING BOT SLAVE MANAGER:")
    print("-" * 35)
    manager = InstagramBotSlaveManager(port=5001)
    print("✅ Bot slave manager initialized")
    
    try:
        while True:
            print("\n📋 OPTIONS:")
            print("1. Add bot slave")
            print("2. Show bot status")
            print("3. Start slave manager server")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                add_bot_slave(manager)
            elif choice == "2":
                show_bot_status(manager)
            elif choice == "3":
                print("\n🚀 STARTING BOT SLAVE MANAGER:")
                print("-" * 30)
                print("The bot slave manager will start on port 5001")
                print("Make sure to start the main API server on port 5000")
                print("Press Ctrl+C to stop the server")
                print()
                manager.run()
                break
            elif choice == "4":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
    finally:
        manager.cleanup()

if __name__ == "__main__":
    main()
