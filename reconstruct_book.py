#!/usr/bin/env python3
"""
Book Reconstruction Tool for LibraryOfBabel
Reassemble a book from its chunks back to original form
"""
import psycopg2
import os
import sys
import re

def reconstruct_book(book_title):
    """Reconstruct a book from database chunks"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='knowledge_base', 
            user=os.getenv('USER'),
            port=5432
        )
        cur = conn.cursor()
        
        # Find the book
        cur.execute("SELECT book_id, title, author FROM books WHERE title ILIKE %s", (f"%{book_title}%",))
        book_results = cur.fetchall()
        
        if not book_results:
            print(f"❌ Book not found: '{book_title}'")
            return
            
        if len(book_results) > 1:
            print("📚 Multiple books found:")
            for i, (book_id, title, author) in enumerate(book_results, 1):
                print(f"  {i}. {title} by {author}")
            choice = input("Enter choice (1-{}): ".format(len(book_results)))
            try:
                book_id, title, author = book_results[int(choice) - 1]
            except (ValueError, IndexError):
                print("❌ Invalid choice")
                return
        else:
            book_id, title, author = book_results[0]
        
        print(f"📖 Reconstructing: {title} by {author}")
        
        # Get all chunks for this book, ordered properly
        cur.execute("""
        SELECT 
            chunk_id,
            chunk_type,
            chapter_number,
            section_number,
            content,
            word_count
        FROM chunks 
        WHERE book_id = %s
        ORDER BY 
            COALESCE(chapter_number, 0),
            COALESCE(section_number, 0),
            chunk_id
        """, (book_id,))
        
        chunks = cur.fetchall()
        
        if not chunks:
            print("❌ No chunks found for this book")
            return
            
        print(f"📝 Found {len(chunks)} chunks")
        
        # Reconstruct the book
        reconstructed_text = []
        current_chapter = None
        total_words = 0
        
        for chunk_id, chunk_type, chapter_num, section_num, content, word_count in chunks:
            # Add chapter breaks
            if chapter_num and chapter_num != current_chapter:
                if current_chapter is not None:
                    reconstructed_text.append("\n" + "="*60 + "\n")
                reconstructed_text.append(f"CHAPTER {chapter_num}\n")
                reconstructed_text.append("-" * 20 + "\n\n")
                current_chapter = chapter_num
            
            # Clean up content
            clean_content = content.strip()
            if clean_content:
                reconstructed_text.append(clean_content)
                reconstructed_text.append("\n\n")
                total_words += word_count or 0
        
        # Write to file
        filename = f"{title.replace('/', '_').replace(':', '_')}_reconstructed.txt"
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)  # Remove invalid filename chars
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"RECONSTRUCTED BOOK\n")
            f.write(f"Title: {title}\n")
            f.write(f"Author: {author}\n")
            f.write(f"Total Words: {total_words:,}\n")
            f.write(f"Source: LibraryOfBabel Database\n")
            f.write("="*80 + "\n\n")
            f.write(''.join(reconstructed_text))
        
        print(f"✅ Book reconstructed successfully!")
        print(f"📄 Output file: {filename}")
        print(f"📊 Total words: {total_words:,}")
        print(f"📚 Chunks assembled: {len(chunks)}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def list_available_books():
    """List books available for reconstruction"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='knowledge_base', 
            user=os.getenv('USER'),
            port=5432
        )
        cur = conn.cursor()
        
        cur.execute("""
        SELECT b.title, b.author, COUNT(c.chunk_id) as chunk_count, SUM(c.word_count) as total_words
        FROM books b
        LEFT JOIN chunks c ON b.book_id = c.book_id
        GROUP BY b.book_id, b.title, b.author
        ORDER BY b.title
        """)
        
        books = cur.fetchall()
        print(f"📚 Available Books for Reconstruction ({len(books)} total):")
        print("="*80)
        
        for title, author, chunks, words in books:
            print(f"📖 {title}")
            print(f"   👤 Author: {author}")
            print(f"   📝 Chunks: {chunks}, Words: {words:,}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    if len(sys.argv) < 2:
        print("📖 LibraryOfBabel Book Reconstruction Tool")
        print("\nUsage:")
        print("  python3 reconstruct_book.py 'book title'     # Reconstruct specific book")
        print("  python3 reconstruct_book.py --list           # List all available books")
        print("\nExamples:")
        print("  python3 reconstruct_book.py 'Psalm'")
        print("  python3 reconstruct_book.py 'Discipline and Punish'")
        print("  python3 reconstruct_book.py 'Foucault'")
        return
        
    if sys.argv[1] == '--list':
        list_available_books()
    else:
        book_title = sys.argv[1]
        reconstruct_book(book_title)

if __name__ == "__main__":
    main()