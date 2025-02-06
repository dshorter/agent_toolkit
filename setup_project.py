# setup.py
import os
import subprocess
import platform
from pathlib import Path
import sys
import venv

def run_powershell_command(command):
    try:
        subprocess.run(["powershell", "-Command", command], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def create_structure():
    """Create project directories"""
    dirs = [
        'src/agent',
        'src/api',
        'src/config',
        'src/core',
        'src/utils',
        'tests',
        'docs',
        'scripts'
    ]
    
    for dir in dirs:
        Path(dir).mkdir(parents=True, exist_ok=True)
        init_file = Path(dir) / '__init__.py'
        init_file.touch()

def create_requirements():
    """Create requirements.txt"""
    requirements = """
fastapi==0.109.2
uvicorn[standard]==0.27.1
pydantic==2.6.1
pydantic-settings==2.1.0
python-dotenv==1.0.0
motor==3.3.2
redis==5.0.1
beanie==1.25.0
celery==5.3.6
flower==2.0.1
torch==2.1.2
transformers==4.37.2
sentence-transformers==2.2.2
pytest==7.4.4
pytest-asyncio==0.23.4
black==23.12.1
ruff==0.1.11
python-multipart==0.0.6
httpx==0.26.0
"""
    with open('requirements.txt', 'w') as f:
        f.write(requirements.strip())

def setup_venv():
    """Create and configure virtual environment"""
    venv.create('venv', with_pip=True)
    
    if platform.system() == "Windows":
        pip_path = "venv\\Scripts\\pip"
    else:
        pip_path = "venv/bin/pip"
    
    subprocess.run([pip_path, "install", "--upgrade", "pip"])
    subprocess.run([pip_path, "install", "-r", "requirements.txt"])

def create_env_example():
    """Create .env.example"""
    content = """
PROJECT_NAME=AI Agent System
VERSION=1.0.0
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=agent_db
REDIS_URL=redis://localhost:6379
LLM_MODEL_NAME=mistral-7b
LOG_LEVEL=INFO
"""
    with open('.env.example', 'w') as f:
        f.write(content.strip())

def create_gitignore():
    """Create .gitignore"""
    content = """
venv/
__pycache__/
*.py[cod]
.env
.vscode/
.idea/
*.log
"""
    with open('.gitignore', 'w') as f:
        f.write(content.strip())

def main():
    """Setup project environment"""
    print("🚀 Setting up AI Agent project...")
    
    try:
        create_structure()
        create_requirements()
        create_env_example()
        create_gitignore()
        setup_venv()
        
        print("\n✅ Setup complete!")
        print("\nNext steps:")
        if platform.system() == "Windows":
            print("1. .\\venv\\Scripts\\activate")
        else:
            print("1. source venv/bin/activate")
        print("2. Copy .env.example to .env and update")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    
    
    
    
    