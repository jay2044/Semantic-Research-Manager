# Semantic Research Manager

A comprehensive Python tool to check, store, and manage academic papers based on their relevance to your research context using semantic embeddings.

## Features

- **Semantic Similarity**: Uses sentence transformers to create embeddings of your research context and compare with paper abstracts
- **Paper Storage**: Automatically stores papers with their relevance scores and metadata
- **Smart Recommendations**: Get relevance scores and categories with actionable recommendations
- **Paper Management**: View, search, and manage your paper collection
- **Relevance Ranking**: All papers are automatically ranked by relevance score
- **Export Functionality**: Export your paper collection to JSON format
- **Interactive CLI**: User-friendly terminal interface with clear navigation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Semantic-Research-Manager.git
cd Semantic-Research-Manager
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows: `.\venv\Scripts\Activate.ps1`
- Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

Run the interactive interface:
```bash
python main.py
```

### Main Menu Options

1. **Add and check new paper** - Enter paper title/abstract, get relevance score, and choose to store or discard
2. **View all papers (ranked by relevance)** - See all stored papers sorted by relevance score
3. **View relevant papers only** - Filter to show only papers marked as relevant
4. **View discarded papers** - Filter to show only papers marked as discarded
5. **Search papers** - Search through your paper collection by title or abstract
6. **View storage statistics** - See overview of your paper collection
7. **View current research context** - Display your loaded research context
8. **Change research context file** - Switch to a different context file
9. **Change embedding model** - Choose different embedding models
10. **Export papers** - Export your paper collection to JSON
11. **Exit** - Clean exit from the application

### Paper Workflow

1. **Add Paper**: Enter title and abstract
2. **Get Analysis**: System provides relevance score and recommendation
3. **Choose Action**:
   - **Store as relevant** (≥30% relevance): Paper is saved with embedding
   - **Store as discarded**: Paper is saved but marked as discarded
   - **Skip**: Paper is not stored
4. **Manage Collection**: View, search, and organize your papers

### Relevance Categories

- **Highly Relevant** (≥85%): Must-read papers closely aligned with your research
- **Moderately Relevant** (65-84%): Worth reading if you have time
- **Somewhat Relevant** (45-64%): May contain useful insights
- **Low Relevance** (<45%): Can be safely skipped

## Data Storage

Papers are stored in `papers.json` with the following information:
- Paper ID (auto-generated)
- Title and abstract
- Relevance score and category
- Status (relevant/discarded)
- Addition date
- Embedding vector (for relevant papers)

## Configuration

### Changing the embedding model

You can use different sentence transformer models:

```python
checker = SemanticResearchChecker(model_name='all-mpnet-base-v2')  # Default, balanced
checker = SemanticResearchChecker(model_name='all-MiniLM-L6-v2')   # Faster, less accurate
checker = SemanticResearchChecker(model_name='allenai/specter2')   # Scientific text optimized
```

### Research Context

Edit `research_context.txt` to describe your research interests. This file serves as the reference for relevance checking.

## Programmatic Usage

```python
from semantic_checker import SemanticResearchChecker
from paper_storage import PaperStorage

# Initialize
checker = SemanticResearchChecker()
storage = PaperStorage()

# Load context
checker.load_research_context('research_context.txt')

# Check and store a paper
result = checker.check_paper_relevance(title, abstract)
paper_id = storage.add_paper(
    title=title,
    abstract=abstract,
    relevance_score=result['relevance_score'],
    category=result['category']
)

# Get ranked papers
papers = storage.get_papers_by_relevance()
```

## File Structure

```
Semantic-Research-Manager/
├── main.py                 # Interactive terminal interface
├── semantic_checker.py     # Core semantic similarity logic
├── paper_storage.py        # Paper storage and management
├── check_paper.py          # Simple CLI for single paper checking
├── example_usage.py        # Example script
├── research_context.txt    # Your research context
├── papers.json            # Stored papers (auto-generated)
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## How it works

1. **Context Embedding**: Your research context is embedded into a high-dimensional vector
2. **Paper Analysis**: Each paper (title + abstract) is embedded using the same model
3. **Similarity Calculation**: Cosine similarity between embeddings determines relevance
4. **Storage Decision**: You choose whether to store the paper as relevant or discarded
5. **Collection Management**: Papers are ranked, searchable, and exportable

## Future Improvements

Potential enhancements include:

- PDF processing and text extraction
- Integration with arxiv API for automatic paper fetching
- Vector database for scaling to thousands of papers
- Web interface for easier use
- Support for multiple research contexts
- Citation network analysis
- Fine-tuning on your specific domain
- Collaborative paper sharing

## Requirements

- Python 3.8+
- PyTorch
- Sentence Transformers
- NumPy

See `requirements.txt` for specific versions.

## License

MIT License - see LICENSE file for details