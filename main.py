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


def open_pdf_file(pdf_path):
    """Open a PDF file using the system's default PDF viewer"""
    import subprocess
    import platform
    import os
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    try:
        if platform.system() == "Windows":
            os.startfile(pdf_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", pdf_path])
        else:  # Linux
            subprocess.run(["xdg-open", pdf_path])
        
        print(f"✅ Opening PDF: {os.path.basename(pdf_path)}")
        return True
        
    except Exception as e:
        print(f"❌ Could not open PDF: {e}")
        print(f"PDF location: {os.path.abspath(pdf_path)}")
        return False


def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print the application header"""
    print("\n" + "="*60)
    print("🔬 SEMANTIC RESEARCH MANAGER")
    print("="*60)
    print("Check paper relevance against your research context\n")


def print_statistics(storage):
    """Print storage statistics at the top of the interface"""
    stats = storage.get_statistics()
    
    print("📊 PAPER STATISTICS:")
    print(f"📚 To Read: {stats['to_read_papers']} | 📖 Reading: {stats['reading_papers']} | ✅ Read: {stats['read_papers']} | ❌ Discarded: {stats['discarded_papers']}")
    
    if stats['total_papers'] > 0:
        non_discarded = stats['to_read_papers'] + stats['reading_papers'] + stats['read_papers']
        if non_discarded > 0:
            completion_rate = (stats['read_papers'] / non_discarded) * 100
            print(f"📈 Reading Progress: {completion_rate:.1f}% complete | 📄 PDFs: {len([p for p in storage.papers if p.get('pdf_path')])}")
    
    print("-" * 60)


def print_menu():
    """Print the main menu options"""
    print("📋 MAIN MENU:")
    print("1. Search and add from ArXiv")
    print("2. Add paper manually (title + abstract)")
    print("3. View all papers (ranked by relevance)")
    print("4. View papers by status")
    print("5. Search stored papers")
    print("6. 🎯 Show top 10 papers to read next")
    print("7. 🎲 Pick random paper to read")
    print("8. 📖 Manage reading queue")
    print("9. Open papers folder")
    print("10. Manage research context")
    print("11. Change embedding model")
    print("12. Export papers")
    print("13. Recalculate embeddings & relevance")
    print("14. 📚 Mass add papers from ArXiv IDs")
    print("15. Exit")
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
    print_statistics(storage)
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
    print_statistics(storage)
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
        
        confirm = get_user_input("Analyze this paper? (Y/n): ")
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
        if result['relevance_score'] >= 85:
            print("\n✅ RECOMMENDATION: This paper is highly relevant to your research!")
            print("   You should definitely read this paper.")
        elif result['relevance_score'] >= 65:
            print("\n📋 RECOMMENDATION: This paper is moderately relevant.")
            print("   Consider reading if you have time.")
        elif result['relevance_score'] >= 45:
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
                print("1. Add to reading list + download PDF (recommended)")
                print("2. Add to reading list (no PDF)")
                print("3. Discard paper")
                print("4. Skip (don't store)")
                
                choice = get_user_input("\nEnter your choice (1-4): ")
                
                if choice == "1":
                    # Store and download PDF (defaults to "to read" status)
                    paper_id = _store_paper_with_pdf(storage, paper_data, result, download_pdf=True)
                    
                elif choice == "2":
                    # Store without PDF (defaults to "to read" status)
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
                print("1. Add to reading list (recommended)")
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
    
    print(f"✅ Paper stored with status 'to read' (ID: {paper_id})")
    
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
    """View all papers ranked by relevance with pagination"""
    papers = storage.get_papers_by_relevance()
    display_papers_with_pagination(papers, "📚 ALL PAPERS (RANKED BY RELEVANCE)", storage)


def display_papers_with_pagination(papers, title, storage, page_size=10):
    """Display papers with pagination support"""
    if not papers:
        print(f"📝 No papers found.")
        input("Press Enter to continue...")
        return
    
    total_papers = len(papers)
    total_pages = (total_papers + page_size - 1) // page_size
    current_page = 1
    
    while True:
        clear_screen()
        print_header()
        print_statistics(storage)
        print(title)
        print("-" * 60)
        
        # Calculate start and end indices for current page
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_papers)
        current_papers = papers[start_idx:end_idx]
        
        print(f"Total papers: {total_papers} | Page {current_page} of {total_pages}")
        print(f"Showing papers {start_idx + 1}-{end_idx}")
        print()
        
        # Display papers for current page
        for i, paper in enumerate(current_papers, start_idx + 1):
            # Use status icons
            status_icons = {
                "to read": "📚",
                "reading": "📖", 
                "read": "✅",
                "discarded": "❌"
            }
            status_icon = status_icons.get(paper["status"], "📄")
            pdf_icon = "📄" if paper.get('pdf_path') else "📝"
            
            print(f"{i}. {status_icon}{pdf_icon} {paper['title'][:50]}...")
            print(f"   Relevance: {paper['relevance_score']:.2f}% - {paper['category']}")
            print(f"   Status: {paper['status']} | Added: {paper['added_date'][:10]}")
            if paper.get('arxiv_id'):
                print(f"   ArXiv: {paper['arxiv_id']}")
            print()
        
        # Show pagination controls
        print("-" * 60)
        print("📄 PAGINATION CONTROLS:")
        
        if total_pages > 1:
            if current_page > 1:
                print("◀️  Previous page (p)")
            if current_page < total_pages:
                print("▶️  Next page (n)")
            print(f"📄 Go to page (g1-{total_pages})")
        
        print("📋 ACTIONS:")
        print("1. View paper details")
        print("2. Change paper status")
        print("3. Delete paper")
        print("4. Open PDF (if available)")
        print("5. Back to main menu")
        
        choice = get_user_input("\nEnter your choice: ").lower()
        
        if choice == 'p' and current_page > 1:
            current_page -= 1
        elif choice == 'n' and current_page < total_pages:
            current_page += 1
        elif choice.startswith('g') and choice[1:].isdigit():
            # Go to specific page
            page_num = int(choice[1:])
            if 1 <= page_num <= total_pages:
                current_page = page_num
            else:
                print("❌ Invalid page number.")
                input("Press Enter to continue...")
        elif choice.isdigit():
            # Handle actions
            choice_num = int(choice)
            if choice_num == 1:
                view_paper_details_from_paginated_list(storage, papers, current_page, page_size)
            elif choice_num == 2:
                change_paper_status_from_paginated_list(storage, papers, current_page, page_size)
            elif choice_num == 3:
                delete_paper_from_paginated_list(storage, papers, current_page, page_size)
            elif choice_num == 4:
                open_pdf_from_paginated_list(storage, papers, current_page, page_size)
            elif choice_num == 5:
                return
            else:
                print("❌ Invalid choice.")
                input("Press Enter to continue...")
        else:
            print("❌ Invalid choice.")
            input("Press Enter to continue...")


def view_paper_details_from_paginated_list(storage, papers, current_page, page_size):
    """View paper details from a paginated list"""
    if not papers:
        return
        
    paper_num = get_user_input(f"Enter paper number to view details (1-{len(papers)}): ")
    
    try:
        paper_num = int(paper_num)
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            _show_paper_details(paper)
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("Press Enter to continue...")


def change_paper_status_from_paginated_list(storage, papers, current_page, page_size):
    """Change paper status from a paginated list"""
    if not papers:
        return
        
    paper_num = get_user_input(f"Enter paper number to change status (1-{len(papers)}): ")
    
    try:
        paper_num = int(paper_num)
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            _change_paper_status_interactive(storage, paper)
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("Press Enter to continue...")


def delete_paper_from_paginated_list(storage, papers, current_page, page_size):
    """Delete paper from a paginated list"""
    if not papers:
        return
        
    paper_num = get_user_input(f"Enter paper number to delete (1-{len(papers)}): ")
    
    try:
        paper_num = int(paper_num)
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            
            confirm = get_user_input(f"Are you sure you want to delete '{paper['title'][:30]}...'? (Y/n): ")
            
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
    
    input("Press Enter to continue...")


def open_pdf_from_paginated_list(storage, papers, current_page, page_size):
    """Open PDF from a paginated list"""
    if not papers:
        return
        
    paper_num = get_user_input(f"Enter paper number to open PDF (1-{len(papers)}): ")
    
    try:
        paper_num = int(paper_num)
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            
            if paper.get('pdf_path'):
                open_pdf_file(paper['pdf_path'])
            else:
                print("❌ No PDF available for this paper.")
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("Press Enter to continue...")


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
            
            # Show notes if any
            if paper.get('notes'):
                print(f"\nNotes:")
                print("-" * 20)
                print(paper['notes'])
                print("-" * 20)
            
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
            _change_paper_status_interactive(storage, paper)
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
            
            confirm = get_user_input(f"Are you sure you want to delete '{paper['title'][:30]}...'? (Y/n): ")
            
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
    
    input("Press Enter to continue...")


def view_papers_by_status(storage):
    """View papers filtered by status"""
    clear_screen()
    print_header()
    print_statistics(storage)
    print("📋 VIEW PAPERS BY STATUS")
    print("-" * 60)
    
    # Show status options with counts
    valid_statuses = storage.get_valid_statuses()
    print("Select status to view:")
    
    for i, status in enumerate(valid_statuses, 1):
        count = len(storage.get_papers_by_status(status))
        status_icon = {
            "to read": "📚",
            "reading": "📖", 
            "read": "✅",
            "discarded": "❌"
        }.get(status, "📄")
        
        print(f"{i}. {status_icon} {status.title()} ({count} papers)")
    
    print("5. All papers")
    print("6. Back to main menu")
    
    choice = get_user_input(f"\nEnter choice (1-6): ")
    
    try:
        choice_num = int(choice)
        if 1 <= choice_num <= 4:
            selected_status = valid_statuses[choice_num - 1]
            _display_papers_by_status(storage, selected_status)
        elif choice_num == 5:
            view_all_papers(storage)
            return
        elif choice_num == 6:
            return
        else:
            print("❌ Invalid choice.")
            input("Press Enter to continue...")
    except ValueError:
        print("❌ Please enter a valid number.")
        input("Press Enter to continue...")


def _display_papers_by_status(storage, status):
    """Display papers with a specific status using pagination"""
    papers = storage.get_papers_by_status(status)
    
    # Sort papers by relevance score (highest first)
    papers = sorted(papers, key=lambda x: x["relevance_score"], reverse=True)
    
    status_icons = {
        "to read": "📚",
        "reading": "📖", 
        "read": "✅",
        "discarded": "❌"
    }
    
    status_icon = status_icons.get(status, "📄")
    title = f"{status_icon} {status.upper()} PAPERS"
    
    display_papers_with_pagination(papers, title, storage)


def view_paper_details_from_status_list(storage, papers):
    """View paper details from a status-filtered list"""
    if not papers:
        return
        
    paper_num = get_user_input(f"Enter paper number to view details (1-{len(papers)}): ")
    
    try:
        paper_num = int(paper_num)
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            _show_paper_details(paper)
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("\nPress Enter to continue...")


def change_paper_status_from_status_list(storage, papers):
    """Change paper status from a status-filtered list"""
    if not papers:
        return
        
    paper_num = get_user_input(f"Enter paper number to change status (1-{len(papers)}): ")
    
    try:
        paper_num = int(paper_num)
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            _change_paper_status_interactive(storage, paper)
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("\nPress Enter to continue...")


def delete_paper_from_status_list(storage, papers):
    """Delete paper from a status-filtered list"""
    if not papers:
        return
        
    paper_num = get_user_input(f"Enter paper number to delete (1-{len(papers)}): ")
    
    try:
        paper_num = int(paper_num)
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            
            confirm = get_user_input(f"Are you sure you want to delete '{paper['title'][:30]}...'? (Y/n): ")
            
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
    
    input("Press Enter to continue...")


def _show_paper_details(paper):
    """Helper function to display detailed paper information"""
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
    
    # Show embedding status
    if paper.get('embedding_needs_update'):
        print("🔄 Embedding update needed (notes added/modified)")
    elif paper.get('embedding_updated_date'):
        print(f"✅ Embedding updated: {paper['embedding_updated_date'][:10]}")
    
    # Show notes if any
    if paper.get('notes'):
        print(f"\nNotes:")
        print("-" * 20)
        print(paper['notes'])
        print("-" * 20)
    
    print("\nAbstract:")
    print("-" * 40)
    print(paper['abstract'])
    print("-" * 40)
    
    # Add PDF opening option if PDF exists
    if paper.get('pdf_path'):
        print("\n" + "-" * 60)
        print("📄 PDF ACTIONS:")
        print("-" * 60)
        print("1. Open PDF")
        print("2. Back to previous menu")
        
        choice = get_user_input("\nEnter your choice (1-2): ")
        
        if choice == "1":
            open_pdf_file(paper['pdf_path'])
            input("Press Enter to continue...")


def _change_paper_status_interactive(storage, paper):
    """Helper function to change paper status interactively"""
    print(f"\nCurrent status: {paper['status']}")
    print("Select new status:")
    
    valid_statuses = storage.get_valid_statuses()
    status_icons = {
        "to read": "📚",
        "reading": "📖", 
        "read": "✅",
        "discarded": "❌"
    }
    
    for i, status in enumerate(valid_statuses, 1):
        icon = status_icons.get(status, "📄")
        current_indicator = " (current)" if status == paper['status'] else ""
        print(f"{i}. {icon} {status.title()}{current_indicator}")
    
    choice = get_user_input(f"\nEnter choice (1-{len(valid_statuses)}): ")
    
    try:
        choice_num = int(choice)
        if 1 <= choice_num <= len(valid_statuses):
            new_status = valid_statuses[choice_num - 1]
            if new_status != paper['status']:
                storage.update_paper_status(paper['id'], new_status)
                print(f"✅ Paper status updated to: {new_status}")
            else:
                print("📝 Status unchanged.")
        else:
            print("❌ Invalid choice.")
    except ValueError:
        print("❌ Please enter a valid number.")


def search_papers(storage):
    """Search papers by title or abstract with pagination"""
    clear_screen()
    print_header()
    print_statistics(storage)
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
    
    display_search_results_with_pagination(results, query, storage)


def display_search_results_with_pagination(results, query, storage, page_size=10):
    """Display search results with pagination"""
    if not results:
        print(f"📝 No papers found matching '{query}'.")
        input("Press Enter to continue...")
        return
    
    total_papers = len(results)
    total_pages = (total_papers + page_size - 1) // page_size
    current_page = 1
    
    while True:
        clear_screen()
        print_header()
        print_statistics(storage)
        print("🔍 SEARCH RESULTS")
        print("-" * 60)
        
        # Calculate start and end indices for current page
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_papers)
        current_papers = results[start_idx:end_idx]
        
        print(f"Found {total_papers} papers matching '{query}'")
        print(f"Page {current_page} of {total_pages} | Showing papers {start_idx + 1}-{end_idx}")
        print()
        
        # Display papers for current page
        for i, paper in enumerate(current_papers, start_idx + 1):
            # Use status icons
            status_icons = {
                "to read": "📚",
                "reading": "📖", 
                "read": "✅",
                "discarded": "❌"
            }
            status_icon = status_icons.get(paper["status"], "📄")
            pdf_icon = "📄" if paper.get('pdf_path') else "📝"
            
            print(f"{i}. {status_icon}{pdf_icon} {paper['title'][:50]}...")
            print(f"   Relevance: {paper['relevance_score']:.2f}% - {paper['category']}")
            print(f"   Status: {paper['status']}")
            if paper.get('arxiv_id'):
                print(f"   ArXiv: {paper['arxiv_id']}")
            if paper.get('notes'):
                print(f"   Note: {paper['notes'][:50]}...")
            print()
        
        # Show pagination controls
        print("-" * 60)
        print("📄 PAGINATION CONTROLS:")
        
        if total_pages > 1:
            if current_page > 1:
                print("◀️  Previous page (p)")
            if current_page < total_pages:
                print("▶️  Next page (n)")
            print(f"📄 Go to page (g1-{total_pages})")
        
        print("📋 ACTIONS:")
        print("1. Change paper status")
        print("2. Add/edit notes")
        print("3. View paper details")
        print("4. Discard papers")
        print("5. Open PDF (if available)")
        print("6. Back to main menu")
        
        choice = get_user_input("\nEnter your choice: ").lower()
        
        if choice == 'p' and current_page > 1:
            current_page -= 1
        elif choice == 'n' and current_page < total_pages:
            current_page += 1
        elif choice.startswith('g') and choice[1:].isdigit():
            # Go to specific page
            page_num = int(choice[1:])
            if 1 <= page_num <= total_pages:
                current_page = page_num
            else:
                print("❌ Invalid page number.")
                input("Press Enter to continue...")
        elif choice.isdigit():
            # Handle actions
            choice_num = int(choice)
            if choice_num == 1:
                change_paper_status_from_search(storage, results)
            elif choice_num == 2:
                edit_paper_notes_from_list(storage, results)
            elif choice_num == 3:
                view_paper_details_from_list(storage, results)
            elif choice_num == 4:
                discard_papers_from_search(storage, results)
            elif choice_num == 5:
                open_pdf_from_search_results(storage, results)
            elif choice_num == 6:
                return
            else:
                print("❌ Invalid choice.")
                input("Press Enter to continue...")
        else:
            print("❌ Invalid choice.")
            input("Press Enter to continue...")


def change_paper_status_from_search(storage, papers):
    """Change paper status from search results"""
    if not papers:
        return
        
    paper_num = get_user_input(f"Enter paper number to change status (1-{len(papers)}): ")
    
    try:
        paper_num = int(paper_num)
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            _change_paper_status_interactive(storage, paper)
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("Press Enter to continue...")


def discard_papers_from_search(storage, papers):
    """Discard papers from search results"""
    if not papers:
        return
        
    paper_num = get_user_input(f"Enter paper number to discard (1-{len(papers)}): ")
    
    try:
        paper_num = int(paper_num)
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            confirm = get_user_input(f"Discard '{paper['title'][:30]}...'? (Y/n): ")
            
            if confirm.lower() == 'y':
                storage.update_paper_status(paper['id'], "discarded")
                print(f"✅ Paper discarded: {paper['title'][:40]}...")
            else:
                print("📝 Action cancelled.")
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("Press Enter to continue...")


def view_statistics(storage):
    """View storage statistics"""
    clear_screen()
    print_header()
    print("📊 STORAGE STATISTICS")
    print("-" * 60)
    
    stats = storage.get_statistics()
    
    print(f"Total papers: {stats['total_papers']}")
    print()
    print("📊 Papers by Status:")
    print(f"📚 To Read: {stats['to_read_papers']}")
    print(f"📖 Reading: {stats['reading_papers']}")
    print(f"✅ Read: {stats['read_papers']}")
    print(f"❌ Discarded: {stats['discarded_papers']}")
    print()
    print("📈 Relevance Analysis:")
    print(f"Average relevance: {stats['average_relevance']}%")
    print(f"Highly relevant (≥85%): {stats['highly_relevant']}")
    print(f"Moderately relevant (65-84%): {stats['moderately_relevant']}")
    
    if stats['total_papers'] > 0:
        # Calculate completion rate (read papers vs total non-discarded papers)
        non_discarded = stats['to_read_papers'] + stats['reading_papers'] + stats['read_papers']
        if non_discarded > 0:
            completion_rate = (stats['read_papers'] / non_discarded) * 100
            print(f"Reading completion rate: {completion_rate:.1f}%")
    
    # Count papers with PDFs
    papers_with_pdfs = len([p for p in storage.papers if p.get('pdf_path')])
    print(f"Papers with PDFs: {papers_with_pdfs}")
    
    input("\nPress Enter to continue...")


def export_papers(storage):
    """Export papers to JSON file"""
    clear_screen()
    print_header()
    print_statistics(storage)
    print("📤 EXPORT PAPERS")
    print("-" * 60)
    
    print("Export options:")
    print("1. All papers")
    print("2. To Read papers only")
    print("3. Reading papers only")
    print("4. Read papers only")
    print("5. Discarded papers only")
    
    choice = get_user_input("\nEnter choice (1-5): ")
    
    filename = get_user_input("Enter filename (e.g., papers_export.json): ")
    
    if not filename.endswith('.json'):
        filename += '.json'
    
    try:
        if choice == "1":
            storage.export_papers(filename)
            status_filter = None
        elif choice == "2":
            storage.export_papers(filename, "to read")
            status_filter = "to read"
        elif choice == "3":
            storage.export_papers(filename, "reading")
            status_filter = "reading"
        elif choice == "4":
            storage.export_papers(filename, "read")
            status_filter = "read"
        elif choice == "5":
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


def manage_research_context(checker):
    """Manage research context - view, edit, snippets, or change file"""
    clear_screen()
    print_header()
    print("📖 MANAGE RESEARCH CONTEXT")
    print("-" * 60)
    
    current_file = getattr(checker, '_context_file', 'research_context.txt')
    print(f"Current context file: {current_file}")
    
    if checker.context_text:
        base_context_length = len(checker._extract_base_context() if hasattr(checker, '_extract_base_context') else checker.context_text)
        snippets_count = len(checker.context_snippets) if hasattr(checker, 'context_snippets') else 0
        print(f"Base context: {base_context_length} characters")
        print(f"Research snippets: {snippets_count}")
        print(f"Status: ✅ Loaded")
    else:
        print("Status: ❌ Not loaded")
    
    print("\nOptions:")
    print("1. View current context")
    print("2. Edit base context in CLI")
    print("3. Manage research snippets")
    print("4. Change context file")
    print("5. Back to main menu")
    
    choice = get_user_input("\nEnter choice (1-5): ")
    
    if choice == "1":
        view_research_context(checker)
    elif choice == "2":
        edit_context_in_cli(checker)
    elif choice == "3":
        manage_context_snippets(checker)
    elif choice == "4":
        change_context_file(checker)
    elif choice == "5":
        return
    else:
        print("❌ Invalid choice.")
        input("Press Enter to continue...")


def edit_context_in_cli(checker):
    """Edit research context directly in the CLI"""
    clear_screen()
    print_header()
    print("✏️  EDIT RESEARCH CONTEXT")
    print("-" * 60)
    
    current_file = getattr(checker, '_context_file', 'research_context.txt')
    print(f"Editing: {current_file}")
    print()
    
    if checker.context_text:
        print("Current context:")
        print("-" * 40)
        print(checker.context_text)
        print("-" * 40)
        print()
    
    print("Enter your new research context below.")
    print("Press Enter twice when finished:")
    print()
    
    lines = []
    while True:
        line = input()
        if line == "" and lines:  # Empty line after content
            break
        lines.append(line)
    
    new_context = "\n".join(lines)
    
    if not new_context.strip():
        print("❌ Context cannot be empty.")
        input("Press Enter to continue...")
        return
    
    # Save to file
    try:
        with open(current_file, 'w', encoding='utf-8') as f:
            f.write(new_context)
        
        # Reload context
        checker.load_research_context(current_file)
        print(f"✅ Context updated and saved to {current_file}")
        print(f"   New length: {len(new_context)} characters")
        
    except Exception as e:
        print(f"❌ Error saving context: {e}")
    
    input("Press Enter to continue...")


def change_context_file(checker):
    """Change the research context file"""
    clear_screen()
    print_header()
    print("📁 CHANGE RESEARCH CONTEXT FILE")
    print("-" * 60)
    
    current_file = getattr(checker, '_context_file', 'research_context.txt')
    print(f"Current context file: {current_file}")
    
    print("\nOptions:")
    print("1. Enter path to existing file")
    print("2. Create new context file")
    print("3. Back to context management")
    
    choice = get_user_input("\nEnter choice (1-3): ")
    
    if choice == "1":
        new_file = get_user_input("Enter path to existing context file: ")
        if not new_file:
            print("❌ No file path provided.")
            input("Press Enter to continue...")
            return
        
        try:
            checker.load_research_context(new_file)
            checker._context_file = new_file
            print(f"✅ Successfully loaded context from: {new_file}")
        except Exception as e:
            print(f"❌ Error loading context file: {e}")
    
    elif choice == "2":
        new_file = get_user_input("Enter path for new context file: ")
        if not new_file:
            print("❌ No file path provided.")
            input("Press Enter to continue...")
            return
        
        try:
            # Create empty file
            with open(new_file, 'w', encoding='utf-8') as f:
                f.write("# Research Context\n\nEnter your research context here...")
            
            checker.load_research_context(new_file)
            checker._context_file = new_file
            print(f"✅ Created and loaded new context file: {new_file}")
            print("   You can now edit it using the 'Edit context in CLI' option.")
            
        except Exception as e:
            print(f"❌ Error creating context file: {e}")
    
    elif choice == "3":
        return
    
    else:
        print("❌ Invalid choice.")
    
    input("Press Enter to continue...")


def change_model(checker):
    """Change the embedding model"""
    clear_screen()
    print_header()
    print("🤖 CHANGE EMBEDDING MODEL")
    print("-" * 60)
    
    current_model = getattr(checker, 'model_name', 'allenai/specter2')
    print(f"Current model: {current_model}")
    
    print("\nAvailable models:")
    print("1. allenai/specter2 (default, scientific text optimized)")
    print("2. all-mpnet-base-v2 (balanced, general purpose)")
    print("3. all-MiniLM-L6-v2 (faster, less accurate)")
    print("4. Custom model name")
    
    choice = get_user_input("\nEnter choice (1-4): ")
    
    model_map = {
        '1': 'allenai/specter2',
        '2': 'all-mpnet-base-v2',
        '3': 'all-MiniLM-L6-v2'
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
        # Create a new checker instance with the new model
        new_checker = SemanticResearchChecker(new_model)
        
        # Transfer context if it exists
        if checker.context_text:
            new_checker.context_text = checker.context_text
            new_checker.context_embedding = new_checker._encode_text(checker.context_text)
            print("✅ Context transferred to new model")
        
        # Replace the old checker
        checker.__dict__.update(new_checker.__dict__)
        print("✅ Model changed successfully!")
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("Keeping current model.")
    
    input("Press Enter to continue...")


def reset_embeddings_and_recalculate(checker, storage):
    """Recalculate context embeddings and relevance scores for all papers"""
    clear_screen()
    print_header()
    print_statistics(storage)
    print("🔄 RECALCULATE EMBEDDINGS & RELEVANCE")
    print("-" * 60)
    
    if not storage.papers:
        print("📝 No papers stored to recalculate.")
        input("Press Enter to continue...")
        return
    
    if not checker.context_text:
        print("❌ No research context loaded.")
        print("   Please load a research context first using 'Manage research context'.")
        input("Press Enter to continue...")
        return
    
    print(f"📊 Current status:")
    print(f"   Total papers: {len(storage.papers)}")
    print(f"   Research context: {getattr(checker, '_context_file', 'research_context.txt')}")
    print(f"   Context length: {len(checker.context_text)} characters")
    print(f"   Current model: {getattr(checker, 'model_name', 'unknown')}")
    print()
    
    print("This will:")
    print("1. Recalculate context embeddings with current model")
    print("2. Recalculate relevance scores for ALL stored papers")
    print("3. Update paper categories and status based on new scores")
    print("4. Save all changes to storage")
    print()
    
    confirm = get_user_input("Are you sure you want to proceed? (Y/n): ")
    
    if confirm.lower() != 'y':
        print("❌ Recalculation cancelled.")
        input("Press Enter to continue...")
        return
    
    try:
        # Step 1: Recalculate context embeddings
        print("\n🔄 Step 1: Recalculating context embeddings...")
        print("Creating new context embedding with current model...")
        checker.context_embedding = checker._encode_text(checker.context_text)
        print("✅ Context embeddings recalculated successfully!")
        
        # Step 2: Recalculate all relevance scores
        print("\n🔄 Step 2: Recalculating paper relevance scores...")
        stats = storage.recalculate_all_relevance_scores(checker)
        
        # Step 3: Show summary
        print("\n" + "="*60)
        print("📊 RECALCULATION SUMMARY")
        print("="*60)
        print(f"Total papers processed: {stats['total_papers']}")
        print(f"Papers with significant changes: {stats['updated_papers']}")
        print(f"Papers with minimal changes: {stats['unchanged_papers']}")
        print(f"Papers with errors: {stats['error_papers']}")
        
        if stats['updated_papers'] > 0:
            print(f"\n✅ Successfully updated {stats['updated_papers']} papers!")
            print("   Paper relevance scores have been recalculated with fresh embeddings.")
        else:
            print(f"\n📝 No significant changes detected.")
            print("   All papers maintained similar relevance scores.")
        
        print("\n💡 Tip: Use 'View all papers' to see the updated rankings.")
        
    except Exception as e:
        print(f"\n❌ Error during recalculation: {e}")
        print("Please try again or contact support.")
        import traceback
        print(f"Debug info: {traceback.format_exc()}")
    
    input("\nPress Enter to continue...")


def show_top_papers_to_read(storage):
    """Show top papers to read next by relevance with pagination"""
    top_papers = storage.get_top_unread_papers(50)  # Get more papers for pagination
    
    if not top_papers:
        print("📝 No unread papers available.")
        input("Press Enter to continue...")
        return
    
    display_top_papers_with_pagination(top_papers, storage)


def display_top_papers_with_pagination(papers, storage, page_size=10):
    """Display top papers with pagination"""
    if not papers:
        print("📝 No unread papers available.")
        input("Press Enter to continue...")
        return
    
    total_papers = len(papers)
    total_pages = (total_papers + page_size - 1) // page_size
    current_page = 1
    
    while True:
        clear_screen()
        print_header()
        print_statistics(storage)
        print("🎯 TOP PAPERS TO READ NEXT")
        print("-" * 60)
        
        # Calculate start and end indices for current page
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_papers)
        current_papers = papers[start_idx:end_idx]
        
        print(f"Showing top {total_papers} unread papers by relevance")
        print(f"Page {current_page} of {total_pages} | Showing papers {start_idx + 1}-{end_idx}")
        print()
        
        # Display papers for current page
        for i, paper in enumerate(current_papers, start_idx + 1):
            pdf_icon = "📄" if paper.get('pdf_path') else "📝"
            print(f"{i}. {pdf_icon} {paper['title'][:55]}...")
            print(f"   Relevance: {paper['relevance_score']:.2f}% - {paper['category']}")
            print(f"   Added: {paper['added_date'][:10]}")
            if paper.get('arxiv_id'):
                print(f"   ArXiv: {paper['arxiv_id']}")
            if paper.get('notes'):
                print(f"   Note: {paper['notes'][:50]}...")
            print()
        
        # Show pagination controls
        print("-" * 60)
        print("📄 PAGINATION CONTROLS:")
        
        if total_pages > 1:
            if current_page > 1:
                print("◀️  Previous page (p)")
            if current_page < total_pages:
                print("▶️  Next page (n)")
            print(f"📄 Go to page (g1-{total_pages})")
        
        print("📋 ACTIONS:")
        print("1. Start reading a paper (change status to 'reading')")
        print("2. View paper details")
        print("3. Add/edit notes")
        print("4. Open PDF (if available)")
        print("5. Back to main menu")
        
        choice = get_user_input("\nEnter your choice: ").lower()
        
        if choice == 'p' and current_page > 1:
            current_page -= 1
        elif choice == 'n' and current_page < total_pages:
            current_page += 1
        elif choice.startswith('g') and choice[1:].isdigit():
            # Go to specific page
            page_num = int(choice[1:])
            if 1 <= page_num <= total_pages:
                current_page = page_num
            else:
                print("❌ Invalid page number.")
                input("Press Enter to continue...")
        elif choice.isdigit():
            # Handle actions
            choice_num = int(choice)
            if choice_num == 1:
                start_reading_paper_from_list(storage, papers)
            elif choice_num == 2:
                view_paper_details_from_list(storage, papers)
            elif choice_num == 3:
                edit_paper_notes_from_list(storage, papers)
            elif choice_num == 4:
                open_pdf_from_top_papers_list(storage, papers)
            elif choice_num == 5:
                return
            else:
                print("❌ Invalid choice.")
                input("Press Enter to continue...")
        else:
            print("❌ Invalid choice.")
            input("Press Enter to continue...")


def pick_random_paper_to_read(storage):
    """Pick a random unread paper"""
    clear_screen()
    print_header()
    print_statistics(storage)
    print("🎲 RANDOM PAPER PICKER")
    print("-" * 60)
    
    random_paper = storage.get_random_unread_paper()
    
    if not random_paper:
        print("📝 No unread papers available.")
        input("Press Enter to continue...")
        return
    
    print("🎯 Here's your randomly selected paper:")
    print()
    
    pdf_icon = "📄" if random_paper.get('pdf_path') else "📝"
    print(f"{pdf_icon} {random_paper['title']}")
    print(f"Relevance: {random_paper['relevance_score']:.2f}% - {random_paper['category']}")
    print(f"Added: {random_paper['added_date'][:10]}")
    if random_paper.get('arxiv_id'):
        print(f"ArXiv: {random_paper['arxiv_id']}")
    if random_paper.get('authors'):
        print(f"Authors: {random_paper['authors']}")
    if random_paper.get('notes'):
        print(f"Notes: {random_paper['notes']}")
    
    print(f"\nAbstract:")
    print("-" * 40)
    print(random_paper['abstract'])
    print("-" * 40)
    
    # Show action options
    print("\nWhat would you like to do?")
    print("1. Start reading this paper")
    print("2. Pick another random paper") 
    print("3. Add/edit notes for this paper")
    print("4. Discard this paper")
    print("5. Back to main menu")
    
    choice = get_user_input("\nEnter your choice (1-5): ")
    
    if choice == "1":
        storage.update_paper_status(random_paper['id'], "reading")
        print("✅ Paper status updated to 'reading'!")
        input("Press Enter to continue...")
    elif choice == "2":
        pick_random_paper_to_read(storage)  # Recursively pick another
        return
    elif choice == "3":
        edit_single_paper_notes(storage, random_paper)
    elif choice == "4":
        storage.update_paper_status(random_paper['id'], "discarded")
        print("✅ Paper discarded.")
        input("Press Enter to continue...")
    elif choice == "5":
        return
    else:
        print("❌ Invalid choice.")
        input("Press Enter to continue...")


def manage_reading_queue(storage):
    """Manage the reading queue - view currently reading papers with pagination"""
    reading_papers = storage.get_papers_by_status("reading")
    
    if not reading_papers:
        print("📝 No papers currently being read.")
        input("Press Enter to continue...")
        return
    
    # Sort by relevance score
    reading_papers = sorted(reading_papers, key=lambda x: x["relevance_score"], reverse=True)
    
    display_reading_queue_with_pagination(reading_papers, storage)


def display_reading_queue_with_pagination(papers, storage, page_size=10):
    """Display reading queue with pagination"""
    if not papers:
        print("📝 No papers currently being read.")
        input("Press Enter to continue...")
        return
    
    total_papers = len(papers)
    total_pages = (total_papers + page_size - 1) // page_size
    current_page = 1
    
    while True:
        clear_screen()
        print_header()
        print_statistics(storage)
        print("📖 READING QUEUE MANAGEMENT")
        print("-" * 60)
        
        # Calculate start and end indices for current page
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_papers)
        current_papers = papers[start_idx:end_idx]
        
        print(f"Currently reading {total_papers} papers")
        print(f"Page {current_page} of {total_pages} | Showing papers {start_idx + 1}-{end_idx}")
        print()
        
        # Display papers for current page
        for i, paper in enumerate(current_papers, start_idx + 1):
            pdf_icon = "📄" if paper.get('pdf_path') else "📝"
            print(f"{i}. {pdf_icon} {paper['title'][:55]}...")
            print(f"   Relevance: {paper['relevance_score']:.2f}% - {paper['category']}")
            print(f"   Added: {paper['added_date'][:10]}")
            if paper.get('notes'):
                print(f"   Note: {paper['notes'][:50]}...")
            print()
        
        # Show pagination controls
        print("-" * 60)
        print("📄 PAGINATION CONTROLS:")
        
        if total_pages > 1:
            if current_page > 1:
                print("◀️  Previous page (p)")
            if current_page < total_pages:
                print("▶️  Next page (n)")
            print(f"📄 Go to page (g1-{total_pages})")
        
        print("📋 ACTIONS:")
        print("1. Mark paper as completed (status: 'read')")
        print("2. Move paper back to 'to read' queue")
        print("3. View paper details")
        print("4. Add/edit notes")
        print("5. Open PDF (if available)")
        print("6. Back to main menu")
        
        choice = get_user_input("\nEnter your choice: ").lower()
        
        if choice == 'p' and current_page > 1:
            current_page -= 1
        elif choice == 'n' and current_page < total_pages:
            current_page += 1
        elif choice.startswith('g') and choice[1:].isdigit():
            # Go to specific page
            page_num = int(choice[1:])
            if 1 <= page_num <= total_pages:
                current_page = page_num
            else:
                print("❌ Invalid page number.")
                input("Press Enter to continue...")
        elif choice.isdigit():
            # Handle actions
            choice_num = int(choice)
            if choice_num == 1:
                mark_paper_as_read_from_list(storage, papers)
            elif choice_num == 2:
                move_paper_back_to_queue(storage, papers)
            elif choice_num == 3:
                view_paper_details_from_list(storage, papers)
            elif choice_num == 4:
                edit_paper_notes_from_list(storage, papers)
            elif choice_num == 5:
                open_pdf_from_reading_queue(storage, papers)
            elif choice_num == 6:
                return
            else:
                print("❌ Invalid choice.")
                input("Press Enter to continue...")
        else:
            print("❌ Invalid choice.")
            input("Press Enter to continue...")


def start_reading_paper_from_list(storage, papers):
    """Start reading a paper from a list"""
    if not papers:
        return
        
    paper_num = get_user_input(f"Enter paper number to start reading (1-{len(papers)}): ")
    
    try:
        paper_num = int(paper_num)
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            storage.update_paper_status(paper['id'], "reading")
            print(f"✅ Started reading: {paper['title'][:40]}...")
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("Press Enter to continue...")


def view_paper_details_from_list(storage, papers):
    """View paper details from a list"""
    if not papers:
        return
        
    paper_num = get_user_input(f"Enter paper number to view details (1-{len(papers)}): ")
    
    try:
        paper_num = int(paper_num)
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            _show_paper_details_with_notes(paper)
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("Press Enter to continue...")


def edit_paper_notes_from_list(storage, papers):
    """Edit paper notes from a list"""
    if not papers:
        return
        
    paper_num = get_user_input(f"Enter paper number to edit notes (1-{len(papers)}): ")
    
    try:
        paper_num = int(paper_num)
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            edit_single_paper_notes(storage, paper)
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")


def edit_single_paper_notes(storage, paper):
    """Edit notes for a single paper and update embeddings"""
    print(f"\nEditing notes for: {paper['title'][:50]}...")
    print(f"Current notes: {paper.get('notes', '(no notes)')}")
    print()
    print("Enter new notes (press Enter twice when done):")
    
    lines = []
    while True:
        line = input()
        if line == "" and lines:  # Empty line after content
            break
        lines.append(line)
    
    new_notes = "\n".join(lines)
    
    # Update notes in storage
    storage.update_paper_notes(paper['id'], new_notes)
    
    # Show additional options
    print("✅ Notes updated!")
    print()
    print("Additional options:")
    print("1. Update paper embedding with new notes")
    print("2. Add snippet from this paper to global research context")
    print("3. Continue without updating embedding")
    
    choice = get_user_input("Enter choice (1-3): ")
    
    if choice == "1":
        update_paper_embedding_with_notes(storage, paper['id'])
    elif choice == "2":
        add_snippet_to_context_from_paper(storage, paper, new_notes)
    
    input("Press Enter to continue...")


def update_paper_embedding_with_notes(storage, paper_id):
    """Update a paper's embedding to include its notes"""
    try:
        # We need access to the checker - let's get it from main
        # For now, we'll need to pass it as a parameter or access it differently
        print("🔄 Updating paper embedding with notes...")
        print("⚠️  Note: Embedding will be updated next time relevance is recalculated.")
        print("   Use 'Recalculate embeddings & relevance' from main menu for immediate update.")
    except Exception as e:
        print(f"❌ Error updating embedding: {e}")


def add_snippet_to_context_from_paper(storage, paper, notes=""):
    """Add a snippet from a paper to the global research context"""
    print(f"\nAdding snippet from: {paper['title'][:50]}...")
    print()
    
    # Default snippet options
    print("Choose snippet source:")
    print("1. From paper abstract")
    print("2. From your notes")
    print("3. Custom snippet")
    
    choice = get_user_input("Enter choice (1-3): ")
    
    snippet_content = ""
    if choice == "1":
        snippet_content = paper['abstract'][:500] + "..." if len(paper['abstract']) > 500 else paper['abstract']
    elif choice == "2":
        if notes:
            snippet_content = notes
        else:
            print("❌ No notes available for this paper.")
            return
    elif choice == "3":
        print("Enter custom snippet:")
        snippet_content = get_user_input("Snippet: ")
    else:
        print("❌ Invalid choice.")
        return
    
    if not snippet_content.strip():
        print("❌ Snippet cannot be empty.")
        return
    
    # Store snippet info for later processing
    snippet_data = {
        'content': snippet_content,
        'source': paper['title'],
        'paper_id': paper['id']
    }
    
    # Save snippet data to a temporary file for processing by main
    import json
    temp_file = "temp_snippet.json"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(snippet_data, f)
    
    print("✅ Snippet prepared! It will be added to context when you return to main menu.")


def manage_context_snippets(checker):
    """Manage research context snippets"""
    while True:
        clear_screen()
        print_header()
        print("🧩 MANAGE RESEARCH SNIPPETS")
        print("-" * 60)
        
        if not hasattr(checker, 'context_snippets'):
            print("❌ Context snippets not supported by current checker version.")
            input("Press Enter to continue...")
            return
        
        snippets = checker.get_context_snippets()
        
        if not snippets:
            print("📝 No research snippets added yet.")
        else:
            print(f"Research snippets ({len(snippets)}):")
            print()
            
            for i, snippet in enumerate(snippets, 1):
                print(f"{i}. {snippet['content'][:60]}...")
                if snippet.get('source'):
                    print(f"   Source: {snippet['source']}")
                print(f"   Added: {snippet['added_date'][:10]}")
                print()
        
        print("-" * 60)
        print("Options:")
        print("1. Add new snippet")
        print("2. View snippet details")
        print("3. Remove snippet")
        print("4. Back to context management")
        
        choice = get_user_input("\nEnter choice (1-4): ")
        
        if choice == "1":
            add_new_context_snippet(checker)
        elif choice == "2" and snippets:
            view_snippet_details(checker, snippets)
        elif choice == "3" and snippets:
            remove_context_snippet(checker, snippets)
        elif choice == "4":
            break
        else:
            if choice in ["2", "3"] and not snippets:
                print("❌ No snippets available.")
            else:
                print("❌ Invalid choice.")
            input("Press Enter to continue...")


def add_new_context_snippet(checker):
    """Add a new snippet to research context"""
    print("\n➕ ADD NEW RESEARCH SNIPPET")
    print("-" * 40)
    
    content = get_user_input("Enter snippet content: ")
    source = get_user_input("Enter source (optional): ", required=False)
    
    if content.strip():
        snippet_id = checker.add_context_snippet(content, source)
        print(f"✅ Added snippet (ID: {snippet_id})")
    else:
        print("❌ Snippet content cannot be empty.")
    
    input("Press Enter to continue...")


def view_snippet_details(checker, snippets):
    """View detailed information about a snippet"""
    snippet_num = get_user_input(f"Enter snippet number to view (1-{len(snippets)}): ")
    
    try:
        snippet_num = int(snippet_num)
        if 1 <= snippet_num <= len(snippets):
            snippet = snippets[snippet_num - 1]
            
            print("\n📄 SNIPPET DETAILS")
            print("-" * 40)
            print(f"ID: {snippet['id']}")
            print(f"Added: {snippet['added_date']}")
            if snippet.get('source'):
                print(f"Source: {snippet['source']}")
            if snippet.get('paper_id'):
                print(f"Paper ID: {snippet['paper_id']}")
            print("\nContent:")
            print("-" * 20)
            print(snippet['content'])
            print("-" * 20)
        else:
            print("❌ Invalid snippet number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("Press Enter to continue...")


def remove_context_snippet(checker, snippets):
    """Remove a snippet from research context"""
    snippet_num = get_user_input(f"Enter snippet number to remove (1-{len(snippets)}): ")
    
    try:
        snippet_num = int(snippet_num)
        if 1 <= snippet_num <= len(snippets):
            snippet = snippets[snippet_num - 1]
            
            confirm = get_user_input(f"Remove snippet '{snippet['content'][:30]}...'? (Y/n): ")
            
            if confirm.lower() == 'y':
                if checker.remove_context_snippet(snippet['id']):
                    print("✅ Snippet removed and context embedding updated.")
                else:
                    print("❌ Failed to remove snippet.")
            else:
                print("📝 Removal cancelled.")
        else:
            print("❌ Invalid snippet number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("Press Enter to continue...")


def mark_paper_as_read_from_list(storage, papers):
    """Mark a paper as read from a list"""
    if not papers:
        return
        
    paper_num = get_user_input(f"Enter paper number to mark as read (1-{len(papers)}): ")
    
    try:
        paper_num = int(paper_num)
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            storage.update_paper_status(paper['id'], "read")
            print(f"✅ Marked as read: {paper['title'][:40]}...")
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("Press Enter to continue...")


def move_paper_back_to_queue(storage, papers):
    """Move a paper back to 'to read' status"""
    if not papers:
        return
        
    paper_num = get_user_input(f"Enter paper number to move back to queue (1-{len(papers)}): ")
    
    try:
        paper_num = int(paper_num)
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            storage.update_paper_status(paper['id'], "to read")
            print(f"✅ Moved back to queue: {paper['title'][:40]}...")
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("Press Enter to continue...")


def open_pdf_from_reading_queue(storage, papers):
    """Open PDF from reading queue"""
    if not papers:
        return
        
    paper_num = get_user_input(f"Enter paper number to open PDF (1-{len(papers)}): ")
    
    try:
        paper_num = int(paper_num)
        if 1 <= paper_num <= len(papers):
            paper = papers[paper_num - 1]
            
            if paper.get('pdf_path'):
                open_pdf_file(paper['pdf_path'])
            else:
                print("❌ No PDF available for this paper.")
        else:
            print("❌ Invalid paper number.")
    except ValueError:
        print("❌ Please enter a valid number.")
    
    input("Press Enter to continue...")


def _show_paper_details_with_notes(paper):
    """Helper function to display detailed paper information including notes"""
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
    
    # Show embedding status
    if paper.get('embedding_needs_update'):
        print("🔄 Embedding update needed (notes added/modified)")
    elif paper.get('embedding_updated_date'):
        print(f"✅ Embedding updated: {paper['embedding_updated_date'][:10]}")
    
    # Show notes if any
    if paper.get('notes'):
        print(f"\nNotes:")
        print("-" * 20)
        print(paper['notes'])
        print("-" * 20)
    
    print("\nAbstract:")
    print("-" * 40)
    print(paper['abstract'])
    print("-" * 40)
    
    # Add PDF opening option if PDF exists
    if paper.get('pdf_path'):
        print("\n" + "-" * 60)
        print("📄 PDF ACTIONS:")
        print("-" * 60)
        print("1. Open PDF")
        print("2. Back to previous menu")
        
        choice = get_user_input("\nEnter your choice (1-2): ")
        
        if choice == "1":
            open_pdf_file(paper['pdf_path'])
            input("Press Enter to continue...")


def check_and_process_temp_snippets(checker):
    """Check for temporary snippets and add them to context"""
    import json
    import os
    
    temp_file = "temp_snippet.json"
    if os.path.exists(temp_file):
        try:
            with open(temp_file, 'r', encoding='utf-8') as f:
                snippet_data = json.load(f)
            
            # Add snippet to context
            snippet_id = checker.add_context_snippet(
                snippet_data['content'],
                snippet_data['source'],
                snippet_data.get('paper_id')
            )
            
            print(f"✅ Added research snippet from {snippet_data['source']} (ID: {snippet_id})")
            
            # Clean up temp file
            os.remove(temp_file)
            
        except Exception as e:
            print(f"❌ Error processing snippet: {e}")
            # Clean up temp file on error
            try:
                os.remove(temp_file)
            except:
                pass


def mass_add_papers(checker, storage):
    """Mass add papers from a list of ArXiv IDs"""
    clear_screen()
    print_header()
    print_statistics(storage)
    print("📚 MASS ADD PAPERS FROM ARXIV IDs")
    print("-" * 60)
    print("Enter ArXiv IDs separated by new lines (one per line).")
    print("Example:")
    print("2206.10498")
    print("2406.13094")
    print("2505.20246")
    print()
    print("Enter an empty line when done:")
    print("-" * 60)
    
    # Collect ArXiv IDs
    arxiv_ids = []
    while True:
        line = input().strip()
        if line == "":
            break
        # Clean the ID (remove any arxiv: prefix and whitespace)
        clean_id = line.replace('arxiv:', '').strip()
        if clean_id:
            arxiv_ids.append(clean_id)
    
    if not arxiv_ids:
        print("❌ No ArXiv IDs provided.")
        input("Press Enter to continue...")
        return
    
    print(f"\n📝 Found {len(arxiv_ids)} ArXiv IDs to process:")
    for i, arxiv_id in enumerate(arxiv_ids, 1):
        print(f"  {i}. {arxiv_id}")
    
    # Confirm processing
    confirm = get_user_input(f"\nProcess these {len(arxiv_ids)} papers? (Y/n): ")
    if confirm.lower() != 'y':
        return
    
    # Process each paper
    arxiv = ArXivIntegration()
    results = {
        'added': 0,
        'skipped_existing': 0,
        'failed': 0,
        'errors': []
    }
    
    print(f"\n🔄 Processing {len(arxiv_ids)} papers...")
    print("=" * 60)
    
    for i, arxiv_id in enumerate(arxiv_ids, 1):
        print(f"\n[{i}/{len(arxiv_ids)}] Processing {arxiv_id}...")
        
        try:
            # Check if paper already exists
            if storage.paper_exists_by_arxiv_id(arxiv_id):
                existing_paper = storage.get_paper_by_arxiv_id(arxiv_id)
                print(f"  ⚠️  Already exists: {existing_paper['title'][:50]}...")
                results['skipped_existing'] += 1
                continue
            
            # Fetch paper from ArXiv
            print(f"  🔄 Fetching from ArXiv...")
            paper = arxiv.get_paper_by_id(arxiv_id)
            
            if not paper:
                print(f"  ❌ Paper not found on ArXiv")
                results['failed'] += 1
                results['errors'].append(f"{arxiv_id}: Not found on ArXiv")
                continue
            
            # Check relevance
            print(f"  🧠 Analyzing relevance...")
            result = checker.check_paper_relevance(paper['title'], paper['abstract'])
            
            # Store paper
            print(f"  💾 Storing paper...")
            enhanced_data = {
                'title': paper['title'],
                'abstract': paper['abstract'],
                'relevance_score': result['relevance_score'],
                'category': result['category'],
                'arxiv_id': paper.get('arxiv_id'),
                'authors': paper.get('authors', 'Unknown'),
                'published': paper.get('published', 'Unknown')
            }
            
            # Add to storage
            paper_id = storage.add_paper(
                title=enhanced_data['title'],
                abstract=enhanced_data['abstract'],
                relevance_score=enhanced_data['relevance_score'],
                category=enhanced_data['category']
            )
            
            # Update with additional metadata
            stored_paper = storage.get_paper_by_id(paper_id)
            if stored_paper:
                stored_paper['arxiv_id'] = enhanced_data['arxiv_id']
                stored_paper['authors'] = enhanced_data['authors']
                stored_paper['published'] = enhanced_data['published']
                storage._save_papers()
            
            # Download PDF
            print(f"  📄 Downloading PDF...")
            try:
                folder_path = get_folder_for_relevance(enhanced_data['relevance_score'])
                pdf_path = arxiv.download_pdf(enhanced_data['arxiv_id'], enhanced_data['title'], folder_path)
                
                if pdf_path and stored_paper:
                    stored_paper['pdf_path'] = pdf_path
                    storage._save_papers()
                    print(f"  ✅ PDF saved")
                else:
                    print(f"  ⚠️  PDF download failed")
                    
            except Exception as e:
                print(f"  ⚠️  PDF download failed: {e}")
            
            print(f"  ✅ Added: {paper['title'][:50]}... (Relevance: {result['relevance_score']:.1f}%)")
            results['added'] += 1
            
        except Exception as e:
            print(f"  ❌ Error processing {arxiv_id}: {e}")
            results['failed'] += 1
            results['errors'].append(f"{arxiv_id}: {str(e)}")
    
    # Show final results
    print("\n" + "=" * 60)
    print("📊 MASS ADD RESULTS:")
    print("=" * 60)
    print(f"✅ Successfully added: {results['added']} papers")
    print(f"⚠️  Skipped (already exist): {results['skipped_existing']} papers")
    print(f"❌ Failed: {results['failed']} papers")
    
    if results['errors']:
        print(f"\n❌ Errors encountered:")
        for error in results['errors']:
            print(f"   • {error}")
    
    if results['added'] > 0:
        print(f"\n✅ {results['added']} new papers added to your library!")
        print("   All papers are set to 'to read' status.")
        print("   Use option 6 to see your top papers to read next.")
    
    input("\nPress Enter to continue...")


def enhanced_embedding_update_menu(checker, storage):
    """Enhanced embedding update with notes integration"""
    clear_screen()
    print_header()
    print_statistics(storage)
    print("🔄 ENHANCED EMBEDDING & RELEVANCE UPDATE")
    print("-" * 60)
    
    # Get papers that need embedding updates
    papers_needing_update = storage.get_papers_needing_embedding_update()
    total_papers = len(storage.papers)
    
    print(f"📊 Current Status:")
    print(f"Total papers: {total_papers}")
    print(f"Papers with notes needing embedding update: {len(papers_needing_update)}")
    print(f"Research context snippets: {len(checker.context_snippets) if hasattr(checker, 'context_snippets') else 0}")
    
    if not checker.context_text:
        print("❌ No research context loaded.")
        print("   Please load a research context first using 'Manage research context'.")
        input("Press Enter to continue...")
        return
    
    print(f"Context file: {getattr(checker, '_context_file', 'research_context.txt')}")
    print(f"Current model: {getattr(checker, 'model_name', 'unknown')}")
    print()
    
    print("This will:")
    print("1. Recalculate context embeddings (including any new snippets)")
    print("2. Update embeddings for papers with notes")
    print("3. Recalculate relevance scores for ALL papers with enhanced context")
    print("4. Save all changes to storage")
    print()
    
    confirm = get_user_input("Are you sure you want to proceed? (Y/n): ")
    
    if confirm.lower() != 'y':
        print("❌ Update cancelled.")
        input("Press Enter to continue...")
        return
    
    try:
        # Step 1: Recalculate context embeddings
        print("\n🔄 Step 1: Recalculating enhanced context embeddings...")
        if hasattr(checker, '_extract_base_context'):
            base_context = checker._extract_base_context()
            checker.context_text = checker._build_enhanced_context(base_context)
        checker.context_embedding = checker._encode_text(checker.context_text)
        print("✅ Enhanced context embeddings recalculated!")
        
        # Step 2: Update paper embeddings with notes
        print("\n🔄 Step 2: Updating paper embeddings with notes...")
        embedding_stats = storage.batch_update_embeddings_with_notes(checker)
        print(f"✅ Updated embeddings for {embedding_stats['updated_count']} papers")
        if embedding_stats['error_count'] > 0:
            print(f"⚠️  {embedding_stats['error_count']} papers had errors")
        
        # Step 3: Recalculate all relevance scores
        print("\n🔄 Step 3: Recalculating relevance scores with enhanced context...")
        relevance_stats = storage.recalculate_all_relevance_scores(checker)
        
        # Step 4: Show summary
        print("\n" + "="*60)
        print("📊 ENHANCED UPDATE SUMMARY")
        print("="*60)
        print(f"Total papers processed: {relevance_stats['total_papers']}")
        print(f"Papers with embedding updates: {embedding_stats['updated_count']}")
        print(f"Papers with relevance changes: {relevance_stats['updated_papers']}")
        print(f"Papers with minimal changes: {relevance_stats['unchanged_papers']}")
        print(f"Errors: {relevance_stats['error_papers'] + embedding_stats['error_count']}")
        
        if embedding_stats['updated_count'] > 0:
            print(f"\n✅ Successfully integrated notes into {embedding_stats['updated_count']} paper embeddings!")
        
        if relevance_stats['updated_papers'] > 0:
            print(f"✅ Updated relevance scores for {relevance_stats['updated_papers']} papers!")
        
        print("\n💡 Tip: Papers with notes now have enhanced semantic relevance scoring!")
        
    except Exception as e:
        print(f"\n❌ Error during enhanced update: {e}")
        print("Please try again or contact support.")
        import traceback
        print(f"Debug info: {traceback.format_exc()}")
    
    input("\nPress Enter to continue...")


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
            print_statistics(storage)
            
            # Check for temporary snippets and process them
            check_and_process_temp_snippets(checker)
            
            print_menu()
            
            choice = get_user_input("Enter your choice (1-15): ")
            
            if choice == '1':
                search_arxiv_papers(checker, storage)
            elif choice == '2':
                add_manual_paper(checker, storage)
            elif choice == '3':
                view_all_papers(storage)
            elif choice == '4':
                view_papers_by_status(storage)
            elif choice == '5':
                search_papers(storage)
            elif choice == '6':
                show_top_papers_to_read(storage)
            elif choice == '7':
                pick_random_paper_to_read(storage)
            elif choice == '8':
                manage_reading_queue(storage)
            elif choice == '9':
                open_papers_folder()
            elif choice == '10':
                manage_research_context(checker)
            elif choice == '11':
                change_model(checker)
            elif choice == '12':
                export_papers(storage)
            elif choice == '13':
                enhanced_embedding_update_menu(checker, storage)
            elif choice == '14':
                mass_add_papers(checker, storage)
            elif choice == '15':
                print("\n👋 Bye! ~ Semantic Research Manager")
                break
            else:
                print("❌ Invalid choice. Please enter 1-15.")
                input("Press Enter to continue...")
                
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main() 