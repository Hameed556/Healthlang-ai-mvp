# Data

This directory contains data files and resources for HealthLang AI MVP.

## Contents

### Medical Knowledge Base
- **raw/** - Raw medical documents and sources
- **processed/** - Processed and cleaned medical data
- **embeddings/** - Vector embeddings for RAG system
- **models/** - Trained ML models and checkpoints

### Translation Data
- **translation/** - Translation datasets and models
- **yoruba/** - Yoruba language resources
- **parallel-corpus/** - Parallel text corpora

### User Data
- **users/** - User profiles and preferences
- **queries/** - Medical query history
- **translations/** - Translation history
- **analytics/** - Usage analytics and metrics

### Configuration Data
- **config/** - Application configuration files
- **secrets/** - Encrypted secrets and keys
- **backups/** - Database and data backups

## Data Sources

### Medical Sources
- WHO Guidelines
- CDC Recommendations
- PubMed Articles
- Medical Textbooks
- Clinical Guidelines

### Translation Sources
- Yoruba-English Parallel Texts
- Medical Terminology Dictionaries
- Community-Contributed Translations
- Professional Medical Translations

## Data Management

```bash
# Download medical knowledge base
make download-medical-data

# Process raw documents
make process-documents

# Generate embeddings
make generate-embeddings

# Backup data
make backup-data
```

## Privacy & Security

- All user data is encrypted at rest
- Medical data follows HIPAA guidelines
- Translation data respects privacy
- Regular data backups and recovery testing 