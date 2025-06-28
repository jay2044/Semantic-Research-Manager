import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict
import os
from pathlib import Path


class SemanticResearchChecker:
    """
    A simple semantic similarity checker for research papers.
    Embeds research context and compares it with paper abstracts.
    """
    
    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """
        Initialize the semantic checker with a sentence transformer model.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        print(f"Loading model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.context_embedding = None
        self.context_text = None
        
    def load_research_context(self, filepath: str) -> None:
        """
        Load and embed the research context from a text file.
        
        Args:
            filepath: Path to the research context text file
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Context file not found: {filepath}")
            
        with open(filepath, 'r', encoding='utf-8') as f:
            self.context_text = f.read().strip()
            
        if not self.context_text:
            raise ValueError("Context file is empty")
            
        print(f"Loaded context: {len(self.context_text)} characters")
        
        # Create embedding for the context
        print("Creating context embedding...")
        self.context_embedding = self.model.encode(self.context_text, convert_to_tensor=True)
        print("Context embedding created successfully")
        
    def check_paper_relevance(self, title: str, abstract: str) -> Dict[str, float]:
        """
        Check the relevance of a paper against the research context.
        
        Args:
            title: Paper title
            abstract: Paper abstract or introduction
            
        Returns:
            Dictionary with relevance scores and analysis
        """
        if self.context_embedding is None:
            raise ValueError("Research context not loaded. Call load_research_context() first.")
            
        # Combine title and abstract
        paper_text = f"{title}\n\n{abstract}"
        
        # Create embedding for the paper
        paper_embedding = self.model.encode(paper_text, convert_to_tensor=True)
        
        # Calculate cosine similarity
        cosine_sim = self._cosine_similarity(self.context_embedding, paper_embedding)
        
        # Convert to percentage
        relevance_score = float(cosine_sim) * 100
        
        # Determine relevance category
        if relevance_score >= 70:
            category = "Highly Relevant"
        elif relevance_score >= 50:
            category = "Moderately Relevant"
        elif relevance_score >= 30:
            category = "Somewhat Relevant"
        else:
            category = "Low Relevance"
            
        return {
            "relevance_score": relevance_score,
            "category": category,
            "title": title,
            "abstract_length": len(abstract)
        }
        
    def _cosine_similarity(self, embedding1, embedding2):
        """
        Calculate cosine similarity between two embeddings.
        """
        # Normalize embeddings
        embedding1_norm = embedding1 / np.linalg.norm(embedding1)
        embedding2_norm = embedding2 / np.linalg.norm(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1_norm, embedding2_norm)
        
        return similarity
        
    def batch_check_papers(self, papers: List[Tuple[str, str]]) -> List[Dict[str, float]]:
        """
        Check multiple papers at once.
        
        Args:
            papers: List of (title, abstract) tuples
            
        Returns:
            List of relevance results
        """
        results = []
        for title, abstract in papers:
            result = self.check_paper_relevance(title, abstract)
            results.append(result)
            
        # Sort by relevance score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return results 