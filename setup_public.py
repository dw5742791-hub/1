#!/usr/bin/env python3
"""
Public Access Setup for CMS
Automatically sets up ngrok tunnel for public access
"""

import os
import subprocess
import sys
import time
from pathlib import Path

def print_header():
    print("\n" + "="*70)
    print("🌐 CMS - PUBLIC ACCESS SETUP")
    print("="*70 + "\n")

def check_dependencies():
    """Check and install required dependencies"""
    print("📦 Checking dependencies...\n")
    
    # Check Python
    try:
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
        print(f"✓ Python: {result.stdout.strip()}")
    except:
        print("✗ Python not found")
        return False
    
    # Check if Flask is installed
    try:
        import flask
        print(f"✓ Flask: {flask.__version__}")
    except:
        print("! Flask not installed - installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      capture_output=True)
        print("✓ Dependencies installed")
    
    return True

def install_ngrok():
    """Install ngrok if not present"""
    print("\n🔧 Setting up ngrok tunnel...\n")
    
    # Check if ngrok exists
    if os.path.exists('ngrok'):
        print("✓ ngrok already installed")
        return True
    
    if os.path.exists('/usr/local/bin/ngrok') or os.path.exists('/usr/bin/ngrok'):
        print("✓ ngrok found in system PATH")
        return True
    
    print("⏳ Installing ngrok...")
    
    try:
        # Detect architecture
        arch = subprocess.run(['uname', '-m'], capture_output=True, text=True).stdout.strip()
        if 'x86_64' in arch or 'amd64' in arch:
            url = 'https://ngrok-agent.s3.amazonaws.com/ngrok-v3-stable-linux-amd64.zip'
        elif 'arm64' in arch or 'aarch64' in arch:
            url = 'https://ngrok-agent.s3.amazonaws.com/ngrok-v3-stable-linux-arm64.zip'
        else:
            url = 'https://ngrok-agent.s3.amazonaws.com/ngrok-v3-stable-linux-amd64.zip'
        
        # Download and extract
        subprocess.run(['curl', '-sL', url, '-o', 'ngrok.zip'], check=True)
        subprocess.run(['unzip', '-q', 'ngrok.zip'], check=True)
        os.remove('ngrok.zip')
        os.chmod('ngrok', 0o755)
        
        print("✓ ngrok installed successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to install ngrok: {e}")
        print("\nAlternative: Install ngrok manually from https://ngrok.com/download")
        return False

def start_flask():
    """Start Flask app in background"""
    print("\n🚀 Starting Flask application...\n")
    
    if not os.path.exists('app.py'):
        print("✗ app.py not found")
        return None
    
    try:
        # Start Flask
        process = subprocess.Popen(
            [sys.executable, 'app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for Flask to start
        time.sleep(3)
        
        if process.poll() is None:  # Still running
            print("✓ Flask app started")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"✗ Flask failed to start:\n{stderr}")
            return None
    except Exception as e:
        print(f"✗ Error starting Flask: {e}")
        return None

def start_ngrok():
    """Start ngrok tunnel"""
    print("\n🌐 Creating public tunnel...\n")
    
    try:
        subprocess.run(['./ngrok', 'http', '5000'], check=False)
    except FileNotFoundError:
        print("✗ ngrok not found")
        print("\nTry: ./ngrok http 5000 (in another terminal)")

def show_access_info():
    """Show how to access the public URL"""
    print("\n" + "="*70)
    print("📱 PUBLIC ACCESS INSTRUCTIONS")
    print("="*70 + "\n")
    
    print("1. Look for output like this from ngrok:")
    print("   └── Forwarding: https://xxxx-xxxx-xxxx.ngrok.io → http://localhost:5000\n")
    
    print("2. Use that URL to share with others:")
    print("   👉 https://xxxx-xxxx-xxxx.ngrok.io\n")
    
    print("3. Login credentials:")
    print("   Username: 228820")
    print("   Password: 228820\n")
    
    print("4. Monitor requests at:")
    print("   http://127.0.0.1:4040\n")
    
    print("="*70 + "\n")

def main():
    print_header()
    
    # Check dependencies
    if not check_dependencies():
        print("\n✗ Failed to verify dependencies")
        return 1
    
    # Install ngrok
    if not install_ngrok():
        print("\n⚠️  ngrok installation failed, but you can still use tunneling alternatives:")
        print("\n   Option 1: Install ngrok manually from https://ngrok.com/download")
        print("   Option 2: Use localtunnel: npm install -g localtunnel && lt --port 5000")
        print("   Option 3: Deploy to cloud (Heroku, Railway, Replit)")
        print("\n   See PUBLIC_ACCESS.md for all options")
        return 1
    
    # Start Flask
    flask_process = start_flask()
    if not flask_process:
        print("\n✗ Failed to start Flask app")
        return 1
    
    # Show access info
    show_access_info()
    
    # Start ngrok
    try:
        start_ngrok()
    except KeyboardInterrupt:
        print("\n\n⏹️  Shutting down...")
        flask_process.terminate()
        flask_process.wait()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
