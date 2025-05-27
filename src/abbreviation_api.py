"""
Medical Abbreviation API Handler
Uses online services for abbreviation lookups
"""

import requests
import json
from typing import Dict, List, Optional
from functools import lru_cache
import time

class MedicalAbbreviationAPI:
    def __init__(self, cache_file: str = "data/api_cache.json"):
        self.cache_file = cache_file
        self.session = requests.Session()
        self.load_cache()
        
        # API endpoints (examples - replace with actual services)
        self.apis = {
            'medabbrev': {
                'url': 'https://www.medabbrev.com/api/v1/abbreviations',
                'key': 'YOUR_API_KEY',  # Get from service
                'rate_limit': 100  # requests per minute
            },
            'allie': {  # ALLIE - A Search Service for Abbreviations
                'url': 'https://allie.dbcls.jp/api/search',
                'key': None,  # Free service
                'rate_limit': 60
            }
        }
        
        self.last_request_time = {}
    
    def load_cache(self):
        """Load cached API responses"""
        try:
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)
        except:
            self.cache = {}
    
    def save_cache(self):
        """Save cache to file"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)
    
    def _rate_limit(self, api_name: str):
        """Implement rate limiting"""
        if api_name in self.last_request_time:
            elapsed = time.time() - self.last_request_time[api_name]
            min_interval = 60.0 / self.apis[api_name]['rate_limit']
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
        
        self.last_request_time[api_name] = time.time()
    
    @lru_cache(maxsize=1000)
    def lookup_allie(self, abbreviation: str) -> Dict:
        """Look up using ALLIE database"""
        # Check cache
        cache_key = f"allie_{abbreviation}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        self._rate_limit('allie')
        
        try:
            response = self.session.get(
                self.apis['allie']['url'],
                params={
                    'keywords': abbreviation,
                    'format': 'json',
                    'count': 10
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('results', []):
                    if item.get('abbreviation', '').upper() == abbreviation.upper():
                        results.append({
                            'definition': item.get('long_form', ''),
                            'frequency': item.get('frequency', 0),
                            'source': 'ALLIE'
                        })
                
                result = {
                    'abbreviation': abbreviation,
                    'definitions': [r['definition'] for r in results],
                    'found': len(results) > 0,
                    'source': 'ALLIE'
                }
                
                # Cache result
                self.cache[cache_key] = result
                self.save_cache()
                
                return result
        
        except Exception as e:
            print(f"Error querying ALLIE: {e}")
        
        return {
            'abbreviation': abbreviation,
            'definitions': [],
            'found': False,
            'error': True
        }
    
    def lookup_pubmed(self, abbreviation: str) -> Dict:
        """Look up using PubMed abbreviation database"""
        # Implementation for PubMed E-utilities API
        # Requires NCBI API key for better rate limits
        pass
    
    def lookup_multiple_sources(self, abbreviation: str) -> Dict:
        """Look up abbreviation in multiple sources"""
        results = {
            'abbreviation': abbreviation,
            'definitions': [],
            'sources': []
        }
        
        # Try ALLIE first (free service)
        allie_result = self.lookup_allie(abbreviation)
        if allie_result.get('found'):
            results['definitions'].extend(allie_result['definitions'])
            results['sources'].append('ALLIE')
        
        # Add other API calls here
        
        # Deduplicate definitions
        seen = set()
        unique_defs = []
        for d in results['definitions']:
            if d.lower() not in seen:
                seen.add(d.lower())
                unique_defs.append(d)
        
        results['definitions'] = unique_defs
        results['found'] = len(unique_defs) > 0
        
        return results