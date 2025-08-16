-- Create embedding tables in knowledge_with_embeds with exact schema match

-- chunk_embeddings table
CREATE TABLE chunk_embeddings (
    embedding_id integer NOT NULL,
    chunk_id character varying(255) NOT NULL,
    book_id integer NOT NULL,
    embedding jsonb NOT NULL,
    embedding_model character varying(100) NOT NULL,
    embedding_dimension integer NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    content_type character varying(50),
    routing_reason text,
    confidence_score numeric(3,2),
    embedding_vector vector(768),
    embedding_vector_bge vector(1024),
    embedding_vector_granite vector(384),
    embedding_vector_mxbai vector(1024)
);

CREATE SEQUENCE chunk_embeddings_embedding_id_seq AS integer START WITH 1 INCREMENT BY 1;
ALTER SEQUENCE chunk_embeddings_embedding_id_seq OWNED BY chunk_embeddings.embedding_id;
ALTER TABLE ONLY chunk_embeddings ALTER COLUMN embedding_id SET DEFAULT nextval('chunk_embeddings_embedding_id_seq'::regclass);

-- Specialized embedding tables
CREATE TABLE semantic_embeddings (
    chunk_id character varying(255) NOT NULL,
    book_id integer,
    chunk_level character varying(20),
    embedding vector(1536),
    confidence_score double precision DEFAULT 1.0,
    processing_timestamp timestamp without time zone DEFAULT now()
);

CREATE TABLE stylistic_embeddings (
    chunk_id character varying(255) NOT NULL,
    book_id integer,
    chunk_level character varying(20),
    embedding vector(1536),
    confidence_score double precision DEFAULT 1.0,
    processing_timestamp timestamp without time zone DEFAULT now()
);

CREATE TABLE topical_embeddings (
    chunk_id character varying(255) NOT NULL,
    book_id integer,
    chunk_level character varying(20),
    embedding vector(1536),
    confidence_score double precision DEFAULT 1.0,
    processing_timestamp timestamp without time zone DEFAULT now()
);

CREATE TABLE temporal_embeddings (
    chunk_id character varying(255) NOT NULL,
    book_id integer,
    chunk_level character varying(20),
    embedding vector(1536),
    confidence_score double precision DEFAULT 1.0,
    processing_timestamp timestamp without time zone DEFAULT now()
);

CREATE TABLE factual_embeddings (
    chunk_id character varying(255) NOT NULL,
    book_id integer,
    chunk_level character varying(20),
    embedding vector(1536),
    confidence_score double precision DEFAULT 1.0,
    processing_timestamp timestamp without time zone DEFAULT now()
);

-- Primary keys and constraints
ALTER TABLE ONLY chunk_embeddings ADD CONSTRAINT chunk_embeddings_pkey PRIMARY KEY (embedding_id);
ALTER TABLE ONLY chunk_embeddings ADD CONSTRAINT chunk_embeddings_unique_chunk_model UNIQUE (chunk_id, embedding_model);
ALTER TABLE ONLY semantic_embeddings ADD CONSTRAINT semantic_embeddings_pkey PRIMARY KEY (chunk_id);
ALTER TABLE ONLY stylistic_embeddings ADD CONSTRAINT stylistic_embeddings_pkey PRIMARY KEY (chunk_id);
ALTER TABLE ONLY topical_embeddings ADD CONSTRAINT topical_embeddings_pkey PRIMARY KEY (chunk_id);
ALTER TABLE ONLY temporal_embeddings ADD CONSTRAINT temporal_embeddings_pkey PRIMARY KEY (chunk_id);
ALTER TABLE ONLY factual_embeddings ADD CONSTRAINT factual_embeddings_pkey PRIMARY KEY (chunk_id);

-- Essential indexes for performance
CREATE INDEX idx_chunk_embeddings_book_id ON chunk_embeddings USING btree (book_id);
CREATE INDEX idx_chunk_embeddings_model ON chunk_embeddings USING btree (embedding_model);
CREATE INDEX idx_semantic_embeddings_book_id ON semantic_embeddings USING btree (book_id);
CREATE INDEX idx_stylistic_embeddings_book_id ON stylistic_embeddings USING btree (book_id);
CREATE INDEX idx_topical_embeddings_book_id ON topical_embeddings USING btree (book_id);
CREATE INDEX idx_temporal_embeddings_book_id ON temporal_embeddings USING btree (book_id);
CREATE INDEX idx_factual_embeddings_book_id ON factual_embeddings USING btree (book_id);