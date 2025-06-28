#!/usr/bin/env python3
"""
Paper storage system for Semantic Research Manager
Handles saving, loading, and ranking papers by relevance
"""

import json
import os
import random
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
            "status": "to read",  # New default status
            "notes": ""  # Add notes field
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
        """Get papers by status (to read/reading/read/discarded)"""
        return [p for p in self.papers if p["status"] == status]
    
    def get_valid_statuses(self) -> List[str]:
        """Get list of valid paper statuses"""
        return ["to read", "reading", "read", "discarded"]
    
    def update_paper_status(self, paper_id: str, status: str):
        """Update paper status (to read/reading/read/discarded)"""
        valid_statuses = self.get_valid_statuses()
        if status not in valid_statuses:
            raise ValueError(f"Invalid status '{status}'. Valid statuses: {valid_statuses}")
        
        for paper in self.papers:
            if paper["id"] == paper_id:
                paper["status"] = status
                paper["updated_date"] = datetime.now().isoformat()
                break
        self._save_papers()
    
    def update_paper_notes(self, paper_id: str, notes: str):
        """Update paper notes and recalculate embedding"""
        for paper in self.papers:
            if paper["id"] == paper_id:
                paper["notes"] = notes
                paper["updated_date"] = datetime.now().isoformat()
                # Mark that embedding needs update
                paper["embedding_needs_update"] = True
                break
        self._save_papers()
    
    def update_paper_embedding_with_notes(self, paper_id: str, checker):
        """
        Update a paper's embedding to include its notes using the semantic checker.
        
        Args:
            paper_id: ID of the paper to update
            checker: SemanticResearchChecker instance
        """
        for paper in self.papers:
            if paper["id"] == paper_id:
                # Create new embedding including notes
                new_embedding = checker.create_paper_embedding_with_notes(
                    paper["title"], 
                    paper["abstract"], 
                    paper.get("notes", "")
                )
                
                # Store the new embedding
                paper["embedding"] = new_embedding.tolist()
                paper["embedding_updated_date"] = datetime.now().isoformat()
                paper["embedding_needs_update"] = False
                
                # Recalculate relevance with notes included
                result = checker.check_paper_relevance(
                    paper["title"], 
                    paper["abstract"], 
                    paper.get("notes", "")
                )
                
                # Update relevance score and category
                paper["relevance_score"] = result["relevance_score"]
                paper["category"] = result["category"]
                
                break
        
        self._save_papers()
        
    def batch_update_embeddings_with_notes(self, checker) -> Dict:
        """
        Update embeddings for all papers that have notes and need embedding updates.
        
        Args:
            checker: SemanticResearchChecker instance
            
        Returns:
            Dictionary with update statistics
        """
        updated_count = 0
        error_count = 0
        
        for paper in self.papers:
            # Update if paper has notes and needs embedding update
            if (paper.get("notes", "") and 
                paper.get("embedding_needs_update", True)):
                
                try:
                    # Create new embedding including notes
                    new_embedding = checker.create_paper_embedding_with_notes(
                        paper["title"], 
                        paper["abstract"], 
                        paper.get("notes", "")
                    )
                    
                    # Store the new embedding
                    paper["embedding"] = new_embedding.tolist()
                    paper["embedding_updated_date"] = datetime.now().isoformat()
                    paper["embedding_needs_update"] = False
                    
                    # Recalculate relevance with notes included
                    result = checker.check_paper_relevance(
                        paper["title"], 
                        paper["abstract"], 
                        paper.get("notes", "")
                    )
                    
                    # Update relevance score and category
                    paper["relevance_score"] = result["relevance_score"]
                    paper["category"] = result["category"]
                    
                    updated_count += 1
                    
                except Exception as e:
                    print(f"❌ Error updating embedding for paper {paper['id']}: {e}")
                    error_count += 1
        
        self._save_papers()
        
        return {
            "updated_count": updated_count,
            "error_count": error_count,
            "total_papers": len(self.papers)
        }
        
    def get_papers_needing_embedding_update(self) -> List[Dict]:
        """Get papers that have notes but need embedding updates"""
        return [p for p in self.papers 
                if p.get("notes", "") and p.get("embedding_needs_update", True)]
    
    def get_top_unread_papers(self, limit: int = 10) -> List[Dict]:
        """Get top unread papers by relevance score"""
        unread_papers = self.get_papers_by_status("to read")
        return sorted(unread_papers, key=lambda x: x["relevance_score"], reverse=True)[:limit]
    
    def get_random_unread_paper(self) -> Optional[Dict]:
        """Get a random unread paper"""
        unread_papers = self.get_papers_by_status("to read")
        return random.choice(unread_papers) if unread_papers else None
    
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
        to_read_papers = len(self.get_papers_by_status("to read"))
        reading_papers = len(self.get_papers_by_status("reading"))
        read_papers = len(self.get_papers_by_status("read"))
        discarded_papers = len(self.get_papers_by_status("discarded"))
        
        if total_papers > 0:
            avg_relevance = sum(p["relevance_score"] for p in self.papers) / total_papers
            highly_relevant = len([p for p in self.papers if p["relevance_score"] >= 85])
            moderately_relevant = len([p for p in self.papers if 65 <= p["relevance_score"] < 85])
        else:
            avg_relevance = 0
            highly_relevant = 0
            moderately_relevant = 0
        
        return {
            "total_papers": total_papers,
            "to_read_papers": to_read_papers,
            "reading_papers": reading_papers,
            "read_papers": read_papers,
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
    
    def paper_exists_by_arxiv_id(self, arxiv_id: str) -> bool:
        """Check if a paper with the given ArXiv ID already exists"""
        for paper in self.papers:
            if paper.get('arxiv_id') == arxiv_id:
                return True
        return False
    
    def get_paper_by_arxiv_id(self, arxiv_id: str) -> Optional[Dict]:
        """Get a paper by its ArXiv ID"""
        for paper in self.papers:
            if paper.get('arxiv_id') == arxiv_id:
                return paper
        return None

    def recalculate_all_relevance_scores(self, checker) -> Dict:
        """
        Recalculate relevance scores for all stored papers using the current context.
        
        Args:
            checker: SemanticResearchChecker instance with loaded context
            
        Returns:
            Dictionary with recalculation statistics
        """
        if checker.context_embedding is None:
            raise ValueError("No research context loaded. Please load context first.")
        
        updated_count = 0
        unchanged_count = 0
        error_count = 0
        
        print(f"🔄 Recalculating relevance scores for {len(self.papers)} papers...")
        
        for i, paper in enumerate(self.papers, 1):
            try:
                # Recalculate relevance for this paper
                result = checker.check_paper_relevance(paper["title"], paper["abstract"])
                
                old_score = paper["relevance_score"]
                new_score = result["relevance_score"]
                old_category = paper["category"]
                new_category = result["category"]
                
                # Update paper data
                paper["relevance_score"] = new_score
                paper["category"] = new_category
                paper["recalculated_date"] = datetime.now().isoformat()
                
                # Preserve existing status - don't automatically change it
                # Users can manually change status if needed
                
                # Track changes
                if abs(new_score - old_score) > 1.0:  # Significant change threshold
                    updated_count += 1
                    print(f"  Paper {i}: {old_score:.1f}% → {new_score:.1f}% ({old_category} → {new_category})")
                else:
                    unchanged_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"  ❌ Error processing paper {i}: {e}")
        
        # Save updated papers
        self._save_papers()
        
        print(f"✅ Recalculation complete!")
        print(f"   Updated: {updated_count} papers")
        print(f"   Unchanged: {unchanged_count} papers")
        print(f"   Errors: {error_count} papers")
        
        return {
            "total_papers": len(self.papers),
            "updated_papers": updated_count,
            "unchanged_papers": unchanged_count,
            "error_papers": error_count
        } 