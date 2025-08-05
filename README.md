# ICLeaf-P1 - AI-Powered Learning Assistant

An intelligent chatbot system with role-based responses and dual-mode operation (internal/external data sources).

## Features

- **Role-based AI Assistant**: Different system prompts for Learners, Trainers, and Admins
- **Dual Mode Operation**:
  - **External Mode**: Web search, YouTube, GitHub integration using Google Gemini
  - **Internal Mode**: Private document retrieval using Pinecone (planned)
- **Modern Tech Stack**: LangChain, Google Gemini, Flask
- **YouTube Integration**: Official YouTube Data API v3 for reliable video search

## Project Structure

```
ICLeaf-P1/
├── config/
│   ├── prompts.py      # Role-based system prompts
│   └── settings.py     # Configuration and API keys
├── agents/
│   ├── base_agent.py   # Base agent class
│   ├── external_agent.py # External mode implementation
│   └── internal_agent.py # Internal mode (pseudocode)
├── retrievers/
│   ├── web_retriever.py    # Web, YouTube, GitHub search
│   └── pinecone_retriever.py # Internal document retrieval
├── utils/
│   └── state.py        # State management
├── tests/
│   └── test_external_agent.py # Test cases
├── main.py             # Flask application
└── requirements.txt    # Dependencies
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy `env_example.txt` to `.env` and fill in your API keys:

```bash
cp env_example.txt .env
```

Required API Keys:
- **Google Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **YouTube Data API v3 Key** (Optional): Get from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- **GitHub Token** (Optional): For GitHub search functionality

### 3. Environment Variables

```env
GEMINI_API_KEY=your_gemini_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here
GITHUB_TOKEN=your_github_token_here
```

### 4. YouTube API Setup (Optional)

To enable YouTube search functionality:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Create credentials (API Key)
5. Add the API key to your `.env` file

## Usage

### Running the Application

```bash
python main.py
```

The Flask server will start on `http://localhost:5000`

### API Endpoints

#### POST /chat

Send a chat request with role, mode, and query.

**Request Body:**
```json
{
    "role": "learner",
    "mode": "external",
    "query": "What is Python programming?"
}
```

**Response:**
```json
{
    "response": "Python is a high-level programming language..."
}
```

### Testing

Run the test suite:

```bash
python -m unittest tests/test_external_agent.py
```

Test YouTube API specifically:

```bash
python test_youtube_api.py
```

### Direct Agent Testing

You can also test the external agent directly:

```python
from utils.state import QueryState
from agents.external_agent import ExternalAgent

# Create a query state
state = QueryState(role="learner", mode="external", query="What is machine learning?")

# Initialize the external agent
agent = ExternalAgent(state)

# Get response
response = agent.get_response()
print(response)
```

## External Mode Features

The external agent provides:

1. **Web Search**: Using DuckDuckGo for general web content
2. **YouTube Search**: Official YouTube Data API v3 for reliable video search with detailed metadata
3. **GitHub Search**: Discover repositories and code examples
4. **Google Gemini Integration**: Advanced AI responses with context

### YouTube Search Features

- **Official API**: Uses YouTube Data API v3 for reliable results
- **Rich Metadata**: Includes title, channel, duration, views, and publication date
- **Error Handling**: Graceful fallback when API is unavailable
- **Rate Limiting**: Respects YouTube API quotas

## Role-Based Prompts

- **Learner**: Focused on educational content and explanations
- **Trainer**: Emphasizes teaching methodologies and advanced concepts
- **Admin**: Administrative and oversight capabilities

## Development

### Adding New Features

1. **New Retrievers**: Extend the base retriever class
2. **New Roles**: Add prompts to `config/prompts.py`
3. **New Modes**: Create new agent classes

### Error Handling

The system includes comprehensive error handling for:
- API failures
- Network issues
- Invalid queries
- Missing API keys
- YouTube API quota limits

## Future Enhancements

- [ ] Internal mode with Pinecone integration
- [ ] Document upload and processing
- [ ] Conversation history
- [ ] User authentication
- [ ] Advanced analytics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License.