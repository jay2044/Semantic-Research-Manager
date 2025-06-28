#!/usr/bin/env python3
"""
Terminal-based Semantic Research Manager
Interactive interface for checking paper relevance
"""

import os
import sys
from semantic_checker import SemanticResearchChecker
from paper_storage import PaperStorage
from arxiv_integration import ArXivIntegration, get_folder_for_relevance


def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print the application header"""
    print("\n" + "="*60)
    print("🔬 SEMANTIC RESEARCH MANAGER")
    print("="*60)
    print("Check paper relevance against your research context\n")


def print_menu():
    """Print the main menu options"""
    print("📋 MAIN MENU:")
    print("1. Add paper manually (title + abstract)")
    print("2. Search and add from ArXiv")
    print("3. View all papers (ranked by relevance)")
    print("4. View relevant papers only")
    print("5. View discarded papers")
    print("6. Search stored papers")
    print("7. View storage statistics")
    print("8. Open papers folder")
    print("9. View current research context")
    print("10. Change research context file")
    print("11. Change embedding model")
    print("12. Export papers")
    print("13. Exit")
    print("-" * 60)


def get_user_input(prompt, required=True):
    """Get user input with validation"""
    while True:
        user_input = input(prompt).strip()
        if user_input or not required:
            return user_input
        print("❌ This field is required. Please try again.")


def add_manual_paper(checker, storage):
    """Add a paper manually with title and abstract"""
    clear_screen()
    print_header()
    print("📝 ADD PAPER MANUALLY")
    print("-" * 60)
    
    # Get paper details
    title = get_user_input("Enter paper title: ")
    print("\nEnter paper abstract (press Enter twice when done):")
    
    lines = []
    while True:
        line = input()
        if line == "" and lines:  # Empty line after content
            break
        lines.append(line)
    
    abstract = "\n".join(lines)
    
    if not abstract.strip():
        print("❌ Abstract cannot be empty.")
        input("Press Enter to continue...")
        return
    
    # Process the paper
    _process_paper(checker, storage, {
        'title': title,
        'abstract': abstract,
        'arxiv_id': None,
        'authors': 'Manual entry',
        'published': 'Unknown'
    })


def search_arxiv_papers(checker, storage):
    """Search ArXiv for papers and add selected ones"""
    clear_screen()
    print_header()
    print("🔍 SEARCH ARXIV")
    print("-" * 60)
    
    # Get search query
    search_type = get_user_input("Search by (1) keyword or (2) ArXiv ID? Enter 1 or 2: ")
    
    arxiv = ArXivIntegration()
    
    if search_type == "1":
        # Keyword search
        query = get_user_input("Enter search keywords: ")
        print(f"\n🔄 Searching ArXiv for: {query}")
        
        papers = arxiv.search_papers(query, max_results=10)
        
        if not papers:
            print("❌ No papers found.")
            input("Press Enter to continue...")
            return
        
        # Display results
        print(f"\n✅ Found {len(papers)} papers:")
        print()
        
        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper['title'][:60]}...")
            print(f"   Authors: {paper.get('authors', 'Unknown')[:50]}...")
            print(f"   ArXiv ID: {paper.get('arxiv_id', 'N/A')}")
            print(f"   Published: {paper.get('published', 'Unknown')}")
            print()
        
        # Let user select paper
        choice = get_user_input(f"\nEnter paper number to analyze (1-{len(papers)}) or 0 to cancel: ")
        
        try:
            choice_num = int(choice)
            if choice_num == 0:
                return
            elif 1 <= choice_num <= len(papers):
                selected_paper = papers[choice_num - 1]
                _process_paper(checker, storage, selected_paper)
            else:
                print("❌ Invalid choice.")
                input("Press Enter to continue...")
        except ValueError:
            print("❌ Please enter a valid number.")
            input("Press Enter to continue...")
    
    elif search_type == "2":
        # ArXiv ID search
        arxiv_id = get_user_input("Enter ArXiv ID (e.g., 2303.08774): ")
        print(f"\n🔄 Fetching paper: {arxiv_id}")
        
        paper = arxiv.get_paper_by_id(arxiv_id)
        
        if not paper:
            print("❌ Paper not found.")
            input("Press Enter to continue...")
            return
        
        # Show paper details
        print(f"\n✅ Found paper:")
        print(f"Title: {paper['title']}")
        print(f"Authors: {paper.get('authors', 'Unknown')}")
        print(f"Published: {paper.get('published', 'Unknown')}")
        print()
        
        confirm = get_user_input("Analyze this paper? (y/N): ")
        if confirm.lower() == 'y':
            _process_paper(checker, storage, paper)
    
    else:
        print("❌ Invalid choice.")
        input("Press Enter to continue...")


def _process_paper(checker, storage, paper_data):
    """Process a paper (check relevance and optionally store)"""
    title = paper_data['title']
    abstract = paper_data['abstract']
    arxiv_id = paper_data.get('arxiv_id')
    
    # Check relevance
    print("\n🔄 Analyzing paper...")
    try:
        result = checker.check_paper_relevance(title, abstract)
        
        # Display results
        print("\n" + "="*60)
        print("📊 ANALYSIS RESULTS:")
        print("="*60)
        print(f"Title: {result['title']}")
        print(f"Abstract length: {result['abstract_length']} characters")
        print(f"Relevance Score: {result['relevance_score']:.2f}%")
        print(f"Category: {result['category']}")
        if arxiv_id:
            print(f"ArXiv ID: {arxiv_id}")
        print("="*60)
        
        # Provide recommendation
        if result['relevance_score'] >= 70:
            print("\n✅ RECOMMENDATION: This paper is highly relevant to your research!")
            print("   You should definitely read this paper.")
        elif result['relevance_score'] >= 50:
            print("\n📋 RECOMMENDATION: This paper is moderately relevant.")
            print("   Consider reading if you have time.")
        elif result['relevance_score'] >= 30:
            print("\n🔍 RECOMMENDATION: This paper has some relevance.")
            print("   Skim the paper for potentially useful insights.")
        else:
            print("\n❌ RECOMMENDATION: This paper has low relevance.")
            print("   You can safely skip this paper.")
        
        # Ask user what to do with the paper
        print("\n" + "-"*60)
        print("💾 STORAGE OPTIONS:")
        print("-"*60)
        
        if result['relevance_score'] >= 30:
            if arxiv_id:
                print("1. Store as relevant paper + download PDF (recommended)")
                print("2. Store as relevant paper (no PDF)")
                print("3. Discard paper")
                print("4. Skip (don't store)")
                
                choice = get_user_input("\nEnter your choice (1-4): ")
                
                if choice == "1":
                    # Store and download PDF
                    paper_id = _store_paper_with_pdf(storage, paper_data, result, download_pdf=True)
                    
                elif choice == "2":
                    # Store without PDF
                    paper_id = _store_paper_with_pdf(storage, paper_data, result, download_pdf=False)
                    
                elif choice == "3":
                    # Store as discarded
                    paper_id = _store_paper_with_pdf(storage, paper_data, result, download_pdf=False)
                    storage.update_paper_status(paper_id, "discarded")
                    print(f"✅ Paper stored as discarded (ID: {paper_id})")
                    
                else:
                    print("📝 Paper not stored.")
            else:
                # No ArXiv ID, so no PDF option
                print("1. Store as relevant paper (recommended)")
                print("2. Discard paper")
                print("3. Skip (don't store)")
                
                choice = get_user_input("\nEnter your choice (1-3): ")
                
                if choice == "1":
                    paper_id = _store_paper_with_pdf(storage, paper_data, result, download_pdf=False)
                elif choice == "2":
                    paper_id = _store_paper_with_pdf(storage, paper_data, result, download_pdf=False)
                    storage.update_paper_status(paper_id, "discarded")
                    print(f"✅ Paper stored as discarded (ID: {paper_id})")
                else:
                    print("📝 Paper not stored.")
        else:
            print("1. Store as discarded paper")
            print("2. Skip (don't store)")
            
            choice = get_user_input("\nEnter your choice (1-2): ")
            
            if choice == "1":
                paper_id = _store_paper_with_pdf(storage, paper_data, result, download_pdf=False)
                storage.update_paper_status(paper_id, "discarded")
                print(f"✅ Paper stored as discarded (ID: {paper_id})")
            else:
                print("📝 Paper not stored.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    input("\nPress Enter to continue...")


def _store_paper_with_pdf(storage, paper_data, result, download_pdf=False):
    """Store paper and optionally download PDF"""
    # Create enhanced paper data
    enhanced_data = {
        'title': paper_data['title'],
        'abstract': paper_data['abstract'],
        'relevance_score': result['relevance_score'],
        'category': result['category'],
        'arxiv_id': paper_data.get('arxiv_id'),
        'authors': paper_data.get('authors', 'Unknown'),
        'published': paper_data.get('published', 'Unknown')
    }
    
    # Store in database
    paper_id = storage.add_paper(
        title=enhanced_data['title'],
        abstract=enhanced_data['abstract'],
        relevance_score=enhanced_data['relevance_score'],
        category=enhanced_data['category']
    )
    
    # Update with additional metadata
    paper = storage.get_paper_by_id(paper_id)
    if paper:
        paper['arxiv_id'] = enhanced_data['arxiv_id']
        paper['authors'] = enhanced_data['authors']
        paper['published'] = enhanced_data['published']
        storage._save_papers()  # Save the updates
    
    print(f"✅ Paper stored (ID: {paper_id})")
    
    # Download PDF if requested and ArXiv ID available
    if download_pdf and enhanced_data['arxiv_id']:
        try:
            arxiv = ArXivIntegration()
            folder_path = get_folder_for_relevance(enhanced_data['relevance_score'])
            
            pdf_path = arxiv.download_pdf(enhanced_data['arxiv_id'], enhanced_data['title'], folder_path)
            
            if pdf_path:
                # Update paper record with PDF path
                paper = storage.get_paper_by_id(paper_id)
                if paper:
                    paper['pdf_path'] = pdf_path
                    storage._save_papers()
                print(f"📁 PDF saved to: {folder_path}")
            
        except Exception as e:
            print(f"⚠️  PDF download failed: {e}")
            print("   Paper stored without PDF.")
    
    return paper_id


def open_papers_folder():
    """Open the papers folder in file explorer"""
    import subprocess
    import platform
    
    folder_path = "papers"
    
    # Create folder if it doesn't exist
    os.makedirs(folder_path, exist_ok=True)
    
    try:
        if platform.system() == "Windows":
            subprocess.run(["explorer", folder_path])
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", folder_path])
        else:  # Linux
            subprocess.run(["xdg-open", folder_path])
        
        print(f"✅ Opened folder: {folder_path}")
        
    except Exception as e:
        print(f"❌ Could not open folder: {e}")
        print(f"Papers folder location: {os.path.abspath(folder_path)}")
    
    input("\nPress Enter to continue...")


def view_all_papers(storage):
    """View all papers ranked by relevance"""
    clear_screen()
    print_header()
    print("📚 ALL PAPERS (RANKED BY RELEVANCE)")
    print("-" * 60)
    
    papers = storage.get_papers_by_relevance()
    
    if not papers:
        print("📝 No papers stored yet.")
        input("Press Enter to continue...")
        return
    
    print(f"Total papers: {len(papers)}")
    print()
    
    for i, paper in enumerate(papers, 1):
        status_icon = "✅" if paper["status"] == "relevant" else "❌"
        pdf_icon = "📄" if paper.get('pdf_path') else "📝"
        
        print(f"{i}. {status_icon}{pdf_icon} {paper['title'][:50]}...")
        print(f"   Relevance: {paper['relevance_score']:.2f}% - {paper['category']}")
        print(f"   Status: {paper['status']} | Added: {paper['added_date'][:10]}")
        if paper.get('arxiv_id'):
            print(f"   ArXiv: {paper['arxiv_id']}")
        print()
    
    # Show action options
    print("-" * 60)
    print("Actions:")
    print("1. View paper details")
    print("2. Change paper status")
    print("3. Delete paper")
    print("4. Back to main menu")
    
    choice = get_user_input("\nEnter your choice (1-4): ")
    
    if choice == "1":
        view_paper_details(storage)
    elif choice == "2":
        change_paper_status(storage)
    elif choice == "3":
        delete_paper(storage)
    # Choice 4 just returns to main menu


def view_paper_details(storage):
    """View detailed information about a specific paper"""
    paper_num = get_user_input("Enter paper number to view details: ")
    
    try:
        paper_num = int(paper_num)
        papers = storage.get_papers_by_relevance()
        
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            
            clear_screen()
            print_header()
            print("📄 PAPER DETAILS")
            print("-" * 60)
            print(f"Title: {paper['title']}")
            print(f"ID: {paper['id']}")
            print(f"Relevance: {paper['relevance_score']:.2f}% - {paper['category']}")
            print(f"Status: {paper['status']}")
            print(f"Added: {paper['added_date']}")
            if paper.get('arxiv_id'):
                print(f"ArXiv ID: {paper['arxiv_id']}")
            if paper.get('authors'):
                print(f"Authors: {paper['authors']}")
            if paper.get('published'):
                print(f"Published: {paper['published']}")
            if paper.get('pdf_path'):
                print(f"PDF: {paper['pdf_path']}")
            print(f"Abstract length: {paper['abstract_length']} characters")
            print("\nAbstract:")
            print("-" * 40)
            print(paper['abstract'])
            print("-" * 40)
            
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("\nPress Enter to continue...")


def change_paper_status(storage):
    """Change the status of a paper"""
    paper_num = get_user_input("Enter paper number to change status: ")
    
    try:
        paper_num = int(paper_num)
        papers = storage.get_papers_by_relevance()
        
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            
            print(f"\nCurrent status: {paper['status']}")
            print("New status:")
            print("1. relevant")
            print("2. discarded")
            
            choice = get_user_input("Enter choice (1-2): ")
            
            new_status = "relevant" if choice == "1" else "discarded"
            storage.update_paper_status(paper['id'], new_status)
            print(f"✅ Paper status updated to: {new_status}")
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("\nPress Enter to continue...")


def delete_paper(storage):
    """Delete a paper from storage"""
    paper_num = get_user_input("Enter paper number to delete: ")
    
    try:
        paper_num = int(paper_num)
        papers = storage.get_papers_by_relevance()
        
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            
            confirm = get_user_input(f"Are you sure you want to delete '{paper['title'][:30]}...'? (y/N): ")
            
            if confirm.lower() == 'y':
                if storage.delete_paper(paper['id']):
                    print("✅ Paper deleted successfully.")
                else:
                    print("❌ Failed to delete paper.")
            else:
                print("📝 Deletion cancelled.")
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("\nPress Enter to continue...")


def view_relevant_papers(storage):
    """View only relevant papers"""
    clear_screen()
    print_header()
    print("✅ RELEVANT PAPERS")
    print("-" * 60)
    
    papers = storage.get_papers_by_status("relevant")
    
    if not papers:
        print("📝 No relevant papers stored.")
        input("Press Enter to continue...")
        return
    
    print(f"Relevant papers: {len(papers)}")
    print()
    
    for i, paper in enumerate(papers, 1):
        pdf_icon = "📄" if paper.get('pdf_path') else "📝"
        print(f"{i}. {pdf_icon} {paper['title'][:60]}...")
        print(f"   Relevance: {paper['relevance_score']:.2f}% - {paper['category']}")
        print(f"   Added: {paper['added_date'][:10]}")
        if paper.get('arxiv_id'):
            print(f"   ArXiv: {paper['arxiv_id']}")
        print()
    
    input("Press Enter to continue...")


def view_discarded_papers(storage):
    """View only discarded papers"""
    clear_screen()
    print_header()
    print("❌ DISCARDED PAPERS")
    print("-" * 60)
    
    papers = storage.get_papers_by_status("discarded")
    
    if not papers:
        print("📝 No discarded papers stored.")
        input("Press Enter to continue...")
        return
    
    print(f"Discarded papers: {len(papers)}")
    print()
    
    for i, paper in enumerate(papers, 1):
        print(f"{i}. {paper['title'][:60]}...")
        print(f"   Relevance: {paper['relevance_score']:.2f}% - {paper['category']}")
        print(f"   Added: {paper['added_date'][:10]}")
        if paper.get('arxiv_id'):
            print(f"   ArXiv: {paper['arxiv_id']}")
        print()
    
    input("Press Enter to continue...")


def search_papers(storage):
    """Search papers by title or abstract"""
    clear_screen()
    print_header()
    print("🔍 SEARCH STORED PAPERS")
    print("-" * 60)
    
    query = get_user_input("Enter search term: ")
    
    if not query:
        print("❌ Search term cannot be empty.")
        input("Press Enter to continue...")
        return
    
    results = storage.search_papers(query)
    
    if not results:
        print(f"📝 No papers found matching '{query}'.")
        input("Press Enter to continue...")
        return
    
    print(f"\nFound {len(results)} papers matching '{query}':")
    print()
    
    for i, paper in enumerate(results, 1):
        status_icon = "✅" if paper["status"] == "relevant" else "❌"
        pdf_icon = "📄" if paper.get('pdf_path') else "📝"
        
        print(f"{i}. {status_icon}{pdf_icon} {paper['title'][:50]}...")
        print(f"   Relevance: {paper['relevance_score']:.2f}% - {paper['category']}")
        print(f"   Status: {paper['status']}")
        if paper.get('arxiv_id'):
            print(f"   ArXiv: {paper['arxiv_id']}")
        print()
    
    input("Press Enter to continue...")


def view_statistics(storage):
    """View storage statistics"""
    clear_screen()
    print_header()
    print("📊 STORAGE STATISTICS")
    print("-" * 60)
    
    stats = storage.get_statistics()
    
    print(f"Total papers: {stats['total_papers']}")
    print(f"Relevant papers: {stats['relevant_papers']}")
    print(f"Discarded papers: {stats['discarded_papers']}")
    print(f"Average relevance: {stats['average_relevance']}%")
    print(f"Highly relevant (≥70%): {stats['highly_relevant']}")
    print(f"Moderately relevant (50-69%): {stats['moderately_relevant']}")
    
    if stats['total_papers'] > 0:
        relevant_percentage = (stats['relevant_papers'] / stats['total_papers']) * 100
        print(f"Relevance rate: {relevant_percentage:.1f}%")
    
    # Count papers with PDFs
    papers_with_pdfs = len([p for p in storage.papers if p.get('pdf_path')])
    print(f"Papers with PDFs: {papers_with_pdfs}")
    
    input("\nPress Enter to continue...")


def export_papers(storage):
    """Export papers to JSON file"""
    clear_screen()
    print_header()
    print("📤 EXPORT PAPERS")
    print("-" * 60)
    
    print("Export options:")
    print("1. All papers")
    print("2. Relevant papers only")
    print("3. Discarded papers only")
    
    choice = get_user_input("\nEnter choice (1-3): ")
    
    filename = get_user_input("Enter filename (e.g., papers_export.json): ")
    
    if not filename.endswith('.json'):
        filename += '.json'
    
    try:
        if choice == "1":
            storage.export_papers(filename)
            status_filter = None
        elif choice == "2":
            storage.export_papers(filename, "relevant")
            status_filter = "relevant"
        elif choice == "3":
            storage.export_papers(filename, "discarded")
            status_filter = "discarded"
        else:
            print("❌ Invalid choice.")
            input("Press Enter to continue...")
            return
        
        papers_count = len(storage.get_papers_by_status(status_filter) if status_filter else storage.papers)
        print(f"✅ Exported {papers_count} papers to {filename}")
        
    except Exception as e:
        print(f"❌ Error exporting papers: {e}")
    
    input("Press Enter to continue...")


def view_research_context(checker):
    """Display current research context"""
    clear_screen()
    print_header()
    print("📖 CURRENT RESEARCH CONTEXT")
    print("-" * 60)
    
    if checker.context_text:
        print(checker.context_text)
        print(f"\nContext length: {len(checker.context_text)} characters")
    else:
        print("❌ No research context loaded.")
    
    input("\nPress Enter to continue...")


def change_context_file(checker):
    """Change the research context file"""
    clear_screen()
    print_header()
    print("📁 CHANGE RESEARCH CONTEXT FILE")
    print("-" * 60)
    
    current_file = getattr(checker, '_context_file', 'research_context.txt')
    print(f"Current context file: {current_file}")
    
    new_file = get_user_input("\nEnter new context file path (or press Enter to keep current): ", required=False)
    
    if not new_file:
        print("Keeping current context file.")
        input("Press Enter to continue...")
        return
    
    try:
        checker.load_research_context(new_file)
        checker._context_file = new_file
        print(f"✅ Successfully loaded context from: {new_file}")
    except Exception as e:
        print(f"❌ Error loading context file: {e}")
    
    input("Press Enter to continue...")


def change_model(checker):
    """Change the embedding model"""
    clear_screen()
    print_header()
    print("🤖 CHANGE EMBEDDING MODEL")
    print("-" * 60)
    
    current_model = getattr(checker.model, 'name_or_path', 'all-mpnet-base-v2')
    print(f"Current model: {current_model}")
    
    print("\nAvailable models:")
    print("1. all-mpnet-base-v2 (default, balanced)")
    print("2. all-MiniLM-L6-v2 (faster, less accurate)")
    print("3. allenai/specter2 (scientific text optimized)")
    print("4. Custom model name")
    
    choice = get_user_input("\nEnter choice (1-4): ")
    
    model_map = {
        '1': 'all-mpnet-base-v2',
        '2': 'all-MiniLM-L6-v2',
        '3': 'allenai/specter2'
    }
    
    if choice in model_map:
        new_model = model_map[choice]
    elif choice == '4':
        new_model = get_user_input("Enter custom model name: ")
    else:
        print("❌ Invalid choice. Keeping current model.")
        input("Press Enter to continue...")
        return
    
    try:
        print(f"\n🔄 Loading new model: {new_model}")
        checker.model = checker.model.__class__(new_model)
        print("✅ Model changed successfully!")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
    
    input("Press Enter to continue...")


def main():
    """Main application loop"""
    try:
        # Initialize checker and storage
        print("🔄 Initializing Semantic Research Manager...")
        checker = SemanticResearchChecker()
        storage = PaperStorage()
        
        # Load default context
        try:
            checker.load_research_context('research_context.txt')
            checker._context_file = 'research_context.txt'
        except FileNotFoundError:
            print("⚠️  Warning: research_context.txt not found. Please set up your research context.")
            checker.context_text = None
        
        # Main loop
        while True:
            clear_screen()
            print_header()
            print_menu()
            
            choice = get_user_input("Enter your choice (1-13): ")
            
            if choice == '1':
                add_manual_paper(checker, storage)
            elif choice == '2':
                search_arxiv_papers(checker, storage)
            elif choice == '3':
                view_all_papers(storage)
            elif choice == '4':
                view_relevant_papers(storage)
            elif choice == '5':
                view_discarded_papers(storage)
            elif choice == '6':
                search_papers(storage)
            elif choice == '7':
                view_statistics(storage)
            elif choice == '8':
                open_papers_folder()
            elif choice == '9':
                view_research_context(checker)
            elif choice == '10':
                change_context_file(checker)
            elif choice == '11':
                change_model(checker)
            elif choice == '12':
                export_papers(storage)
            elif choice == '13':
                print("\n👋 Thank you for using Semantic Research Manager!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-13.")
                input("Press Enter to continue...")
                
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main() 