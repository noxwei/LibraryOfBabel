#!/usr/bin/env python3
"""
Real Vector-Based Knowledge Graph Generator
Creates semantic knowledge graphs using actual embeddings from 838 books
Based on actual database schema with chunk_embeddings table
"""

import os
import json
import psycopg2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from collections import defaultdict, Counter
import random

class RealVectorKnowledgeGraph:
    def __init__(self):
        self.books = []
        self.chunk_embeddings = []
        self.book_embeddings = {}  # Aggregated book-level embeddings
        self.similarity_matrix = None
        
    def connect_to_database(self):
        """Connect to PostgreSQL using Dr. Sarah Chen's configuration"""
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'knowledge_base'),
                user=os.getenv('DB_USER', 'weixiangzhang'),
                port=int(os.getenv('DB_PORT', 5432))
            )
            return conn
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return None
    
    def load_books_and_embeddings(self, sample_size=None):
        """Load books and their embeddings from the database"""
        print("📚 Loading books and embeddings from database...")
        
        conn = self.connect_to_database()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # First, get all books
            cursor.execute("""
                SELECT book_id, title, author, genre, publication_year, description
                FROM books 
                ORDER BY book_id
            """)
            
            books_data = cursor.fetchall()
            print(f"📖 Found {len(books_data)} books in database")
            
            # Sample books if requested
            if sample_size and sample_size < len(books_data):
                books_data = random.sample(books_data, sample_size)
                print(f"🎲 Sampling {sample_size} books for analysis")
            
            # Load book metadata
            for book_row in books_data:
                book_data = {
                    'id': book_row[0],
                    'title': book_row[1] or "Unknown Title",
                    'author': book_row[2] or "Unknown Author",
                    'genre': book_row[3] or "Unknown Genre",
                    'year': book_row[4] or 0,
                    'description': book_row[5] or "",
                    'chunks': [],
                    'embedding_vectors': []
                }
                self.books.append(book_data)
            
            # Create book ID to index mapping
            book_id_to_index = {book['id']: i for i, book in enumerate(self.books)}
            
            # Load embeddings for these books
            book_ids = [str(book['id']) for book in self.books]
            book_ids_str = "(" + ",".join(book_ids) + ")"
            
            cursor.execute(f"""
                SELECT ce.book_id, ce.chunk_id, ce.embedding
                FROM chunk_embeddings ce
                WHERE ce.book_id IN {book_ids_str}
                ORDER BY ce.book_id, ce.chunk_id
            """)
            
            embeddings_data = cursor.fetchall()
            print(f"🧠 Found {len(embeddings_data)} embeddings for selected books")
            
            # Process embeddings
            for emb_row in embeddings_data:
                book_id = emb_row[0]
                chunk_id = emb_row[1]
                embedding_json = emb_row[2]
                
                if book_id in book_id_to_index:
                    book_index = book_id_to_index[book_id]
                    
                    # Parse embedding JSON
                    if isinstance(embedding_json, str):
                        embedding_vector = json.loads(embedding_json)
                    else:
                        embedding_vector = embedding_json
                    
                    # Convert to numpy array
                    if isinstance(embedding_vector, list):
                        embedding_array = np.array(embedding_vector, dtype=np.float32)
                        self.books[book_index]['embedding_vectors'].append(embedding_array)
                        self.books[book_index]['chunks'].append(chunk_id)
            
            # Aggregate book-level embeddings (mean of all chunks)
            books_with_embeddings = 0
            for book in self.books:
                if book['embedding_vectors']:
                    # Calculate mean embedding for the book
                    book_embedding = np.mean(book['embedding_vectors'], axis=0)
                    self.book_embeddings[book['id']] = book_embedding
                    books_with_embeddings += 1
            
            print(f"✅ Successfully loaded {books_with_embeddings} books with embeddings")
            print(f"📊 Average chunks per book: {sum(len(book['chunks']) for book in self.books) / len(self.books):.1f}")
            
            conn.close()
            return books_with_embeddings > 0
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            conn.close()
            return False
    
    def calculate_book_similarities(self):
        """Calculate cosine similarities between books using their aggregated embeddings"""
        print("🔗 Calculating book-to-book similarities...")
        
        # Get books that have embeddings
        books_with_embeddings = [book for book in self.books if book['id'] in self.book_embeddings]
        
        if len(books_with_embeddings) < 2:
            print("❌ Need at least 2 books with embeddings")
            return False
        
        # Create embedding matrix
        embedding_matrix = np.array([self.book_embeddings[book['id']] for book in books_with_embeddings])
        
        # Calculate similarity matrix
        self.similarity_matrix = cosine_similarity(embedding_matrix)
        
        print(f"✅ Calculated similarity matrix: {self.similarity_matrix.shape}")
        return True
    
    def create_semantic_book_network(self, output_path, similarity_threshold=0.75):
        """Create a network visualization showing semantic relationships between books"""
        print(f"🎨 Creating semantic book network (threshold: {similarity_threshold})...")
        
        # Get books with embeddings
        books_with_embeddings = [book for book in self.books if book['id'] in self.book_embeddings]
        n_books = len(books_with_embeddings)
        
        if n_books < 2:
            print("❌ Need at least 2 books with embeddings")
            return None
        
        # Use PCA to reduce dimensionality for visualization
        embedding_matrix = np.array([self.book_embeddings[book['id']] for book in books_with_embeddings])
        pca = PCA(n_components=2)
        positions_2d = pca.fit_transform(embedding_matrix)
        
        # Set up the figure
        fig, ax = plt.subplots(figsize=(20, 16))
        fig.patch.set_facecolor('white')
        
        # Find highly similar book pairs
        connections = []
        for i in range(n_books):
            for j in range(i + 1, n_books):
                similarity = self.similarity_matrix[i][j]
                if similarity > similarity_threshold:
                    connections.append((i, j, similarity))
        
        print(f"🔗 Found {len(connections)} strong semantic connections (similarity > {similarity_threshold})")
        
        # Color books by genre
        genres = [book['genre'] for book in books_with_embeddings]
        unique_genres = list(set(genres))
        colors = plt.cm.Set3(np.linspace(0, 1, len(unique_genres)))
        genre_color_map = {genre: colors[i] for i, genre in enumerate(unique_genres)}
        
        # Draw connections
        for i, j, similarity in connections:
            pos1 = positions_2d[i]
            pos2 = positions_2d[j]
            
            # Line thickness and transparency based on similarity
            linewidth = (similarity - similarity_threshold) * 20
            alpha = min(similarity * 0.8, 0.7)
            
            ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], 
                   'gray', alpha=alpha, linewidth=linewidth, zorder=1)
        
        # Draw books as nodes
        for i, book in enumerate(books_with_embeddings):
            pos = positions_2d[i]
            genre = book['genre']
            color = genre_color_map.get(genre, 'gray')
            
            # Node size based on number of chunks
            node_size = min(max(len(book['chunks']) * 3, 50), 300)
            
            # Plot book as a circle
            ax.scatter(pos[0], pos[1], c=[color], s=node_size, alpha=0.8, 
                      edgecolor='black', linewidth=0.5, zorder=3)
            
            # Add labels for highly connected books
            book_connections = sum(1 for conn in connections if i in [conn[0], conn[1]])
            if book_connections > 2:  # Show titles for highly connected books
                title = book['title'][:25] + "..." if len(book['title']) > 25 else book['title']
                ax.annotate(f"{title}\n({book['author'][:20]})", 
                           pos, xytext=(5, 5), textcoords='offset points',
                           fontsize=8, alpha=0.8, 
                           bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7))
        
        # Create genre legend
        legend_elements = [patches.Patch(color=genre_color_map[genre], label=f"{genre} ({genres.count(genre)} books)") 
                          for genre in unique_genres[:10]]  # Limit to top 10 genres
        ax.legend(handles=legend_elements, loc='upper right', fontsize=10, title="Genres")
        
        # Add title and labels
        ax.set_title(f'Semantic Knowledge Graph: {n_books} Books from LibraryOfBabel\n'
                    f'{len(connections)} Strong Semantic Connections (similarity > {similarity_threshold})\n'
                    f'Node size indicates number of text chunks analyzed',
                    fontsize=16, fontweight='bold', pad=20)
        
        # Calculate and display metrics
        if connections:
            avg_similarity = np.mean([sim for _, _, sim in connections])
            max_similarity = max([sim for _, _, sim in connections])
            
            # Find most connected books
            connection_counts = defaultdict(int)
            for i, j, _ in connections:
                connection_counts[i] += 1
                connection_counts[j] += 1
            
            most_connected = max(connection_counts.items(), key=lambda x: x[1]) if connection_counts else (0, 0)
            most_connected_book = books_with_embeddings[most_connected[0]] if connection_counts else None
            
            metrics_text = f"Strong Connections: {len(connections)}\n" \
                          f"Avg Similarity: {avg_similarity:.3f}\n" \
                          f"Max Similarity: {max_similarity:.3f}\n" \
                          f"Most Connected: {most_connected_book['title'][:30] if most_connected_book else 'N/A'}\n" \
                          f"Connection Count: {most_connected[1]}"
        else:
            metrics_text = f"No connections found above threshold {similarity_threshold}\n" \
                          f"Consider lowering threshold for analysis"
        
        ax.text(0.02, 0.98, metrics_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8))
        
        # Style the plot
        ax.set_xlabel('Principal Component 1 (Semantic Dimension)', fontsize=12)
        ax.set_ylabel('Principal Component 2 (Semantic Dimension)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Save
        plt.tight_layout()
        plt.savefig(output_path, format='jpeg', dpi=300, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        plt.close()
        
        return {
            'output_path': output_path,
            'books_analyzed': n_books,
            'connections_found': len(connections),
            'avg_similarity': avg_similarity if connections else 0,
            'most_connected_book': most_connected_book['title'] if most_connected_book else None
        }
    
    def create_genre_cluster_analysis(self, output_path):
        """Create visualization analyzing genre clusters and relationships"""
        print("📊 Creating genre cluster analysis...")
        
        books_with_embeddings = [book for book in self.books if book['id'] in self.book_embeddings]
        
        if len(books_with_embeddings) < 5:
            print("❌ Need at least 5 books for cluster analysis")
            return None
        
        # Perform clustering
        embedding_matrix = np.array([self.book_embeddings[book['id']] for book in books_with_embeddings])
        n_clusters = min(8, len(books_with_embeddings) // 3)  # Adaptive cluster count
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embedding_matrix)
        
        # Analyze clusters
        clusters = defaultdict(lambda: {'books': [], 'genres': Counter(), 'years': []})
        
        for i, book in enumerate(books_with_embeddings):
            cluster_id = cluster_labels[i]
            clusters[cluster_id]['books'].append(book)
            clusters[cluster_id]['genres'][book['genre']] += 1
            if book['year'] and book['year'] > 0:
                clusters[cluster_id]['years'].append(book['year'])
        
        # Create visualization
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
        fig.patch.set_facecolor('white')
        
        # 1. Cluster sizes
        cluster_sizes = [len(clusters[i]['books']) for i in range(n_clusters)]
        cluster_names = [f"Cluster {i}" for i in range(n_clusters)]
        
        bars = ax1.bar(cluster_names, cluster_sizes, color=plt.cm.Set3(np.linspace(0, 1, n_clusters)))
        ax1.set_title('Books per Semantic Cluster', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Number of Books')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom')
        
        # 2. Genre distribution heatmap
        all_genres = set()
        for cluster_data in clusters.values():
            all_genres.update(cluster_data['genres'].keys())
        
        all_genres = sorted(list(all_genres))[:15]  # Limit to top 15 genres
        
        genre_matrix = []
        for i in range(n_clusters):
            cluster_genres = []
            for genre in all_genres:
                count = clusters[i]['genres'].get(genre, 0)
                cluster_genres.append(count)
            genre_matrix.append(cluster_genres)
        
        im = ax2.imshow(genre_matrix, cmap='YlOrRd', aspect='auto')
        ax2.set_title('Genre Distribution by Semantic Cluster', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Genres')
        ax2.set_ylabel('Clusters')
        ax2.set_xticks(range(len(all_genres)))
        ax2.set_xticklabels(all_genres, rotation=45, ha='right')
        ax2.set_yticks(range(n_clusters))
        ax2.set_yticklabels([f"C{i}" for i in range(n_clusters)])
        
        # Add colorbar
        plt.colorbar(im, ax=ax2, label='Number of Books')
        
        # 3. Publication year trends
        all_years = []
        for cluster_data in clusters.values():
            all_years.extend(cluster_data['years'])
        
        if all_years:
            ax3.hist(all_years, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            ax3.set_title('Publication Year Distribution', fontsize=14, fontweight='bold')
            ax3.set_xlabel('Publication Year')
            ax3.set_ylabel('Number of Books')
            
            # Add mean line
            mean_year = np.mean(all_years)
            ax3.axvline(mean_year, color='red', linestyle='--', 
                       label=f'Mean: {int(mean_year)}')
            ax3.legend()
        
        # 4. Cluster characteristics summary
        ax4.axis('off')
        summary_text = "Semantic Cluster Analysis Summary\n\n"
        
        for i in range(n_clusters):
            cluster_data = clusters[i]
            book_count = len(cluster_data['books'])
            
            # Top genre
            if cluster_data['genres']:
                top_genre = cluster_data['genres'].most_common(1)[0]
                genre_text = f"{top_genre[0]} ({top_genre[1]} books)"
            else:
                genre_text = "No genre data"
            
            # Average year
            if cluster_data['years']:
                avg_year = int(np.mean(cluster_data['years']))
                year_range = f"{min(cluster_data['years'])}-{max(cluster_data['years'])}"
                year_text = f"Avg: {avg_year} (Range: {year_range})"
            else:
                year_text = "No year data"
            
            # Sample books
            sample_books = cluster_data['books'][:3]
            book_samples = [f"'{book['title'][:25]}...'" if len(book['title']) > 25 else f"'{book['title']}'" 
                           for book in sample_books]
            
            summary_text += f"Cluster {i} ({book_count} books):\n"
            summary_text += f"  Primary Genre: {genre_text}\n"
            summary_text += f"  Publication: {year_text}\n"
            summary_text += f"  Sample Books: {', '.join(book_samples)}\n\n"
        
        ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(output_path, format='jpeg', dpi=300, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close()
        
        return {
            'output_path': output_path,
            'clusters_created': n_clusters,
            'books_analyzed': len(books_with_embeddings),
            'cluster_summary': {i: {'size': len(clusters[i]['books']), 
                                   'primary_genre': clusters[i]['genres'].most_common(1)[0][0] if clusters[i]['genres'] else 'Unknown'}
                               for i in range(n_clusters)}
        }

def main():
    print("🚀 Starting Real Vector-Based Knowledge Graph Generation...")
    print("📊 Using actual embeddings from LibraryOfBabel database")
    
    # Initialize generator
    kg = RealVectorKnowledgeGraph()
    
    # Load data (sample for testing, remove sample_size for full dataset)
    if not kg.load_books_and_embeddings(sample_size=100):  # Sample 100 books for testing
        print("❌ Failed to load books and embeddings")
        return
    
    # Calculate similarities
    if not kg.calculate_book_similarities():
        print("❌ Failed to calculate similarities")
        return
    
    # Generate visualizations
    output_dir = '/Users/weixiangzhang/Local_Dev/LibraryOfBabel/agents/reddit_bibliophile'
    
    # 1. Semantic network visualization
    print("\n🎨 Creating semantic book network...")
    network_path = os.path.join(output_dir, 'real_semantic_book_network.jpg')
    network_result = kg.create_semantic_book_network(network_path, similarity_threshold=0.7)
    
    if network_result:
        print(f"✅ Semantic network created: {network_result['connections_found']} connections")
        print(f"📚 Books analyzed: {network_result['books_analyzed']}")
        if network_result['most_connected_book']:
            print(f"🌟 Most connected book: {network_result['most_connected_book']}")
    
    # 2. Genre cluster analysis
    print("\n📊 Creating genre cluster analysis...")
    cluster_path = os.path.join(output_dir, 'real_genre_cluster_analysis.jpg')
    cluster_result = kg.create_genre_cluster_analysis(cluster_path)
    
    if cluster_result:
        print(f"✅ Cluster analysis created: {cluster_result['clusters_created']} clusters")
        print(f"📈 Cluster summary: {cluster_result['cluster_summary']}")
    
    print(f"\n🎯 Real vector knowledge graphs saved to: {output_dir}")

if __name__ == "__main__":
    main()