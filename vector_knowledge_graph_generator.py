#!/usr/bin/env python3
"""
Vector-Based Knowledge Graph Generator
Creates semantic knowledge graphs using vector embeddings from 800 books
"""

import psycopg2
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import os

class VectorKnowledgeGraph:
    def __init__(self):
        self.books = []
        self.embeddings = []
        self.similarity_matrix = None
        
    def connect_to_database(self):
        """Connect to PostgreSQL and fetch books with embeddings"""
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'knowledge_base'),
                user=os.getenv('DB_USER', 'weixiangzhang'),
                port=int(os.getenv('DB_PORT', 5432))
            )
            cursor = conn.cursor()
            
            # Fetch all books with their vector embeddings
            query = """
            SELECT id, title, author, genre, publication_year, 
                   description, embedding
            FROM books 
            WHERE embedding IS NOT NULL
            ORDER BY id
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            print(f"📚 Retrieved {len(results)} books with embeddings")
            
            for row in results:
                book_data = {
                    'id': row[0],
                    'title': row[1],
                    'author': row[2],
                    'genre': row[3],
                    'year': row[4],
                    'description': row[5],
                    'embedding': np.array(row[6]) if row[6] else None
                }
                
                if book_data['embedding'] is not None:
                    self.books.append(book_data)
                    self.embeddings.append(book_data['embedding'])
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def calculate_semantic_similarities(self):
        """Calculate cosine similarities between all book embeddings"""
        if not self.embeddings:
            return False
            
        embeddings_matrix = np.array(self.embeddings)
        self.similarity_matrix = cosine_similarity(embeddings_matrix)
        
        print(f"🔗 Calculated similarity matrix: {self.similarity_matrix.shape}")
        return True
    
    def find_semantic_clusters(self, n_clusters=10):
        """Cluster books based on semantic similarity"""
        embeddings_matrix = np.array(self.embeddings)
        
        # Use KMeans clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings_matrix)
        
        # Add cluster labels to books
        for i, book in enumerate(self.books):
            book['cluster'] = cluster_labels[i]
        
        # Analyze clusters
        clusters = {}
        for i, book in enumerate(self.books):
            cluster_id = book['cluster']
            if cluster_id not in clusters:
                clusters[cluster_id] = {
                    'books': [],
                    'genres': {},
                    'authors': {},
                    'years': []
                }
            
            clusters[cluster_id]['books'].append(book)
            
            # Track genres
            genre = book.get('genre', 'Unknown')
            clusters[cluster_id]['genres'][genre] = clusters[cluster_id]['genres'].get(genre, 0) + 1
            
            # Track authors
            author = book.get('author', 'Unknown')
            clusters[cluster_id]['authors'][author] = clusters[cluster_id]['authors'].get(author, 0) + 1
            
            # Track years
            if book.get('year'):
                clusters[cluster_id]['years'].append(book['year'])
        
        return clusters
    
    def create_semantic_network_visualization(self, output_path, similarity_threshold=0.7):
        """Create a network visualization showing semantic relationships"""
        
        # Use PCA to reduce dimensionality for visualization
        pca = PCA(n_components=2)
        embeddings_2d = pca.fit_transform(np.array(self.embeddings))
        
        # Set up the figure
        fig, ax = plt.subplots(figsize=(20, 16))
        fig.patch.set_facecolor('white')
        
        # Find highly similar book pairs
        n_books = len(self.books)
        connections = []
        
        for i in range(n_books):
            for j in range(i + 1, n_books):
                similarity = self.similarity_matrix[i][j]
                if similarity > similarity_threshold:
                    connections.append((i, j, similarity))
        
        print(f"🔗 Found {len(connections)} strong semantic connections (similarity > {similarity_threshold})")
        
        # Draw connections
        for i, j, similarity in connections:
            pos1 = embeddings_2d[i]
            pos2 = embeddings_2d[j]
            
            # Line thickness based on similarity
            linewidth = (similarity - similarity_threshold) * 10
            alpha = min(similarity, 0.8)
            
            ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], 
                   'gray', alpha=alpha, linewidth=linewidth)
        
        # Color books by cluster
        clusters = self.find_semantic_clusters(n_clusters=8)
        colors = plt.cm.Set3(np.linspace(0, 1, 8))
        
        for i, book in enumerate(self.books):
            pos = embeddings_2d[i]
            cluster = book['cluster']
            
            # Plot book as a point
            ax.scatter(pos[0], pos[1], c=[colors[cluster]], s=100, alpha=0.8, zorder=3)
            
            # Add title for highly connected books
            book_connections = sum(1 for conn in connections if i in [conn[0], conn[1]])
            if book_connections > 3:  # Show titles for highly connected books
                title = book['title'][:30] + "..." if len(book['title']) > 30 else book['title']
                ax.annotate(title, pos, xytext=(5, 5), textcoords='offset points',
                           fontsize=8, alpha=0.7)
        
        # Create cluster legend
        cluster_info = []
        for cluster_id, cluster_data in clusters.items():
            top_genre = max(cluster_data['genres'].items(), key=lambda x: x[1])[0]
            book_count = len(cluster_data['books'])
            cluster_info.append(f"Cluster {cluster_id}: {top_genre} ({book_count} books)")
        
        # Add legend
        legend_elements = [patches.Patch(color=colors[i], label=cluster_info[i]) 
                          for i in range(min(len(cluster_info), 8))]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
        
        # Add title and labels
        ax.set_title(f'Semantic Knowledge Graph: 800 Books Vector Network\n'
                    f'{len(connections)} Strong Semantic Connections (similarity > {similarity_threshold})\n'
                    f'PCA Visualization of {len(self.embeddings)}-dimensional embeddings',
                    fontsize=16, fontweight='bold', pad=20)
        
        # Add metrics
        avg_similarity = np.mean([sim for _, _, sim in connections])
        metrics_text = f"Strong Connections: {len(connections)}\n" \
                      f"Avg Similarity: {avg_similarity:.3f}\n" \
                      f"Similarity Threshold: {similarity_threshold}\n" \
                      f"Total Books: {len(self.books)}"
        
        ax.text(0.02, 0.98, metrics_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8))
        
        # Style the plot
        ax.set_xlabel('Principal Component 1', fontsize=12)
        ax.set_ylabel('Principal Component 2', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Save
        plt.tight_layout()
        plt.savefig(output_path, format='jpeg', dpi=300, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        plt.close()
        
        return output_path, len(connections), clusters
    
    def create_cluster_analysis_visualization(self, clusters, output_path):
        """Create detailed cluster analysis visualization"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
        fig.patch.set_facecolor('white')
        
        # 1. Cluster sizes
        cluster_sizes = [len(cluster_data['books']) for cluster_data in clusters.values()]
        cluster_labels = [f"Cluster {i}" for i in clusters.keys()]
        
        ax1.bar(cluster_labels, cluster_sizes, color=plt.cm.Set3(np.linspace(0, 1, len(clusters))))
        ax1.set_title('Books per Semantic Cluster', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Number of Books')
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Genre distribution across clusters
        all_genres = set()
        for cluster_data in clusters.values():
            all_genres.update(cluster_data['genres'].keys())
        
        genre_matrix = []
        for cluster_id in sorted(clusters.keys()):
            cluster_genres = []
            for genre in sorted(all_genres):
                count = clusters[cluster_id]['genres'].get(genre, 0)
                cluster_genres.append(count)
            genre_matrix.append(cluster_genres)
        
        im = ax2.imshow(genre_matrix, cmap='YlOrRd', aspect='auto')
        ax2.set_title('Genre Distribution by Cluster', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Genres')
        ax2.set_ylabel('Clusters')
        ax2.set_xticks(range(len(sorted(all_genres))))
        ax2.set_xticklabels(sorted(all_genres), rotation=45, ha='right')
        ax2.set_yticks(range(len(clusters)))
        ax2.set_yticklabels([f"C{i}" for i in sorted(clusters.keys())])
        
        # 3. Publication year distribution
        all_years = []
        cluster_years = []
        for cluster_id in sorted(clusters.keys()):
            years = clusters[cluster_id]['years']
            if years:
                all_years.extend(years)
                cluster_years.append(np.mean(years))
            else:
                cluster_years.append(0)
        
        if all_years:
            ax3.hist(all_years, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            ax3.set_title('Publication Year Distribution', fontsize=14, fontweight='bold')
            ax3.set_xlabel('Publication Year')
            ax3.set_ylabel('Number of Books')
        
        # 4. Cluster characteristics summary
        ax4.axis('off')
        summary_text = "Semantic Cluster Analysis\n\n"
        
        for cluster_id in sorted(clusters.keys()):
            cluster_data = clusters[cluster_id]
            book_count = len(cluster_data['books'])
            
            # Top genre
            if cluster_data['genres']:
                top_genre = max(cluster_data['genres'].items(), key=lambda x: x[1])
                genre_text = f"{top_genre[0]} ({top_genre[1]} books)"
            else:
                genre_text = "No genre data"
            
            # Average year
            if cluster_data['years']:
                avg_year = int(np.mean(cluster_data['years']))
                year_text = f"Avg: {avg_year}"
            else:
                year_text = "No year data"
            
            summary_text += f"Cluster {cluster_id}: {book_count} books\n"
            summary_text += f"  Primary Genre: {genre_text}\n"
            summary_text += f"  Publication: {year_text}\n\n"
        
        ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, fontsize=11,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(output_path, format='jpeg', dpi=300, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close()
        
        return output_path

def main():
    print("🚀 Starting Vector-Based Knowledge Graph Generation...")
    
    # Initialize generator
    kg = VectorKnowledgeGraph()
    
    # Connect to database and load books
    if not kg.connect_to_database():
        print("❌ Failed to connect to database")
        return
    
    if len(kg.books) == 0:
        print("❌ No books with embeddings found")
        return
    
    # Calculate similarities
    if not kg.calculate_semantic_similarities():
        print("❌ Failed to calculate similarities")
        return
    
    # Generate visualizations
    output_dir = '/Users/weixiangzhang/Local_Dev/LibraryOfBabel/agents/reddit_bibliophile'
    
    # 1. Semantic network visualization
    network_path = os.path.join(output_dir, 'vector_semantic_network.jpg')
    network_result = kg.create_semantic_network_visualization(network_path, similarity_threshold=0.7)
    
    if network_result:
        path, connections, clusters = network_result
        print(f"✅ Created semantic network: {connections} connections")
        
        # 2. Cluster analysis visualization
        cluster_path = os.path.join(output_dir, 'vector_cluster_analysis.jpg')
        kg.create_cluster_analysis_visualization(clusters, cluster_path)
        print(f"✅ Created cluster analysis: {len(clusters)} clusters")
    
    print(f"🎯 Vector knowledge graphs saved to: {output_dir}")

if __name__ == "__main__":
    main()