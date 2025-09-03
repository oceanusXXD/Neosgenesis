# Neogenesis LangChain Integration

> A standardized Python package for Neogenesis System, designed specifically for the LangChain ecosystem

## Introduction

Neogenesis LangChain integrates the core components of Neogenesis System into the LangChain ecosystem, providing advanced decision-making, state management, and multi-armed bandit optimization capabilities.

## Core Features

- 🧠 **Five-Stage Decision Process**: Complete intelligent decision pipeline
- 🏗️ **Modular Architecture**: Five major modules - storage, state, chains, execution, and optimization
- 🔗 **LangChain Integration**: Fully compatible with LangChain tools and chain systems
- 💾 **Enterprise Storage**: Support for multiple storage backends
- 🌐 **Distributed State**: Cross-node state synchronization support
- 🎯 **Intelligent Optimization**: Dynamic optimization based on multi-armed bandits

## Quick Start

```bash
pip install neogenesis-langchain
```

```python
from neogenesis_langchain import NeogenesisFiveStageDecisionTool

tool = NeogenesisFiveStageDecisionTool()
result = tool.run("How to improve team collaboration efficiency?")
```

## Package Structure

```
neogenesis_langchain/
├── tools.py             # Core tools
├── adapters.py          # LangChain adapters
├── storage/             # Storage system
├── state/               # State management
├── chains/              # Decision chains
├── execution/           # Execution system
├── optimization/        # Optimization system
└── examples/            # Example code
```

## Installation

### Basic Installation

```bash
pip install neogenesis-langchain
```

### Development Installation

```bash
git clone https://github.com/neogenesis/neogenesis-langchain.git
cd neogenesis-langchain
pip install -e .
```

### Optional Dependencies

```bash
# Redis storage support
pip install neogenesis-langchain[redis]

# Performance enhancements
pip install neogenesis-langchain[performance]

# Full features
pip install neogenesis-langchain[full]
```

## Usage Examples

### Basic Tool Usage

```python
from neogenesis_langchain import (
    NeogenesisThinkingSeedTool,
    NeogenesisRAGSeedTool,
    get_all_neogenesis_tools
)

# Get all available tools
tools = get_all_neogenesis_tools()
print(f"Available tools: {len(tools)}")

# Use thinking seed tool
thinking_tool = NeogenesisThinkingSeedTool()
result = thinking_tool.run("Analyze market trends for AI startups")
```

### State Management

```python
from neogenesis_langchain import NeogenesisStateManager

# Initialize state manager
state_manager = NeogenesisStateManager()

# Create and manage decision stages
stage = state_manager.create_decision_stage(
    stage_name="analysis",
    context="Market research analysis"
)
```

### Advanced Chains

```python
from neogenesis_langchain.chains import NeogenesisDecisionChain

# Create decision chain
chain = NeogenesisDecisionChain()

# Execute decision process
result = chain.run({
    "query": "Should we invest in this technology?",
    "context": "Startup evaluation"
})
```

## API Reference

### Core Tools

- `NeogenesisThinkingSeedTool`: Advanced thinking and reasoning tool
- `NeogenesisRAGSeedTool`: RAG-based information retrieval tool
- `NeogenesisFiveStageDecisionTool`: Complete five-stage decision process

### State Management

- `NeogenesisStateManager`: Core state management functionality
- `DecisionStage`: Individual decision stage representation
- `DistributedStateManager`: Distributed state synchronization

### Storage

- `PersistentStorageEngine`: Persistent storage backend
- `StorageBackend`: Abstract storage interface

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Documentation

- [Installation Guide](install_guide.md)
- [API Documentation](https://neogenesis-langchain.readthedocs.io/)
- [Examples](examples/)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- 📧 Email: neogenesis@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/neogenesis/neogenesis-langchain/issues)
- 📖 Documentation: [Read the Docs](https://neogenesis-langchain.readthedocs.io/)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.
