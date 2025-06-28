#!/usr/bin/env python3
"""
Simple ArXiv integration for Semantic Research Manager
Handles searching ArXiv and downloading PDFs
"""

import requests
import xml.etree.ElementTree as ET
import os
import re
from typing import List, Dict, Optional


class ArXivIntegration:
    """Simple ArXiv API integration"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    PDF_BASE_URL = "https://arxiv.org/pdf"
    
    def __init__(self):
        self.session = requests.Session()
        
    def search_papers(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search ArXiv for papers"""
        # Clean and format query for ArXiv API
        # ArXiv search works better with simpler queries
        query = query.strip()
        
        # Build search URL - use 'all:' for general search
        params = {
            'search_query': f'all:{query}',
            'start': 0,
            'max_results': max_results,
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            papers = self._parse_arxiv_response(response.text)
            
            # If no results with 'all:', try with title search
            if not papers and 'all:' in params['search_query']:
                params['search_query'] = f'ti:{query}'
                response = self.session.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()
                papers = self._parse_arxiv_response(response.text)
            
            return papers
            
        except Exception as e:
            print(f"Error searching ArXiv: {e}")
            return []
    
    def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict]:
        """Get a specific paper by ArXiv ID"""
        # Clean ArXiv ID (remove arxiv: prefix if present)
        arxiv_id = arxiv_id.replace('arxiv:', '').strip()
        
        params = {
            'id_list': arxiv_id
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()
            
            papers = self._parse_arxiv_response(response.text)
            return papers[0] if papers else None
            
        except Exception as e:
            print(f"Error fetching ArXiv paper {arxiv_id}: {e}")
            return None
    
    def _parse_arxiv_response(self, xml_text: str) -> List[Dict]:
        """Parse ArXiv API XML response"""
        papers = []
        
        try:
            root = ET.fromstring(xml_text)
            
            # Define namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                # Extract paper data
                paper = {}
                
                # Title
                title_elem = entry.find('atom:title', ns)
                if title_elem is not None:
                    paper['title'] = title_elem.text.strip().replace('\n', ' ')
                
                # Abstract
                summary_elem = entry.find('atom:summary', ns)
                if summary_elem is not None:
                    paper['abstract'] = summary_elem.text.strip()
                
                # ArXiv ID
                id_elem = entry.find('atom:id', ns)
                if id_elem is not None:
                    arxiv_url = id_elem.text
                    # Extract ID from URL like http://arxiv.org/abs/2303.08774v1
                    match = re.search(r'arxiv\.org/abs/([^v]+)', arxiv_url)
                    if match:
                        paper['arxiv_id'] = match.group(1)
                
                # Authors
                authors = []
                for author in entry.findall('atom:author', ns):
                    name_elem = author.find('atom:name', ns)
                    if name_elem is not None:
                        authors.append(name_elem.text)
                paper['authors'] = ', '.join(authors)
                
                # Publication date
                published_elem = entry.find('atom:published', ns)
                if published_elem is not None:
                    paper['published'] = published_elem.text[:10]  # Just the date part
                
                # Categories
                categories = []
                for category in entry.findall('atom:category', ns):
                    term = category.get('term')
                    if term:
                        categories.append(term)
                paper['categories'] = ', '.join(categories)
                
                if paper.get('title') and paper.get('abstract'):
                    papers.append(paper)
                    
        except Exception as e:
            print(f"Error parsing ArXiv response: {e}")
        
        return papers
    
    def download_pdf(self, arxiv_id: str, paper_title: str, folder_path: str = "papers") -> str:
        """Download PDF from ArXiv with descriptive filename"""
        # Create folder if it doesn't exist
        os.makedirs(folder_path, exist_ok=True)
        
        # Clean ArXiv ID
        arxiv_id = arxiv_id.replace('arxiv:', '').strip()
        
        # Clean paper title for filename
        clean_title = self._clean_filename(paper_title)
        
        # Create filename: [ArXiv_ID] Title.pdf
        filename = f"[{arxiv_id}] {clean_title}.pdf"
        filepath = os.path.join(folder_path, filename)
        
        # Build PDF URL
        pdf_url = f"{self.PDF_BASE_URL}/{arxiv_id}.pdf"
        
        try:
            print(f"Downloading PDF: {arxiv_id}")
            response = self.session.get(pdf_url, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ PDF downloaded: {filename}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error downloading PDF {arxiv_id}: {e}")
            return None
    
    def _clean_filename(self, title: str) -> str:
        """Clean paper title for use in filename"""
        # Remove or replace invalid filename characters
        invalid_chars = '<>:"/\\|?*'
        clean_title = title
        
        for char in invalid_chars:
            clean_title = clean_title.replace(char, ' ')
        
        # Replace multiple spaces with single space
        clean_title = re.sub(r'\s+', ' ', clean_title)
        
        # Trim to reasonable length (Windows has 260 char path limit)
        if len(clean_title) > 100:
            clean_title = clean_title[:100] + "..."
        
        return clean_title.strip()


def get_folder_for_relevance(relevance_score: float) -> str:
    """Get folder name - now just returns papers folder since we use single folder"""
    return "papers" 