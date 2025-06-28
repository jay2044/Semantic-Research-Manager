#!/usr/bin/env python3
"""
Paper storage system for Semantic Research Manager
Handles saving, loading, and ranking papers by relevance
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import numpy as np


class PaperStorage:
    """Manages storage and retrieval of papers with their relevance data"""
    
    def __init__(self, storage_file: str = "papers.json"):
        self.storage_file = storage_file
        self.papers = self._load_papers()
    
    def _load_papers(self) -> List[Dict]:
        """Load papers from storage file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def _save_papers(self):
        """Save papers to storage file"""
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.papers, f, indent=2, ensure_ascii=False)
    
    def add_paper(self, title: str, abstract: str, relevance_score: float, 
                  category: str, embedding: Optional[np.ndarray] = None) -> str:
        """Add a new paper to storage"""
        paper_id = f"paper_{len(self.papers) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        paper_data = {
            "id": paper_id,
            "title": title,
            "abstract": abstract,
            "relevance_score": relevance_score,
            "category": category,
            "added_date": datetime.now().isoformat(),
            "abstract_length": len(abstract),
            "status": "relevant" if relevance_score >= 30 else "discarded"
        }
        
        # Store embedding if provided
        if embedding is not None:
            paper_data["embedding"] = embedding.tolist()
        
        self.papers.append(paper_data)
        self._save_papers()
        return paper_id
    
    def get_papers_by_relevance(self, min_score: float = 0) -> List[Dict]:
        """Get papers sorted by relevance score (highest first)"""
        relevant_papers = [p for p in self.papers if p["relevance_score"] >= min_score]
        return sorted(relevant_papers, key=lambda x: x["relevance_score"], reverse=True)
    
    def get_papers_by_status(self, status: str) -> List[Dict]:
        """Get papers by status (relevant/discarded)"""
        return [p for p in self.papers if p["status"] == status]
    
    def update_paper_status(self, paper_id: str, status: str):
        """Update paper status (relevant/discarded)"""
        for paper in self.papers:
            if paper["id"] == paper_id:
                paper["status"] = status
                paper["updated_date"] = datetime.now().isoformat()
                break
        self._save_papers()
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict]:
        """Get a specific paper by ID"""
        for paper in self.papers:
            if paper["id"] == paper_id:
                return paper
        return None
    
    def delete_paper(self, paper_id: str) -> bool:
        """Delete a paper from storage"""
        for i, paper in enumerate(self.papers):
            if paper["id"] == paper_id:
                del self.papers[i]
                self._save_papers()
                return True
        return False
    
    def get_statistics(self) -> Dict:
        """Get storage statistics"""
        total_papers = len(self.papers)
        relevant_papers = len(self.get_papers_by_status("relevant"))
        discarded_papers = len(self.get_papers_by_status("discarded"))
        
        if total_papers > 0:
            avg_relevance = sum(p["relevance_score"] for p in self.papers) / total_papers
            highly_relevant = len([p for p in self.papers if p["relevance_score"] >= 70])
            moderately_relevant = len([p for p in self.papers if 50 <= p["relevance_score"] < 70])
        else:
            avg_relevance = 0
            highly_relevant = 0
            moderately_relevant = 0
        
        return {
            "total_papers": total_papers,
            "relevant_papers": relevant_papers,
            "discarded_papers": discarded_papers,
            "average_relevance": round(avg_relevance, 2),
            "highly_relevant": highly_relevant,
            "moderately_relevant": moderately_relevant
        }
    
    def search_papers(self, query: str) -> List[Dict]:
        """Search papers by title or abstract (simple text search)"""
        query_lower = query.lower()
        results = []
        
        for paper in self.papers:
            if (query_lower in paper["title"].lower() or 
                query_lower in paper["abstract"].lower()):
                results.append(paper)
        
        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)
    
    def export_papers(self, filename: str, status: Optional[str] = None):
        """Export papers to a JSON file"""
        papers_to_export = self.papers
        if status:
            papers_to_export = self.get_papers_by_status(status)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(papers_to_export, f, indent=2, ensure_ascii=False) 