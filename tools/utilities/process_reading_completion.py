#!/usr/bin/env python3
"""
📚 Reading Completion Processor
Updates LibraryOfBabel database with completed books and creates priority download queue
"""

import sqlite3
import re
from datetime import datetime
from typing import List, Tuple, Dict

# Reading completion data
READING_DATA = """
2/26/2019    3/5/2019    Circe
3/5/2019    3/8/2019    Digital Minimalism
2/19/2019    3/10/2019    Becoming
2/14/2019    3/14/2019    The Alchemy of Stone
3/7/2019    3/15/2019    Technopoly: The Surrender of Culture to Technology
3/6/2019    3/15/2019    Deep Work: Rules for Focused Success in a Distracted World
3/17/2019    3/18/2019    Atomic Habits
3/18/2019    3/19/2019    Trust Me I'm Lying
3/18/2019    3/19/2019    Hello World
3/19/2019    3/20/2019    Algorithms of Oppression: How Search Engines Reinforce Racism
3/21/2019    3/22/2019    AIQ: How People and Machines Are Smarter Together
3/19/2019    3/22/2019    New Dark Age: Technology and the End of the Future
3/22/2019    3/22/2019    Ego is the Enemy
3/27/2019    3/27/2019    The Hate U Give
3/19/2019    3/27/2019    The Icarus Deception: How High Will You Fly?
2/25/2019    4/1/2019    The Final Empire
4/3/2019    4/3/2019    We Should All Be Feminists
4/2/2019    4/4/2019    The Well of Ascension
4/4/2019    4/5/2019    The New Jim Crow
4/5/2019    4/6/2019    The Gifts of Imperfection: Let Go of Who You Think You're Supposed to Be and Embrace Who You Are
4/5/2019    4/7/2019    Suicidal: Why We Kill Ourselves
4/7/2019    4/8/2019    The Emotionally Absent Mother: A Guide to Self-Healing and Getting the Love You Missed
4/8/2019    4/11/2019    The Body Keeps the Score: Brain, Mind, and Body in the Healing of Trauma
4/11/19    4/12/19    Minecraft: The Island
03/09/19    4/12/19    Everyware, The Dawning age of ubiquitous computing
4/12/19    4/13/19    Dear America: Notes of an Undocumented Citizen
4/14/19    4/16/19    Coders: The Making of a New Tribe and the Remaking of the World
4/16/19    4/17/19    Tim Cook: The Genius Who Took Apple to the Next Level
4/17/19    4/17/19    Educated
04/09/19    4/18/19    No Time To Spare, Thinking About What Matters
4/20/19    4/23/19    Hero of Ages
4/23/19    4/24/19    The Alloy of Law
4/24/19    4/27/19    Abhorsen
4/27/19    4/29/19    Shadow of Self
4/29/19    4/30/19    The Bands of Mourning
5/1/19    5/1/19    Heavy, An American Memoir
5/1/19    5/2/19    Not That Bad, Dispatches from Rape Culture
4/17/19    5/12/19    Walking Through Walls, A Memoir
5/14/19    5/15/19    Invisible Women: Data Bias in a World Designed for Men
4/29/19    5/16/19    These Truths: The History of the United States
5/16/19    5/17/19    When Death Becomes Life: Notes from a Transplant Surgeon
5/18/19    5/19/19    Middlegame
5/19/19    5/20/19    Good Omens: The Nice and Accurate Prophecies of Agnes Nutter, Witch
5/20/19    5/23/19    The Fifth Season
5/23/19    5/23/19    When Breath Becomes Life
5/23/19    5/24/19    The Obelisk Gate
5/26/19    5/28/19    The Poppy War
5/25/19    5/29/19    The Stone Sky
5/29/19    5/29/19    The Traveling Cat Chronicle
5/28/19    5/31/19    Bookworm: A Memoir Of Childhood Reading
6/1/19    6/1/19    Daughters of the Dragon: A Comfort Woman's Story
5/29/19    6/1/19    The Sixth Extinction
6/1/19    6/2/19    The Calculating Stars
6/8/19    6/10/19    The Golem and theJinni
6/10/19    6/11/19    The Rape of Nanking
6/11/19    6/13/19    Waking The Witch: Reflections on Woman, Magic, and Power
6/15/19    6/16/19    Strange Day in Tokyo
6/14/19    6/16/19    Midnight in Chernobyl: The Untold of the World's Greatest Nuclear Disaster
6/13/19    6/16/19    Do No Harm: Stories of Life, Death and Brain Surgery
6/17/19    6/18/19    Amity and Prosperity: A Story of Energy in Two American Towns
6/20/19    6/21/19    Magic for Liars
6/24/19    6/24/19    Black Death at the Golden Gate: The Race to Save America from the Bubonic Plague
6/24/19    6/25/19    The Watchmaker of Filigree Street
6/18/19    6/26/19    The Emperor of All Maladies: A Biography of Cancer
6/25/19    6/27/19    A Darker Shade of Magic
6/27/19    6/28/19    A Natural History of Dragons
6/29/19    7/2/19    And the Band Played On: Politics, People, and the AIDS Epidemic
7/3/19    7/4/19    The Hot Zone: The Terrifying True Story of the Origins of the Ebola Virus
7/4/19    7/9/19    How to Survive a Plague: The Inside Story of How Citizens and Science Tamed AIDS
7/9/19    7/10/19    Range: Why Generalists Triumph in a Specialized World
7/10/19    7/11/19    The Second Shift: Working Families and the Revolution at Home
7/11/19    7/12/19    The Trauma Cleaner: One Woman's Extraordinary Life in the Business of Death, Decay, and Disaster
7/13/19    7/13/19    Where Reasons End
7/13/19    7/15/19    Washington Black
7/15/19    7/15/19    Look Alive Out There
7/15/19    7/16/19    Furiously Happy: A Funny Book About Horrible Things
7/16/19    7/17/19    The Robots are Coming!
7/22/19    7/27/19    No Longer Human
8/4/19    8/5/19    Selfie, How the West Become self-obssessed
8/4/19    8/5/19    The Soul of an Octopus: A Surprising Exploration into the Wonder of Consciousness
8/5/19    8/6/19    Because Internet: Understanding the New Rules of Language
8/6/19    8/7/19    Other Minds: The Octopus, the Sea, and the Deep Origins of Consciousness
8/9/19    8/10/19    This Common Secret: My Journey as an Abortion Doctor
8/17/19    8/19/19    Pachinko
8/10/19    9/17/19    Spinning Silver
9/30/19    10/1/19    Being Mortal: Medicine and What Matters in the End
10/2/19    10/3/19    Braving the Wilderness: The Quest for True Belonging and the Courage to Stand Alone
10/3/19    10/7/19    Less
10/7/19    10/9/19    The Kiss Quotient
10/10/19    10/11/19    The Girl in Red
10/14/19    10/17/19    Children of Time
10/21/19    10/21/19    Post-Truth
10/22/19    10/23/19    The Library of the Unwritten
10/24/19    10/24/19    The Black Tides of Heaven
10/25/19    10/26/19    Wilder Girls
10/31/19    11/1/19    The Fate of Food: What We'll Eat in a Bigger, Hotter, Smarter World
11/1/19    11/6/19    Everything Below the Waist: Why Health Care Needs a Feminist Revolution
11/14/19    11/19/19    Norse Mythology
11/19/19    11/22/19    The Viking Spirit: An Introduction to Norse Mythology and Religion
11/25/19    11/26/19    The Memory Police
11/22/19    11/30/19    The Body: A Guide for Occupants
12/1/19    12/2/19    Will My Cat Eat My Eyeballs?: Big Questions from Tiny Mortals About Death
12/2/19    12/3/19    The Queer Art of Failure
12/3/19    12/4/19    Carter & Lovecraft
12/4/19    12/5/19    Scythe (Arc of a Scythe #1)
12/5/19    12/5/19    Thunderhead (Arc of a Scythe #2)
12/6/19    12/8/19    The Toll (Arc of a Scythe #3)
12/9/19    12/9/19    Unit 731: The Forgotten Asian Auschwitz
12/9/19    12/9/19    This Land Is Our Land: An Immigrant's Manifesto
12/10/19    12/11/19    Here and Now and Then
12/12/19    12/13/19    Daisy Jones & The Six
12/15/19    12/18/19    Lagoon
12/18/19    12/19/19    Einstein's Dream
12/18/19    12/20/19    The Girl with Ghost Eyes (The Daoshi Chronicles #1)
12/22/19    12/28/19    Wild Swans: Three Daughters of China
12/28/19    12/28/19    Death Wins a Goldfish: Reflections from a Grim Reaper's Yearlong Sabbatical
12/28/19    12/28/19    The Prophet
12/12/19    12/31/19    The Elements of Eloquence: How to Turn the Perfect English Phrase
12/30/19    12/30/19    All Systems Red (Murderbot Diaries, #1)
12/30/19    12/31/19    Shout
12/31/19    1/1/20    Dying of Whiteness: How the Politics of Racial Resentment Is Killing America's Heartland
1/2/20    1/3/20    How to Be an Antiracist
1/3/20    1/6/20    The Shadow of the Wind
1/6/20    1/8/20    AI Superpowers China
1/8/20    1/9/20    Such a Fun Age
1/5/20    1/10/20    Dracula
1/13/20    1/13/20    I'd Rather Be Reading: The Delights and Dilemmas of the Reading Life
1/10/20    1/16/20    The God Game
1/18/20    1/19/20    Cold Storage
1/17/20    1/20/20    Kingdom of Souls
1/16/20    1/20/20    The Book of Yokai: Mysterious Creatures of Japanese Folklore
1/20/20    1/22/20    Uncanny Valley: A Memoir
1/22/20    1/24/20    The Gift of Dyslexia: Why Some of the Smartest People Can't Read...and How They Can Learn
1/23/20    1/24/20    Riot Baby
1/24/20    1/27/20    Akata Witch (Akata Witch #1)
1/29/20    1/29/20    The Black God's Drums
2/1/20    2/4/20    The Second Machine Age: Work, Progress, and Prosperity in a Time of Brilliant Technologies
1/30/20    2/5/20    One Child: The Story of China's Most Radical Experiment
2/5/20    2/6/20    No Surrender: My Thirty-Year War
2/7/20    2/7/20    Barracoon: The Story of the Last "Black Cargo"
2/7/20    2/10/20    Last Stop Auschwitz: My Story of Survival from within the Camp
2/10/20    2/12/20    Frankenstein in Baghdad
2/13/20    2/15/20    A Horse Walks into a Bar
2/17/20    2/18/20    McMindfulness: How Mindfulness Became the New Capitalist Spirituality
2/18/20    2/18/20    The Year We Fell From Space
2/19/19    2/19/19    Human Targets: Schools, Police, and the Criminalization of Latino Youth
2/15/20    2/20/20    Defying Hitler
2/20/20    2/20/20    The Metamorphosis
2/21/20    2/23/20    The Rithmatist
2/23/20    2/27/20    The Way of Kings (The Stormlight Archive)
"""

class ReadingCompletionProcessor:
    def __init__(self):
        self.db_path = "database/data/audiobook_ebook_tracker.db"
        self.completed_books = []
        
    def parse_reading_data(self) -> List[Tuple[str, str, str]]:
        """Parse the reading completion data"""
        books = []
        for line in READING_DATA.strip().split('\n'):
            if not line.strip():
                continue
                
            # Split by tab or multiple spaces
            parts = re.split(r'\s{2,}|\t', line.strip())
            if len(parts) >= 3:
                start_date = parts[0].strip()
                end_date = parts[1].strip()
                title = parts[2].strip()
                
                # Clean title
                title = title.replace('"', '').strip()
                if title:
                    books.append((start_date, end_date, title))
                    
        return books
    
    def clean_title_for_matching(self, title: str) -> str:
        """Clean title for database matching"""
        title = re.sub(r'\(.*?\)', '', title)  # Remove parentheses
        title = re.sub(r'\[.*?\]', '', title)  # Remove brackets
        title = re.sub(r':\s*.*$', '', title)  # Remove subtitles after colon
        title = re.sub(r'\s+', ' ', title).strip()
        return title.lower()
    
    def add_completion_tracking_schema(self):
        """Add completion tracking fields to audiobooks table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Add completion tracking columns
            try:
                cursor.execute("""
                    ALTER TABLE audiobooks ADD COLUMN is_completed INTEGER DEFAULT 0
                """)
                print("✅ Added is_completed column")
            except sqlite3.OperationalError:
                print("⚠️ is_completed column already exists")
                
            try:
                cursor.execute("""
                    ALTER TABLE audiobooks ADD COLUMN date_completed TEXT
                """)
                print("✅ Added date_completed column")
            except sqlite3.OperationalError:
                print("⚠️ date_completed column already exists")
                
            try:
                cursor.execute("""
                    ALTER TABLE audiobooks ADD COLUMN reading_priority INTEGER DEFAULT 0
                """)
                print("✅ Added reading_priority column")
            except sqlite3.OperationalError:
                print("⚠️ reading_priority column already exists")
                
            conn.commit()
    
    def update_completed_books(self):
        """Update database with completed books"""
        completed_books = self.parse_reading_data()
        print(f"📚 Processing {len(completed_books)} completed books...")
        
        matched_count = 0
        priority_queue = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all audiobooks for matching
            cursor.execute("SELECT album_id, title, clean_title, author FROM audiobooks")
            audiobooks = cursor.fetchall()
            
            for start_date, end_date, completed_title in completed_books:
                clean_completed = self.clean_title_for_matching(completed_title)
                
                # Try to match with audiobook collection
                best_match = None
                best_score = 0
                
                for album_id, title, clean_title, author in audiobooks:
                    # Try exact match first
                    if clean_completed == clean_title.lower():
                        best_match = (album_id, title, author)
                        best_score = 1.0
                        break
                    
                    # Try partial match
                    if clean_completed and clean_title and (clean_completed in clean_title.lower() or clean_title.lower() in clean_completed):
                        min_len = min(len(clean_completed), len(clean_title.lower()))
                        max_len = max(len(clean_completed), len(clean_title.lower()))
                        if min_len > 0:  # Avoid division by zero
                            score = min_len / max_len  # Similarity score
                            if score > best_score:
                                best_match = (album_id, title, author)
                                best_score = score
                
                if best_match and best_score > 0.7:
                    album_id, matched_title, matched_author = best_match
                    
                    # Update completion status
                    cursor.execute("""
                        UPDATE audiobooks 
                        SET is_completed = 1, 
                            date_completed = ?, 
                            reading_priority = 1
                        WHERE album_id = ?
                    """, (end_date, album_id))
                    
                    matched_count += 1
                    priority_queue.append({
                        'title': matched_title,
                        'author': matched_author,
                        'completed_date': end_date,
                        'original_title': completed_title
                    })
                    
                    print(f"✅ Matched: '{completed_title}' → '{matched_title}' by {matched_author}")
                else:
                    print(f"❌ No match: '{completed_title}'")
            
            conn.commit()
        
        print(f"\n🎯 Successfully matched {matched_count} completed books!")
        return priority_queue
    
    def create_download_queue(self, priority_queue: List[Dict]) -> str:
        """Create download queue for completed books"""
        queue_file = "completed_books_download_queue.json"
        
        import json
        with open(queue_file, 'w') as f:
            json.dump(priority_queue, f, indent=2)
        
        print(f"📋 Created download queue: {queue_file}")
        print(f"🎯 Priority books to download: {len(priority_queue)}")
        
        return queue_file
    
    def get_completion_stats(self):
        """Get completion statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_books,
                    COUNT(CASE WHEN is_completed = 1 THEN 1 END) as completed_books,
                    COUNT(CASE WHEN reading_priority = 1 THEN 1 END) as priority_books
                FROM audiobooks
            """)
            
            result = cursor.fetchone()
            return {
                'total_books': result[0],
                'completed_books': result[1], 
                'priority_books': result[2]
            }

def main():
    processor = ReadingCompletionProcessor()
    
    print("🚀 Processing Reading Completion Data...")
    print("="*50)
    
    # Add completion tracking schema
    processor.add_completion_tracking_schema()
    
    # Update completed books
    priority_queue = processor.update_completed_books()
    
    # Create download queue
    queue_file = processor.create_download_queue(priority_queue)
    
    # Get stats
    stats = processor.get_completion_stats()
    
    print("\n📊 Completion Statistics:")
    print(f"Total Audiobooks: {stats['total_books']}")
    print(f"Completed Books: {stats['completed_books']}")
    print(f"Priority Downloads: {stats['priority_books']}")
    
    print(f"\n✅ Ready for download! Queue file: {queue_file}")
    print("🎯 Next: Use this queue to download EPUBs via Babel's Archive")

if __name__ == "__main__":
    main()