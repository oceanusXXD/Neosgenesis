# Neogenesis LangChain Installation Guide

## System Requirements

- Python 3.8+
- Operating Systems: Windows, macOS, Linux

## Installation Steps

### 1. Basic Installation

```bash
pip install neogenesis-langchain
```

### 2. Development Installation

```bash
git clone https://github.com/neogenesis/neogenesis-langchain.git
cd neogenesis-langchain
pip install -e .
```

### 3. Optional Dependencies

```bash
# Redis storage support
pip install neogenesis-langchain[redis]

# Performance enhancements
pip install neogenesis-langchain[performance]

# Full features
pip install neogenesis-langchain[full]
```

## Verify Installation

```python
import neogenesis_langchain
print(f"Version: {neogenesis_langchain.__version__}")
```

## Common Issues

### Dependency Conflicts
If you encounter dependency conflicts, we recommend using a virtual environment:

```bash
python -m venv neogenesis_env
source neogenesis_env/bin/activate  # Linux/macOS
# or
neogenesis_env\Scripts\activate     # Windows
pip install neogenesis-langchain
```

### Import Errors
Ensure all required dependencies are installed:

```bash
pip install -r requirements.txt
```

## Additional Installation Options

### From Source

```bash
git clone https://github.com/neogenesis/neogenesis-langchain.git
cd neogenesis-langchain
pip install -r requirements.txt
pip install -e .
```

### With Specific Backends

```bash
# For Redis backend
pip install neogenesis-langchain[redis] redis

# For LMDB backend  
pip install neogenesis-langchain[lmdb] lmdb

# For MongoDB backend
pip install neogenesis-langchain[mongodb] pymongo
```

## Quick Start Test

After installation, test the package:

```python
import neogenesis_langchain

# Check available tools
tools = neogenesis_langchain.get_all_neogenesis_tools()
print(f"Available tools: {len(tools)}")

# Test basic functionality
from neogenesis_langchain import NeogenesisFiveStageDecisionTool
tool = NeogenesisFiveStageDecisionTool()
print("Package ready to use!")
```
