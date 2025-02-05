# setup_project.py
import os
import venv
import subprocess
import platform
from pathlib import Path

def install_pyenv():
    """Install pyenv based on operating system"""
    system = platform.system().lower()
    
    if system == "linux" or system == "darwin":
        try:
            # Install pyenv dependencies
            if system == "linux":
                subprocess.run([
                    "sudo", "apt-get", "update"
                ], check=True)
                subprocess.run([
                    "sudo", "apt-get", "install", "-y",
                    "make", "build-essential", "libssl-dev", "zlib1g-dev",
                    "libbz2-dev", "libreadline-dev", "libsqlite3-dev",
                    "wget", "curl", "llvm", "libncurses5-dev", "libncursesw5-dev",
                    "xz-utils", "tk-dev", "libffi-dev", "liblzma-dev",
                    "python-openssl", "git"
                ], check=True)
            
            # Install pyenv
            subprocess.run([
                "curl", "https://pyenv.run", "|", "bash"
            ], shell=True, check=True)
            
            # Add pyenv to shell configuration
            shell_config = os.path.expanduser("~/.bashrc")
            if system == "darwin" and os.path.exists(os.path.expanduser("~/.zshrc")):
                shell_config = os.path.expanduser("~/.zshrc")
                
            with open(shell_config, "a") as f:
                f.write('\n# pyenv configuration\n')
                f.write('export PYENV_ROOT="$HOME/.pyenv"\n')
                f.write('command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"\n')
                f.write('eval "$(pyenv init -)"\n')
            
            print("🔧 pyenv installed successfully!")
            print(f"📝 Updated {shell_config} with pyenv configuration")
            print("⚠️  Please restart your shell or run:")
            print(f"    source {shell_config}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing pyenv: {str(e)}")
            raise
            
    elif system == "windows":
        print("⚠️  For Windows, please install pyenv-win using:")
        print("    pip install pyenv-win --target $env:USERPROFILE\\.pyenv")
        print("    [System.Environment]::SetEnvironmentVariable('PYENV',$env:USERPROFILE + \".pyenv\\pyenv-win\",\"User\")")
        print("    [System.Environment]::SetEnvironmentVariable('PYENV_HOME',$env:USERPROFILE + \".pyenv\\pyenv-win\",\"User\")")
        print("    [System.Environment]::SetEnvironmentVariable('path', $env:USERPROFILE + \".pyenv\\pyenv-win\\bin;\" + $env:USERPROFILE + \".pyenv\\pyenv-win\\shims;\" + [System.Environment]::GetEnvironmentVariable('path', \"User\"),\"User\")")

def setup_python_version():
    """Install and set up Python 3.10 using pyenv"""
    try:
        # Install latest Python 3.10
        subprocess.run(["pyenv", "install", "3.10"], check=True)
        
        # Set local version
        subprocess.run(["pyenv", "local", "3.10"], check=True)
        
        print("✅ Python 3.10 installed and configured!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error setting up Python: {str(e)}")
        raise

# [Previous functions remain the same: create_directory_structure, create_requirements_txt, 
#  create_virtual_environment, create_gitignore, create_env_example]

def main():
    """
    Main function to orchestrate the project setup.
    """
    print("🚀 Starting AI Agent project setup...")
    
    try:
        # Install pyenv first
        print("📦 Installing pyenv...")
        install_pyenv()
        
        # Set up Python version
        print("🐍 Setting up Python 3.10...")
        setup_python_version()
        
        # Create project structure
        print("📁 Creating directory structure...")
        create_directory_structure()
        
        # Create configuration files
        print("📝 Creating requirements.txt...")
        create_requirements_txt()
        print("🔒 Creating .gitignore...")
        create_gitignore()
        print("⚙️ Creating .env.example...")
        create_env_example()
        
        # Create virtual environment using pyenv Python
        print("🐍 Creating virtual environment 'ai_agent'...")
        create_virtual_environment()
        
        print("\n✨ Setup completed successfully! ✨")
        print("\nNext steps:")
        print("1. Restart your shell or run 'source ~/.bashrc' (or ~/.zshrc)")
        print("2. Copy .env.example to .env and update configurations")
        print("3. Activate the virtual environment:")
        if platform.system() == "Windows":
            print("   .\\ai_agent\\Scripts\\activate")
        else:
            print("   source ai_agent/bin/activate")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {str(e)}")
        raise

if __name__ == "__main__":
    main()