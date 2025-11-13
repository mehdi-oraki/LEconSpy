"""
Quick setup verification script
Checks if all dependencies are installed correctly
"""

import sys

def check_imports():
    """Check if all required packages can be imported"""
    print("Checking dependencies...")
    
    required_packages = [
        ("langgraph", "LangGraph"),
        ("langchain", "LangChain"),
        ("bs4", "BeautifulSoup4"),
        ("requests", "Requests"),
        ("pandas", "Pandas"),
        ("lxml", "lxml"),
    ]
    
    missing = []
    
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - MISSING")
            missing.append(name)
    
    if missing:
        print("\n" + "=" * 60)
        print("ERROR: Missing required packages!")
        print("Please install dependencies with:")
        print("  pip install -r requirements.txt")
        print("=" * 60)
        return False
    
    print("\n✓ All dependencies installed correctly!")
    return True

def check_structure():
    """Check if project structure is correct"""
    print("\nChecking project structure...")
    
    import os
    
    required_files = [
        "main.py",
        "config.py",
        "requirements.txt",
        "src/agents/econ_agent.py",
        "src/fetchers/gdp_fetcher.py",
        "src/fetchers/hdi_fetcher.py",
        "src/fetchers/happiness_fetcher.py",
        "src/ranking/ranker.py",
        "src/reporting/report_generator.py",
        "src/utils/web_scraper.py",
        "src/utils/data_validator.py",
    ]
    
    missing = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - MISSING")
            missing.append(file)
    
    if missing:
        print("\n" + "=" * 60)
        print("ERROR: Missing required files!")
        print("=" * 60)
        return False
    
    print("\n✓ Project structure is correct!")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("LEconSpy Setup Verification")
    print("=" * 60)
    print()
    
    deps_ok = check_imports()
    structure_ok = check_structure()
    
    print()
    print("=" * 60)
    if deps_ok and structure_ok:
        print("✓ Setup verification PASSED")
        print("You can now run: python main.py")
        sys.exit(0)
    else:
        print("✗ Setup verification FAILED")
        print("Please fix the issues above before running the system")
        sys.exit(1)

