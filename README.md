# RAG System for Document Processing

This project implements a Retrieval-Augmented Generation (RAG) system for processing and querying documents. The system uses vector embeddings and ChromaDB for efficient document retrieval and processing.

## Project Overview

The system is designed to process documents, store them in a vector database, and enable semantic search capabilities. It uses modern NLP techniques for document processing and retrieval.

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Anaconda or Miniconda

### Environment Setup

1. Create a new Conda environment:
```bash
conda create -n rag-env python=3.8
conda activate rag-env
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Database Population

To initialize or reset the database and load the dataset for normalization of the RAG system, run:

```bash
python populate_database.py --reset
```

### Running the Application

To start the application and query the data:

```bash
python query_data.py
```

## Project Structure

- `populate_database.py`: Script for initializing and populating the database
- `query_data.py`: Main application for querying the processed documents
- `process_dilekce.py`: Document processing utilities
- `get_embedding_function.py`: Embedding generation functionality
- `data/`: Directory containing source documents
- `chroma/`: ChromaDB database files

## Dependencies

Key dependencies are listed in `requirements.txt`. The project uses:
- ChromaDB for vector storage
- Transformers for embedding generation
- Other NLP processing libraries

For any issues or questions, please refer to the project documentation or open an issue.
