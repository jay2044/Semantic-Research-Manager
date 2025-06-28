import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict, Optional
import os
import json
from pathlib import Path
from datetime import datetime

# Try to import adapters for SPECTER2, fallback gracefully if not available
try:
    from adapters import AutoAdapterModel
    from transformers import AutoTokenizer
    import torch
    ADAPTERS_AVAILABLE = True
except ImportError:
    ADAPTERS_AVAILABLE = False
    AutoAdapterModel = None
    AutoTokenizer = None
    torch = None


class SemanticResearchChecker:
    """
    A sophisticated semantic similarity checker for research papers.
    Supports embedding updates, context snippet management, and semantic integration.
    """
    
    def __init__(self, model_name: str = 'allenai/specter2'):
        """
        Initialize the semantic checker with a sentence transformer model or SPECTER2.
        
        Args:
            model_name: Name of the model to use (sentence-transformers or SPECTER2)
        """
        print(f"Loading model: {model_name}...")
        self.model_name = model_name
        
        # Check if it's SPECTER2 or a sentence-transformers model
        if model_name == 'allenai/specter2' and ADAPTERS_AVAILABLE:
            self._load_specter2()
        else:
            self._load_sentence_transformer()
            
        self.context_embedding = None
        self.context_text = None
        self.context_snippets = []  # Store added snippets
        self.snippets_file = "context_snippets.json"
        
        # Load existing snippets
        self._load_context_snippets()
        
    def _load_specter2(self):
        """Load SPECTER2 model using adapters library"""
        try:
            print("🔄 Loading SPECTER2 base model...")
            # Load tokenizer and base model
            self.tokenizer = AutoTokenizer.from_pretrained('allenai/specter2_base')
            self.model = AutoAdapterModel.from_pretrained('allenai/specter2_base')
            
            # Load the proximity adapter (for retrieval tasks)
            print("🔄 Loading SPECTER2 proximity adapter...")
            self.model.load_adapter("allenai/specter2", source="hf", load_as="specter2", set_active=True)
            
            self.is_specter2 = True
            print("✅ SPECTER2 model loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading SPECTER2: {e}")
            print("Falling back to sentence-transformers...")
            self._load_sentence_transformer()
            
    def _load_sentence_transformer(self):
        """Load sentence-transformers model"""
        try:
            # For SPECTER2 fallback, try the original SPECTER model
            if self.model_name == 'allenai/specter2':
                print("🔄 Falling back to original SPECTER model...")
                self.model_name = 'sentence-transformers/allenai-specter'
                
            self.model = SentenceTransformer(self.model_name)
            self.is_specter2 = False
            print("✅ Sentence-transformer model loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading sentence-transformer: {e}")
            # Final fallback to default
            print("Falling back to all-mpnet-base-v2...")
            self.model_name = 'all-mpnet-base-v2'
            self.model = SentenceTransformer('all-mpnet-base-v2')
            self.is_specter2 = False
        
    def _encode_text(self, text: str):
        """Encode text using the appropriate model"""
        if self.is_specter2:
            return self._encode_specter2(text)
        else:
            return self.model.encode(text, convert_to_tensor=True)
            
    def _encode_specter2(self, text: str):
        """Encode text using SPECTER2"""
        # SPECTER2 expects format: title + [SEP] + abstract
        if '\n\n' in text:
            title, abstract = text.split('\n\n', 1)
            # Format for SPECTER2: concatenate title and abstract with [SEP]
            formatted_text = title + self.tokenizer.sep_token + abstract
        else:
            # If no abstract separator, treat as title only
            formatted_text = text + self.tokenizer.sep_token + ""
        
        # Tokenize and encode
        inputs = self.tokenizer(
            formatted_text, 
            padding=True, 
            truncation=True, 
            max_length=512, 
            return_tensors="pt", 
            return_token_type_ids=False
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use the [CLS] token representation (first token)
            embeddings = outputs.last_hidden_state[:, 0, :]
            
        return embeddings.squeeze()
        
    def _load_context_snippets(self):
        """Load saved context snippets from file"""
        if os.path.exists(self.snippets_file):
            try:
                with open(self.snippets_file, 'r', encoding='utf-8') as f:
                    self.context_snippets = json.load(f)
                print(f"✅ Loaded {len(self.context_snippets)} context snippets")
            except (json.JSONDecodeError, FileNotFoundError):
                self.context_snippets = []
        else:
            self.context_snippets = []
            
    def _save_context_snippets(self):
        """Save context snippets to file"""
        with open(self.snippets_file, 'w', encoding='utf-8') as f:
            json.dump(self.context_snippets, f, indent=2, ensure_ascii=False)
        
    def load_research_context(self, filepath: str) -> None:
        """
        Load and embed the research context from a text file, including snippets.
        
        Args:
            filepath: Path to the research context text file
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Context file not found: {filepath}")
            
        with open(filepath, 'r', encoding='utf-8') as f:
            base_context = f.read().strip()
            
        if not base_context:
            raise ValueError("Context file is empty")
        
        # Combine base context with snippets
        self.context_text = self._build_enhanced_context(base_context)
        
        print(f"Loaded context: {len(base_context)} chars + {len(self.context_snippets)} snippets")
        
        # Create embedding for the enhanced context
        print("Creating enhanced context embedding...")
        self.context_embedding = self._encode_text(self.context_text)
        print("Enhanced context embedding created successfully")
        
    def _build_enhanced_context(self, base_context: str) -> str:
        """Build enhanced context by combining base context with snippets"""
        if not self.context_snippets:
            return base_context
        
        # Add snippets section
        enhanced_context = base_context + "\n\n" + "="*50 + "\n"
        enhanced_context += "RESEARCH INSIGHTS & SNIPPETS\n"
        enhanced_context += "="*50 + "\n\n"
        
        for snippet in self.context_snippets:
            enhanced_context += f"• {snippet['content']}\n"
            if snippet.get('source'):
                enhanced_context += f"  (Source: {snippet['source']})\n"
            enhanced_context += "\n"
        
        return enhanced_context
        
    def add_context_snippet(self, content: str, source: str = "", paper_id: str = None) -> str:
        """
        Add a snippet to the global research context and update embeddings.
        
        Args:
            content: The snippet text to add
            source: Source information (paper title, etc.)
            paper_id: Optional paper ID if snippet is from a stored paper
            
        Returns:
            Snippet ID for future reference
        """
        snippet_id = f"snippet_{len(self.context_snippets) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        snippet = {
            "id": snippet_id,
            "content": content,
            "source": source,
            "paper_id": paper_id,
            "added_date": datetime.now().isoformat()
        }
        
        self.context_snippets.append(snippet)
        self._save_context_snippets()
        
        # Update context embedding if we have a base context
        if self.context_text:
            base_context = self._extract_base_context()
            self.context_text = self._build_enhanced_context(base_context)
            self.context_embedding = self._encode_text(self.context_text)
            print(f"✅ Added snippet and updated context embedding")
        
        return snippet_id
        
    def _extract_base_context(self) -> str:
        """Extract the base context without snippets"""
        if "="*50 in self.context_text:
            return self.context_text.split("="*50)[0].strip()
        return self.context_text
        
    def remove_context_snippet(self, snippet_id: str) -> bool:
        """
        Remove a snippet from the context and update embeddings.
        
        Args:
            snippet_id: ID of the snippet to remove
            
        Returns:
            True if snippet was found and removed
        """
        for i, snippet in enumerate(self.context_snippets):
            if snippet['id'] == snippet_id:
                self.context_snippets.pop(i)
                self._save_context_snippets()
                
                # Update context embedding
                if self.context_text:
                    base_context = self._extract_base_context()
                    self.context_text = self._build_enhanced_context(base_context)
                    self.context_embedding = self._encode_text(self.context_text)
                    print(f"✅ Removed snippet and updated context embedding")
                
                return True
        return False
        
    def get_context_snippets(self) -> List[Dict]:
        """Get all context snippets"""
        return self.context_snippets.copy()
        
    def create_paper_embedding_with_notes(self, title: str, abstract: str, notes: str = "") -> np.ndarray:
        """
        Create an embedding for a paper including its notes.
        
        Args:
            title: Paper title
            abstract: Paper abstract
            notes: User notes about the paper
            
        Returns:
            Paper embedding that includes semantic information from notes
        """
        # Combine title, abstract, and notes for richer semantic representation
        if notes.strip():
            paper_text = f"{title}\n\n{abstract}\n\nNOTES: {notes}"
        else:
            paper_text = f"{title}\n\n{abstract}"
        
        return self._encode_text(paper_text)
        
    def check_paper_relevance(self, title: str, abstract: str, notes: str = "") -> Dict[str, float]:
        """
        Check the relevance of a paper against the research context.
        
        Args:
            title: Paper title
            abstract: Paper abstract or introduction
            notes: Optional user notes to include in relevance calculation
            
        Returns:
            Dictionary with relevance scores and analysis
        """
        if self.context_embedding is None:
            raise ValueError("Research context not loaded. Call load_research_context() first.")
            
        # Create embedding that includes notes for more accurate relevance
        paper_embedding = self.create_paper_embedding_with_notes(title, abstract, notes)
        
        # Calculate cosine similarity
        cosine_sim = self._cosine_similarity(self.context_embedding, paper_embedding)
        
        # Convert to percentage
        relevance_score = float(cosine_sim) * 100
        
        # Determine relevance category
        if relevance_score >= 85:
            category = "Highly Relevant"
        elif relevance_score >= 65:
            category = "Moderately Relevant"
        elif relevance_score >= 45:
            category = "Somewhat Relevant"
        else:
            category = "Low Relevance"
            
        return {
            "relevance_score": relevance_score,
            "category": category,
            "title": title,
            "abstract_length": len(abstract),
            "notes_included": bool(notes.strip())
        }
        
    def _cosine_similarity(self, embedding1, embedding2):
        """
        Calculate cosine similarity between two embeddings.
        """
        # Convert to numpy if needed
        if hasattr(embedding1, 'cpu') and hasattr(embedding1, 'numpy'):
            embedding1 = embedding1.cpu().numpy()
        if hasattr(embedding2, 'cpu') and hasattr(embedding2, 'numpy'):
            embedding2 = embedding2.cpu().numpy()
            
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