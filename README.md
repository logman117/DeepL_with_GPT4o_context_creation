# DeepL_with_GPT4o_context_creation

![DeepL and GPT-4o Integration](https://via.placeholder.com/800x400?text=DeepL+and+GPT-4o+Integration)

## 📝 Overview

This project enhances machine translation quality for UI text by combining DeepL's translation capabilities with GPT-4o-generated contextual information. It's specifically designed for translating UI files for touchscreen interfaces on cleaning machines while maintaining high translation quality and contextual accuracy across multiple languages.

## ✨ Key Features

- **Contextual Translation**: Generates rich contextual information for each UI string using Azure OpenAI's GPT-4o
- **Intelligent Description Generation**: Automatically fills in missing description fields for UI elements
- **Multi-Language Support**: Translates to all languages supported by DeepL
- **Formality Control**: Utilizes DeepL's formality settings for appropriate tone
- **JSON Structure Preservation**: Maintains the original JSON structure while translating content
- **Efficient Caching**: Implements context and description caching to avoid redundant API calls
- **Comprehensive Error Handling**: Gracefully handles API failures without interrupting the batch process

## 🔧 How It Works

The translation process works in two phases:

### Phase 1: Preprocessing and Context Generation
1. Loads and parses JSON UI files
2. Fills in any missing descriptions using GPT-4o
3. Generates contextual information for each translatable string
4. Caches all contexts to reduce API calls

### Phase 2: Translation
1. Retrieves supported target languages from DeepL
2. For each target language:
   - Creates a language-specific output folder
   - Translates each JSON file using the pre-generated contexts
   - Preserves the original JSON structure
   - Writes translated files to the language folder

## 📄 UI File Types

The system is designed to handle the following UI file types:

| File Name | Description |
|-----------|-------------|
| `component.json` | UI component labels such as buttons and input placeholders |
| `dynamic.json` | Dynamic configuration texts and settings descriptions |
| `language.json` | Language names used for UI language selection |
| `notification.json` | Notification messages, error alerts, and status updates |
| `screen.json` | Screen titles, instructions, and button labels |
| `unit.json` | Measurement units and dynamic templates |

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- DeepL API key
- Azure OpenAI API key and endpoint

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DeepL_with_GPT4o_context_creation.git
cd DeepL_with_GPT4o_context_creation
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up environment variables for API keys:
```bash
# On Windows
set DEEPL_API_KEY=your_deepl_api_key
set AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
set AZURE_OPENAI_API_KEY=your_azure_openai_api_key

# On Linux/Mac
export DEEPL_API_KEY=your_deepl_api_key
export AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
export AZURE_OPENAI_API_KEY=your_azure_openai_api_key
```

Alternatively, update the key values directly in the script.

### Usage

1. Place your JSON UI files in the same directory as the script.

2. Run the script:
```bash
python main.py
```

3. The script will:
   - Verify API connections
   - Process all JSON files
   - Generate folders for each target language
   - Create translated versions of all JSON files

## ⚙️ Configuration Options

The script includes several configurable parameters:

```python
# DeepL configuration
DEFAULT_FORMALITY = Formality.MORE  # Options: Formality.DEFAULT, Formality.MORE, Formality.LESS
DEFAULT_MODEL_TYPE = ModelType.PREFER_QUALITY_OPTIMIZED  # Alternative: ModelType.PREFER_PERFORMANCE_OPTIMIZED
PRESERVE_FORMATTING = True

# Azure OpenAI configuration
AZURE_API_VERSION = "2024-08-01-preview"
AZURE_MODEL_NAME = "gpt-4o"
```

## 🤝 Contributing

Contributions are welcome! Here are some ways you can contribute:

1. Report bugs
2. Suggest new features
3. Submit pull requests
4. Improve documentation

## 📊 Performance Considerations

- **API Rate Limits**: The script includes timeout handling to manage DeepL and Azure OpenAI rate limits
- **Caching**: Context and description generation results are cached to minimize API calls
- **Error Handling**: Failed translations will return the original string to prevent process interruption

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [DeepL API](https://www.deepl.com/docs-api) for high-quality machine translation
- [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service/) for GPT-4o integration
- All contributors and testers
