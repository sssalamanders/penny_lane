#!/usr/bin/env python3
"""
Penny Lane - Main Script
Handles setup, environment activation, then runs the bot module

Usage:
  python pnny.py           # Run bot (auto-setup if needed)
  python pnny.py --check   # Self-check then run
  python pnny.py --setup   # Force setup mode
"""

import sys
import platform
import logging
import time
import os
import subprocess
import getpass
from pathlib import Path

def activate_venv():
    """Activate the virtual environment by modifying sys.path"""
    venv_path = Path("venv")
    if not venv_path.exists():
        return False
        
    if platform.system() == "Windows":
        site_packages_glob = "venv/Lib/site-packages"
    else:
        # More reliable way to find site-packages
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        site_packages_glob = f"venv/lib/python{python_version}/site-packages"
    
    site_packages_path = Path(site_packages_glob)
    
    if site_packages_path.exists():
        # Add to beginning of sys.path
        sys.path.insert(0, str(site_packages_path.absolute()))
        print(f"✅ Virtual environment activated: {site_packages_path}")
        return True
    else:
        print(f"❌ Site-packages not found at: {site_packages_path}")
        return False

def validate_bot_token(token):
    """Validate bot token format for security"""
    if not token or not isinstance(token, str):
        return False
    
    # Basic format validation for Telegram bot tokens
    if ':' not in token:
        return False
        
    parts = token.split(':')
    if len(parts) != 2:
        return False
    
    # First part should be bot ID (numeric)
    bot_id, auth_token = parts
    if not bot_id.isdigit() or len(bot_id) < 8:
        return False
        
    # Second part should be auth token (alphanumeric + some special chars)
    if len(auth_token) < 20:
        return False
    
    # Bot IDs typically start with certain digits
#    if not bot_id.startswith(('1', '2', '5', '6', '7')):
 #       return False
        
    return True

def first_time_setup():
    """Handle first-time setup: venv, dependencies, token"""
    print("🎸 Penny Lane First-Time Setup")
    print("=" * 40)
    
    # Check Python version
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ required!")
        return False
    
    # Create venv if needed
    venv_path = Path("venv")
    if not venv_path.exists():
        print("Creating virtual environment...")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print("✅ Virtual environment created")
        except subprocess.CalledProcessError:
            print("❌ Failed to create virtual environment")
            return False
    
    # Install requirements
    print("Installing requirements...")
    if platform.system() == "Windows":
        pip_cmd = ["venv\\Scripts\\python.exe", "-m", "pip"]
    else:
        pip_cmd = ["venv/bin/python", "-m", "pip"]
    
    try:
        subprocess.run(pip_cmd + ["install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        subprocess.run(pip_cmd + ["install", "python-telegram-bot==21.0.1"], 
                      check=True, capture_output=True)
        print("✅ Requirements installed")
        
        # Now activate the venv for this session
        activate_venv()
        
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        return False
    
    # Get bot token - Check environment variable first
    env_file = Path(".env")
    if not env_file.exists():
        print("\n🔑 Bot Token Setup")
        
        # First, check if token is available via environment variable (for Railway/Docker)
        token = os.environ.get("PENNY_BOT_TOKEN")
        
        if token:
            print("✅ Bot token found in environment variables")
            # Enhanced token validation
            if not validate_bot_token(token):
                print("❌ Invalid bot token format in environment variable")
                print("   Token should be in format: BOTID:AUTH_TOKEN")
                return False
            print("✅ Token format validated")
        else:
            # Check if we're in an interactive environment
            if not sys.stdin.isatty():
                print("❌ No interactive terminal available and no PENNY_BOT_TOKEN environment variable set")
                print("For Railway/Docker deployments:")
                print("1. Set PENNY_BOT_TOKEN environment variable in your Railway dashboard")
                print("2. Mark it as a 'secret' variable (lock icon)")
                print("3. Or run locally with: export PENNY_BOT_TOKEN=your_token_here")
                return False
            
            # Interactive mode - prompt for token
            print("Get your token from @BotFather:")
            print("1. Message @BotFather on Telegram")
            print("2. Send: /newbot")
            print("3. Follow prompts")
            print("4. Copy the token")
            
            while True:
                try:
                    token = getpass.getpass("🔐 Paste token (hidden): ").strip()
                    
                    if not validate_bot_token(token):
                        print("❌ Invalid token format. Token should look like: 123456789:ABCdefGHI...")
                        print("Try again or press Ctrl+C to cancel.")
                        continue
                        
                    masked = f"{token[:12]}...{token[-8:]}"
                    print(f"Token preview: {masked}")
                    confirm = input("Save this token? (Y/n): ").lower()
                    
                    if confirm in ('', 'y', 'yes'):
                        break
                        
                except KeyboardInterrupt:
                    print("\nSetup cancelled")
                    return False
                except Exception as e:
                    print(f"❌ Error during token input: {e}")
                    return False
        
        # Save token to .env file (if we got it interactively)
        if not os.environ.get("PENNY_BOT_TOKEN"):
            try:
                with open(".env", "w") as f:
                    f.write(f"PENNY_BOT_TOKEN={token}\n")
                    f.write("PENNY_DEBUG=false\n")
                os.chmod(".env", 0o600)  # Secure file permissions
                print("✅ Token saved securely with restricted permissions")
            except Exception as e:
                print(f"❌ Failed to save token: {e}")
                return False
        else:
            # For environment variable case, create a minimal .env for consistency
            try:
                with open(".env", "w") as f:
                    f.write("PENNY_DEBUG=false\n")
                os.chmod(".env", 0o600)
                print("✅ Configuration initialized")
            except Exception as e:
                print(f"⚠️  Warning: Could not create .env file: {e}")
    
    print("\n🎉 Setup complete!")
    print("Test: Message your bot /bandaid privately, then /bandaid in groups")
    return True

def self_check():
    """Built-in self-check functionality"""
    print("🎸 Penny Lane Self-Check")
    print("=" * 30)
    
    # Check environment
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file missing - run with --setup")
        return False
    print("✅ Configuration file found")
    
    # Load and check token
    token = os.getenv("PENNY_BOT_TOKEN")
    if not token:
        try:
            with open(env_file) as f:
                for line in f:
                    if line.startswith("PENNY_BOT_TOKEN="):
                        token = line.split("=", 1)[1].strip()
                        os.environ["PENNY_BOT_TOKEN"] = token
                        break
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
            return False
    
    if not validate_bot_token(token):
        print("❌ Bot token not configured or invalid format")
        return False
    
    masked = f"{token[:12]}...{token[-8:]}"
    print(f"✅ Bot token configured and validated: {masked}")
    
    # Check imports (only after venv is activated)
    try:
        import telegram
        from telegram.ext import Application
        print("✅ Telegram library available")
    except ImportError:
        print("❌ Telegram library missing - run with --setup")
        return False
    
    # Check GIF
    gif_path = Path("success.gif")
    if gif_path.exists():
        size = gif_path.stat().st_size
        print(f"🎬 Almost Famous GIF ready ({size:,} bytes)")
    else:
        print("⚠️  success.gif not found (will use text-only)")
    
    print("\n🚀 Ready to rock! Starting bot...")
    return True

def main():
    """Main function - handles setup then runs bot"""
    # Handle command line arguments
    setup_mode = "--setup" in sys.argv
    check_mode = "--check" in sys.argv
    
    # Force setup mode
    if setup_mode:
        success = first_time_setup()
        if not success:
            return 1
        # Continue to run bot after setup
    
    # Check if first-time setup is needed
    env_file = Path(".env")
    venv_path = Path("venv")
    
    if not env_file.exists() or not venv_path.exists():
        print("🎸 First time running Penny Lane!")
        print("Let's get you set up...")
        print()
        if not first_time_setup():
            return 1
        print("\n🚀 Now starting the bot...")
        print()
    else:
        # Activate venv for existing installations
        if not activate_venv():
            print("❌ Failed to activate virtual environment")
            print("   Run with --setup to recreate")
            return 1
    
    # Load environment variables
    if env_file.exists():
        try:
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key] = value
        except Exception as e:
            print(f"⚠️  Warning: Error reading .env file: {e}")
    
    # Self-check mode
    if check_mode:
        if not self_check():
            print("Self-check failed. Run with --setup to fix issues.")
            return 1
        print()
    
    # Verify token is available and valid
    token = os.getenv("PENNY_BOT_TOKEN")
    if not validate_bot_token(token):
        print("❌ Bot token not configured or invalid")
        print("   Run: python pnny.py --setup")
        return 1
    
    # Import and run the bot module (only after venv is activated)
    print("🔗 Loading bot module...")
    try:
        # Debug: Show current sys.path
        print(f"Current Python path: {sys.path[0] if sys.path else 'empty'}")
        
        import group_id
        print("✅ Bot module loaded successfully")
        return group_id.run_bot(token)
    except ImportError as e:
        print(f"❌ Failed to import bot module: {e}")
        print("   Debug info:")
        print(f"   - group_id.py exists: {Path('group_id.py').exists()}")
        print(f"   - venv exists: {Path('venv').exists()}")
        print(f"   - Current working directory: {Path.cwd()}")
        
        # Try to test telegram import directly
        try:
            import telegram
            print("   - telegram import: SUCCESS (shouldn't happen)")
        except ImportError:
            print("   - telegram import: FAILED (expected)")
            
        return 1

if __name__ == "__main__":
    sys.exit(main())
