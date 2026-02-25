# AI Insight System

Automated AI Model and Paper Analysis System that tracks the latest developments in AI research and generates comprehensive analysis reports.

## Features

- **Automated Data Collection**: Daily collection from GitHub, HuggingFace, arXiv, and major AI providers
- **Technology Trend Analysis**: Identifies emerging patterns in AI research and model development
- **Model Architecture Analysis**: Generates detailed reports including architecture diagrams, parameter analysis, and computation estimates
- **Memory System**: Persists historical context for improved analysis accuracy
- **Multiple Interfaces**: CLI, REST API, and Gradio GUI

## Quick Start

```bash
# Clone the repository
git clone https://github.com/hongyu-zhou3434/ai-insight-system.git
cd ai-insight-system

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the full pipeline
ai-insight run
```

## Usage

### Command Line

```bash
ai-insight run          # Run full daily pipeline
ai-insight collect      # Data collection only
ai-insight analyze      # Analysis only
ai-insight report       # Generate reports
ai-insight serve        # Start API server
ai-insight scheduler    # Start scheduler daemon
ai-insight config       # Show configuration
```

### API Server

```bash
ai-insight serve
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### GUI

```bash
ai-insight-gui
# Interface available at http://localhost:7860
```

## Configuration

Edit `config/config.yaml` or use environment variables:

```yaml
# Example configuration
scheduler:
  enabled: true
  timezone: "Asia/Shanghai"
  collector_schedule: "0 6 * * *"
  
collector:
  github_repos:
    - "huggingface/transformers"
    - "openai/whisper"
  
analyzer:
  llm_provider: "anthropic"
  llm_model: "claude-sonnet-4-20250514"
```

## Output Reports

Reports are generated in `reports/` directory:

- **Insight Reports**: Technology trends, key techniques, model comparisons
- **Model Reports**: Architecture diagrams, parameter analysis, computation estimates

Reports support Markdown, HTML, JSON, and PPT formats.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

## License

MIT License