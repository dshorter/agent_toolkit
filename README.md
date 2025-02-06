# AI Agent System

A flexible AI agent architecture supporting tool integration, sequence tracking, and business intelligence analysis. 

## Quick Start
# Setup environment
python setup.py

# Activate virtual environment
source venv/bin/activate  # Unix
.\venv\Scripts\activate   # Windows

# Configure environment
```
cp .env.example .env
# Edit .env with your settings
```

## Core Features

- Tool-agnostic agent architecture
- Decision chain tracking
- Power BI integration
- Structured logging
- Performance monitoring

## Architecture Overview  

```mermaid
graph TD
    CA[Client Apps] --> API[API Gateway]
    API --> AS[Agent Service]
    AS --> TM[Task Manager]
    AS --> AM[Agent Memory]
    AS --> TS[Tool Service]

    %% Style classes 
    classDef client fill:#E6B9B8,stroke:#000000,stroke-width:2px;
    classDef service fill:#B3CDE3,stroke:#000000,stroke-width:2px;
    classDef storage fill:#BFD8BE,stroke:#000000,stroke-width:2px;
    classDef text color:#000000;
    
    %% Apply styles
    class CA client,text;
    class API,AS,TM,TS service,text;
    class AM storage,text;

    %% Link styling
    linkStyle default stroke:#000000,stroke-width:2px;
```

## Development

- Python 3.10+
- FastAPI
- MongoDB
- Redis
- See requirements.txt for full list

## Documentation

See our [Wiki](wiki-link) for:
- Architecture details
- Development guides
- Configuration
- Monitoring setup

## License

[License Type]
