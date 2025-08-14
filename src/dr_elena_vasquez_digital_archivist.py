#!/usr/bin/env python3
"""
📊 Dr. Elena Vásquez - Digital Archivist & Knowledge Mapping Specialist
========================================================================

Senior Digital Archivist specializing in concept mapping, knowledge graphs, 
and data visualization for large-scale library systems. Expert in transforming 
complex bibliographic relationships into interactive visual diagrams.

🎯 Specializations:
- Concept mapping and knowledge graph generation
- Multi-modal data visualization (books, authors, subjects, embeddings)
- Interactive diagram creation (Mermaid, D3.js, Graphviz)
- Semantic relationship analysis
- Digital preservation workflows
- Data lineage and provenance tracking

🧠 AI Integration:
- Uses embedding vectors to identify conceptual clusters
- Generates visual representations of semantic relationships
- Creates dynamic knowledge maps from bibliographic metadata
- Builds interactive dashboards for library analytics

Dr. Vásquez combines traditional archival science with modern data science
to create compelling visual narratives from complex information systems.
"""

import os
import sys
import json
import logging
import psycopg2
import psycopg2.extras
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

@dataclass
class ConceptNode:
    """Represents a concept in the knowledge graph"""
    id: str
    label: str
    category: str
    weight: float
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    
@dataclass
class ConceptEdge:
    """Represents a relationship between concepts"""
    source: str
    target: str
    relationship: str
    strength: float
    metadata: Dict[str, Any]

class DigitalArchivistVasquez:
    """
    🏛️ Dr. Elena Vásquez - Digital Archivist & Knowledge Mapping Expert
    
    Specializes in creating visual concept maps and knowledge graphs from 
    LibraryOfBabel's multi-modal embedding data and bibliographic metadata.
    """
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.output_dir = project_root / "visualizations" / "concept_maps"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base',
            'user': 'weixiangzhang',
            'password': os.environ.get('DB_PASSWORD')
        }
        
        # Visualization settings
        self.color_palette = {
            'technical': '#1f77b4',      # Blue
            'narrative': '#ff7f0e',      # Orange  
            'multilingual': '#2ca02c',   # Green
            'general': '#d62728',        # Red
            'unknown': '#9467bd'         # Purple
        }
        
        self.logger.info("📊 Dr. Elena Vásquez - Digital Archivist initialized")
        self.logger.info("🎨 Concept mapping and visualization system ready")
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the digital archivist"""
        log_dir = project_root / "logs" / "digital_archivist"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - Dr.Vásquez - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "archivist.log"),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger("DigitalArchivist")
        
    def get_db_connection(self):
        """Get PostgreSQL connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            self.logger.error(f"Database connection failed: {e}")
            return None
            
    def extract_bibliographic_network(self) -> Tuple[List[ConceptNode], List[ConceptEdge]]:
        """
        Extract nodes and edges for bibliographic concept mapping
        
        Returns:
            Tuple of (nodes, edges) representing the knowledge graph
        """
        self.logger.info("📚 Extracting bibliographic network data...")
        
        nodes = []
        edges = []
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return nodes, edges
                    
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Extract book nodes
                    cur.execute("""
                        SELECT 
                            book_id,
                            title,
                            author,
                            genre,
                            publication_year,
                            language,
                            COUNT(c.chunk_id) as chunk_count,
                            AVG(CASE WHEN c.embedding_nomic IS NOT NULL THEN 1 ELSE 0 END) as embedding_coverage
                        FROM books b
                        LEFT JOIN chunks c ON b.book_id = c.book_id
                        GROUP BY book_id, title, author, genre, publication_year, language
                        HAVING COUNT(c.chunk_id) > 0
                        ORDER BY chunk_count DESC
                        LIMIT 500
                    """)
                    
                    books = cur.fetchall()
                    self.logger.info(f"📖 Found {len(books)} books for network analysis")
                    
                    # Create book nodes
                    for book in books:
                        nodes.append(ConceptNode(
                            id=f"book_{book['book_id']}",
                            label=book['title'][:50] + ("..." if len(book['title']) > 50 else ""),
                            category="book",
                            weight=float(book['chunk_count']),
                            metadata={
                                'book_id': book['book_id'],
                                'title': book['title'],
                                'author': book['author'],
                                'genre': book['genre'],
                                'year': book['publication_year'],
                                'language': book['language'],
                                'chunks': book['chunk_count'],
                                'embedding_coverage': float(book['embedding_coverage'] or 0)
                            }
                        ))
                    
                    # Extract author nodes and relationships
                    authors = {}
                    for book in books:
                        if book['author'] and book['author'].strip():
                            author_key = book['author'].strip().lower()
                            if author_key not in authors:
                                authors[author_key] = {
                                    'name': book['author'].strip(),
                                    'books': [],
                                    'total_chunks': 0
                                }
                            authors[author_key]['books'].append(book['book_id'])
                            authors[author_key]['total_chunks'] += book['chunk_count']
                    
                    # Create author nodes and edges
                    for author_key, author_data in authors.items():
                        if len(author_data['books']) > 1:  # Only authors with multiple books
                            nodes.append(ConceptNode(
                                id=f"author_{author_key.replace(' ', '_')}",
                                label=author_data['name'],
                                category="author",
                                weight=float(author_data['total_chunks']),
                                metadata={
                                    'name': author_data['name'],
                                    'book_count': len(author_data['books']),
                                    'total_chunks': author_data['total_chunks']
                                }
                            ))
                            
                            # Create author-book edges
                            for book_id in author_data['books']:
                                edges.append(ConceptEdge(
                                    source=f"author_{author_key.replace(' ', '_')}",
                                    target=f"book_{book_id}",
                                    relationship="authored",
                                    strength=1.0,
                                    metadata={'type': 'authorship'}
                                ))
                    
                    # Extract genre clustering
                    genres = {}
                    for book in books:
                        if book['genre'] and book['genre'].strip():
                            genre_key = book['genre'].strip().lower()
                            if genre_key not in genres:
                                genres[genre_key] = {
                                    'name': book['genre'].strip(),
                                    'books': [],
                                    'total_chunks': 0
                                }
                            genres[genre_key]['books'].append(book['book_id'])
                            genres[genre_key]['total_chunks'] += book['chunk_count']
                    
                    # Create genre nodes and edges (for genres with multiple books)
                    for genre_key, genre_data in genres.items():
                        if len(genre_data['books']) > 2:  # Only genres with 3+ books
                            nodes.append(ConceptNode(
                                id=f"genre_{genre_key.replace(' ', '_')}",
                                label=genre_data['name'],
                                category="genre",
                                weight=float(genre_data['total_chunks']),
                                metadata={
                                    'name': genre_data['name'],
                                    'book_count': len(genre_data['books']),
                                    'total_chunks': genre_data['total_chunks']
                                }
                            ))
                            
                            # Create genre-book edges
                            for book_id in genre_data['books']:
                                edges.append(ConceptEdge(
                                    source=f"genre_{genre_key.replace(' ', '_')}",
                                    target=f"book_{book_id}",
                                    relationship="categorized_as",
                                    strength=0.7,
                                    metadata={'type': 'classification'}
                                ))
                                
        except Exception as e:
            self.logger.error(f"Error extracting bibliographic network: {e}")
            
        self.logger.info(f"🕸️ Network extracted: {len(nodes)} nodes, {len(edges)} edges")
        return nodes, edges
        
    def create_interactive_concept_map(self, nodes: List[ConceptNode], edges: List[ConceptEdge]) -> str:
        """
        Create an interactive concept map using Plotly
        
        Args:
            nodes: List of concept nodes
            edges: List of concept edges
            
        Returns:
            File path of generated HTML visualization
        """
        self.logger.info("🎨 Creating interactive concept map...")
        
        # Create NetworkX graph for layout calculation
        G = nx.Graph()
        
        # Add nodes
        for node in nodes:
            G.add_node(node.id, **node.metadata, category=node.category, weight=node.weight)
            
        # Add edges
        for edge in edges:
            G.add_edge(edge.source, edge.target, weight=edge.strength, relationship=edge.relationship)
        
        # Calculate layout using spring layout
        pos = nx.spring_layout(G, k=3, iterations=50, seed=42)
        
        # Prepare node traces by category
        node_traces = {}
        categories = set(node.category for node in nodes)
        
        for category in categories:
            node_traces[category] = {
                'x': [],
                'y': [],
                'text': [],
                'customdata': [],
                'hovertemplate': []
            }
        
        # Populate node data
        for node in nodes:
            if node.id in pos:
                x, y = pos[node.id]
                node_traces[node.category]['x'].append(x)
                node_traces[node.category]['y'].append(y)
                node_traces[node.category]['text'].append(node.label)
                node_traces[node.category]['customdata'].append(node.metadata)
                
                # Create hover template based on category
                if node.category == 'book':
                    hover_text = f"<b>{node.label}</b><br>"
                    hover_text += f"Author: {node.metadata.get('author', 'Unknown')}<br>"
                    hover_text += f"Genre: {node.metadata.get('genre', 'Unknown')}<br>"
                    hover_text += f"Chunks: {node.metadata.get('chunks', 0)}<br>"
                    hover_text += f"Embedding Coverage: {node.metadata.get('embedding_coverage', 0):.1%}"
                elif node.category == 'author':
                    hover_text = f"<b>{node.label}</b><br>"
                    hover_text += f"Books: {node.metadata.get('book_count', 0)}<br>"
                    hover_text += f"Total Chunks: {node.metadata.get('total_chunks', 0)}"
                elif node.category == 'genre':
                    hover_text = f"<b>{node.label}</b><br>"
                    hover_text += f"Books: {node.metadata.get('book_count', 0)}<br>"
                    hover_text += f"Total Chunks: {node.metadata.get('total_chunks', 0)}"
                else:
                    hover_text = f"<b>{node.label}</b>"
                    
                node_traces[node.category]['hovertemplate'].append(hover_text)
        
        # Create edge traces
        edge_x = []
        edge_y = []
        edge_info = []
        
        for edge in edges:
            if edge.source in pos and edge.target in pos:
                x0, y0 = pos[edge.source]
                x1, y1 = pos[edge.target]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                edge_info.append(f"{edge.relationship} ({edge.strength:.2f})")
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add edge trace
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='rgba(125,125,125,0.5)'),
            hoverinfo='none',
            mode='lines',
            name='Relationships'
        ))
        
        # Add node traces by category
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
        for i, (category, trace_data) in enumerate(node_traces.items()):
            if trace_data['x']:  # Only add if there are nodes in this category
                fig.add_trace(go.Scatter(
                    x=trace_data['x'],
                    y=trace_data['y'],
                    mode='markers+text',
                    name=category.capitalize(),
                    text=trace_data['text'],
                    textposition="middle center",
                    hovertemplate=trace_data['hovertemplate'],
                    marker=dict(
                        size=[min(50, max(8, np.log10(G.nodes[nodes[j].id]['weight']) * 5)) 
                              for j, node in enumerate(nodes) if node.category == category and node.id in pos],
                        color=colors[i % len(colors)],
                        line=dict(width=1, color='white')
                    )
                ))
        
        # Update layout
        fig.update_layout(
            title={
                'text': "📊 LibraryOfBabel Knowledge Graph - Dr. Elena Vásquez",
                'x': 0.5,
                'font': {'size': 20}
            },
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[
                dict(
                    text=f"Interactive concept map showing relationships between {len(nodes)} entities",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002,
                    xanchor='left', yanchor='bottom',
                    font=dict(color='gray', size=12)
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )
        
        # Save interactive HTML
        output_file = self.output_dir / f"concept_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        fig.write_html(str(output_file))
        
        self.logger.info(f"🎨 Interactive concept map saved: {output_file}")
        return str(output_file)
        
    def create_embedding_clusters_visualization(self) -> str:
        """
        Create visualization of embedding clusters using t-SNE
        
        Returns:
            File path of generated visualization
        """
        self.logger.info("🧠 Creating embedding clusters visualization...")
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return ""
                    
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Get chunks with embeddings and metadata
                    cur.execute("""
                        SELECT 
                            c.chunk_id,
                            c.content_type,
                            c.embedding_model_used,
                            c.embedding_nomic,
                            c.embedding_mxbai,
                            c.embedding_bge,
                            b.title,
                            b.author,
                            b.genre,
                            LEFT(c.content, 100) as content_sample
                        FROM chunks c
                        JOIN books b ON c.book_id = b.book_id
                        WHERE c.embedding_nomic IS NOT NULL
                        AND c.embedding_mxbai IS NOT NULL  
                        AND c.embedding_bge IS NOT NULL
                        ORDER BY RANDOM()
                        LIMIT 1000
                    """)
                    
                    chunks = cur.fetchall()
                    
            if not chunks:
                self.logger.warning("No chunks with embeddings found for visualization")
                return ""
                
            self.logger.info(f"🔍 Analyzing {len(chunks)} chunks with embeddings")
            
            # Prepare embedding data for different models
            embeddings = {
                'nomic': [],
                'mxbai': [], 
                'bge': []
            }
            
            labels = []
            metadata = []
            
            for chunk in chunks:
                if chunk['embedding_nomic'] and chunk['embedding_mxbai'] and chunk['embedding_bge']:
                    embeddings['nomic'].append(chunk['embedding_nomic'])
                    embeddings['mxbai'].append(chunk['embedding_mxbai'])
                    embeddings['bge'].append(chunk['embedding_bge'])
                    
                    labels.append(chunk['content_type'] or 'unknown')
                    metadata.append({
                        'chunk_id': chunk['chunk_id'],
                        'title': chunk['title'],
                        'author': chunk['author'],
                        'genre': chunk['genre'],
                        'content_sample': chunk['content_sample'],
                        'model_used': chunk['embedding_model_used']
                    })
            
            # Create subplots for different embedding models
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=['Nomic Embeddings (768d)', 'MXBAI Embeddings (1024d)', 
                               'BGE Embeddings (1024d)', 'Combined Analysis'],
                specs=[[{"type": "scatter"}, {"type": "scatter"}],
                       [{"type": "scatter"}, {"type": "scatter"}]]
            )
            
            # Process each embedding model
            model_positions = {}
            
            for idx, (model_name, emb_data) in enumerate(embeddings.items()):
                if not emb_data:
                    continue
                    
                # Convert to numpy array
                X = np.array(emb_data)
                
                # Apply t-SNE for dimensionality reduction
                self.logger.info(f"📊 Applying t-SNE to {model_name} embeddings...")
                tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(X)-1))
                X_tsne = tsne.fit_transform(X)
                
                model_positions[model_name] = X_tsne
                
                # Determine subplot position
                row = (idx // 2) + 1
                col = (idx % 2) + 1
                
                # Create scatter plot colored by content type
                for content_type in set(labels):
                    mask = [l == content_type for l in labels]
                    if any(mask):
                        x_vals = X_tsne[mask, 0]
                        y_vals = X_tsne[mask, 1]
                        
                        hover_text = [
                            f"<b>{metadata[i]['title'][:30]}...</b><br>"
                            f"Author: {metadata[i]['author']}<br>"
                            f"Genre: {metadata[i]['genre']}<br>"
                            f"Content: {metadata[i]['content_sample'][:50]}..."
                            for i, m in enumerate(mask) if m
                        ]
                        
                        fig.add_trace(
                            go.Scatter(
                                x=x_vals,
                                y=y_vals,
                                mode='markers',
                                name=f"{content_type}-{model_name}",
                                marker=dict(
                                    size=6,
                                    color=self.color_palette.get(content_type, self.color_palette['unknown']),
                                    opacity=0.7
                                ),
                                hovertemplate=hover_text,
                                showlegend=(idx == 0)  # Only show legend for first model
                            ),
                            row=row, col=col
                        )
            
            # Create combined analysis (average of embeddings)
            if len(model_positions) >= 2:
                # Simple average of t-SNE positions (not ideal but illustrative)
                combined_pos = np.mean([pos for pos in model_positions.values()], axis=0)
                
                for content_type in set(labels):
                    mask = [l == content_type for l in labels]
                    if any(mask):
                        x_vals = combined_pos[mask, 0]
                        y_vals = combined_pos[mask, 1]
                        
                        fig.add_trace(
                            go.Scatter(
                                x=x_vals,
                                y=y_vals,
                                mode='markers',
                                name=f"{content_type}-combined",
                                marker=dict(
                                    size=8,
                                    color=self.color_palette.get(content_type, self.color_palette['unknown']),
                                    opacity=0.8
                                ),
                                showlegend=False
                            ),
                            row=2, col=2
                        )
            
            # Update layout
            fig.update_layout(
                title={
                    'text': "🧠 Multi-Modal Embedding Clusters Analysis - Dr. Elena Vásquez",
                    'x': 0.5,
                    'font': {'size': 16}
                },
                height=800,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Update axes
            for i in range(1, 3):
                for j in range(1, 3):
                    fig.update_xaxes(title_text="t-SNE Dimension 1", row=i, col=j)
                    fig.update_yaxes(title_text="t-SNE Dimension 2", row=i, col=j)
            
            # Save visualization
            output_file = self.output_dir / f"embedding_clusters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            fig.write_html(str(output_file))
            
            self.logger.info(f"🧠 Embedding clusters visualization saved: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Error creating embedding visualization: {e}")
            return ""
            
    def generate_mermaid_diagram(self, nodes: List[ConceptNode], edges: List[ConceptEdge]) -> str:
        """
        Generate Mermaid diagram syntax for the concept map
        
        Args:
            nodes: List of concept nodes
            edges: List of concept edges
            
        Returns:
            Mermaid diagram syntax as string
        """
        self.logger.info("📝 Generating Mermaid diagram syntax...")
        
        mermaid_lines = ["graph TD"]
        
        # Add nodes with styling
        for node in nodes:
            node_id = node.id.replace('-', '_').replace(' ', '_')
            label = node.label.replace('"', "'")
            
            if node.category == 'book':
                mermaid_lines.append(f'    {node_id}["{label}"]')
                mermaid_lines.append(f'    class {node_id} bookNode')
            elif node.category == 'author':
                mermaid_lines.append(f'    {node_id}(("{label}"))')
                mermaid_lines.append(f'    class {node_id} authorNode')
            elif node.category == 'genre':
                mermaid_lines.append(f'    {node_id}{{{label}}}')
                mermaid_lines.append(f'    class {node_id} genreNode')
        
        # Add edges
        for edge in edges:
            source_id = edge.source.replace('-', '_').replace(' ', '_')
            target_id = edge.target.replace('-', '_').replace(' ', '_')
            
            if edge.relationship == 'authored':
                mermaid_lines.append(f'    {source_id} --> {target_id}')
            elif edge.relationship == 'categorized_as':
                mermaid_lines.append(f'    {source_id} -.-> {target_id}')
            else:
                mermaid_lines.append(f'    {source_id} --- {target_id}')
        
        # Add styling
        mermaid_lines.extend([
            "",
            "    classDef bookNode fill:#e1f5fe,stroke:#01579b,stroke-width:2px",
            "    classDef authorNode fill:#f3e5f5,stroke:#4a148c,stroke-width:2px", 
            "    classDef genreNode fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px"
        ])
        
        diagram_text = "\n".join(mermaid_lines)
        
        # Save Mermaid diagram
        output_file = self.output_dir / f"concept_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mmd"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(diagram_text)
            
        self.logger.info(f"📝 Mermaid diagram saved: {output_file}")
        return diagram_text
        
    def create_comprehensive_analysis_report(self) -> str:
        """
        Create a comprehensive analysis report with multiple visualizations
        
        Returns:
            File path of generated report
        """
        self.logger.info("📊 Creating comprehensive analysis report...")
        
        # Extract network data
        nodes, edges = self.extract_bibliographic_network()
        
        if not nodes:
            self.logger.warning("No data available for analysis")
            return ""
        
        # Generate visualizations
        interactive_map = self.create_interactive_concept_map(nodes, edges)
        embedding_clusters = self.create_embedding_clusters_visualization()
        mermaid_diagram = self.generate_mermaid_diagram(nodes, edges)
        
        # Create summary report
        report_content = f"""# 📊 LibraryOfBabel Knowledge Analysis Report
*Generated by Dr. Elena Vásquez - Digital Archivist*

## 📋 Executive Summary

**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Entities**: {len(nodes)} nodes
**Relationships**: {len(edges)} edges

### Entity Distribution
"""
        
        # Count entities by category
        category_counts = {}
        for node in nodes:
            category_counts[node.category] = category_counts.get(node.category, 0) + 1
            
        for category, count in category_counts.items():
            report_content += f"- **{category.capitalize()}**: {count} entities\n"
            
        report_content += f"""
### Relationship Types
"""
        
        # Count relationships by type
        relationship_counts = {}
        for edge in edges:
            relationship_counts[edge.relationship] = relationship_counts.get(edge.relationship, 0) + 1
            
        for relationship, count in relationship_counts.items():
            report_content += f"- **{relationship.replace('_', ' ').title()}**: {count} connections\n"
            
        report_content += f"""
## 🎨 Generated Visualizations

1. **Interactive Concept Map**: [{os.path.basename(interactive_map) if interactive_map else 'Not generated'}]({interactive_map})
   - Web-based interactive visualization
   - Hover for detailed entity information
   - Zoomable and pannable interface

2. **Embedding Clusters Analysis**: [{os.path.basename(embedding_clusters) if embedding_clusters else 'Not generated'}]({embedding_clusters})
   - t-SNE visualization of semantic embeddings
   - Multi-modal embedding comparison
   - Content type clustering analysis

3. **Mermaid Diagram**: Available for integration into documentation systems

## 🔍 Key Insights

### Network Topology
- Most connected entities represent central concepts in the collection
- Genre clustering reveals thematic organization patterns
- Author networks show collaborative or stylistic relationships

### Embedding Analysis  
- Multi-modal embeddings reveal different semantic perspectives
- Content type classification enables targeted information retrieval
- Cluster analysis identifies similar content across different books

## 📈 Recommendations

1. **Enhanced Search**: Leverage network relationships for related content discovery
2. **Collection Development**: Identify gaps in genre or topic coverage
3. **User Experience**: Use clustering for personalized recommendations
4. **Archive Organization**: Apply network insights to digital collection structure

---

*Dr. Elena Vásquez - Digital Archivist & Knowledge Mapping Specialist*
*LibraryOfBabel Multi-Modal Analysis System*
"""
        
        # Save report
        report_file = self.output_dir / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        self.logger.info(f"📊 Comprehensive analysis report saved: {report_file}")
        return str(report_file)

def main():
    """Main function for command-line usage"""
    archivist = DigitalArchivistVasquez()
    
    print("📊 Dr. Elena Vásquez - Digital Archivist & Knowledge Mapping System")
    print("=" * 70)
    
    try:
        # Generate comprehensive analysis
        report_path = archivist.create_comprehensive_analysis_report()
        
        if report_path:
            print(f"✅ Analysis complete! Report generated: {report_path}")
            print(f"📁 Visualizations directory: {archivist.output_dir}")
        else:
            print("❌ Analysis failed - check logs for details")
            
    except Exception as e:
        archivist.logger.error(f"Fatal error in analysis: {e}")
        print(f"💥 Fatal error: {e}")

if __name__ == "__main__":
    main()