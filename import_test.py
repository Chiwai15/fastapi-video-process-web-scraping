import sys
import os

# Add the same paths as in conftest.py
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/app')

print('sys.path:', sys.path)
print('Current directory:', os.getcwd())

# Try the import that's failing in your tests
try:
    from services.scraper.science_news_scraper import ScienceNewsScraper
    print('Import successful!')
    print('ScienceNewsScraper class:', ScienceNewsScraper)
except ImportError as e:
    print('Import failed:', e)
    
    # Try alternative import paths
    try:
        from services.scraper.science_news_scraper import ScienceNewsScraper
        print('Alternative import successful!')
    except ImportError as e2:
        print('Alternative import failed:', e2)
        
        # Find the actual file
        print('\nSearching for science_news_scraper.py file:')
        found = False
        for root, dirs, files in os.walk('/app'):
            for file in files:
                if file == 'science_news_scraper.py':
                    path = os.path.join(root, file)
                    print(f'Found at: {path}')
                    found = True
        
        if not found:
            print('File not found anywhere in /app')
