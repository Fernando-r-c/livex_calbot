# Cal.com Chatbot (Streamlit + LangChain)

A conversational assistant for managing your [Cal.com](https://cal.com) events, built with Streamlit and LangChain. This app allows you to list event types, check availability, book, list, cancel, reschedule, and create event types on your Cal.com account—all through a natural language chat interface powered by OpenAI.

## Features

- **Conversational UI**: Interact with your Cal.com account using natural language.
- **Event Management**: List, book, cancel, and reschedule events.
- **Event Type Management**: List and create new event types.
- **Availability Checking**: Find available slots for any event type.
- **Customizable**: Theming and sidebar navigation via Streamlit.

## Demo

see included png files

---

## Getting Started

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd livex_fs_calbot
```

### 2. Install Dependencies

It's recommended to use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root with the following:

```
OPENAI_API_KEY=sk-...
CAL_API_KEY=ck-...
```

- Get your OpenAI API key from [OpenAI](https://platform.openai.com/account/api-keys)
- Get your Cal.com API key from your Cal.com dashboard

### 4. Run the App

```bash
streamlit run streamlit.py
```

The app will open in your browser. Use the sidebar to verify your API keys are loaded.

---

## Usage

- **Ask questions** like:
  - "List my event types"
  - "Book a 30-minute meeting for tomorrow at 10am with John Doe, john@example.com"
  - "Show my events for jane@example.com"
  - "Cancel event with ID 12345"
  - "Reschedule event 12345 to next Monday at 2pm"
  - "Create a new event type called 'Demo Call' for 15 minutes"

- The assistant will guide you to provide all required details and confirm actions before making changes.

---

## Project Structure

```
.
├── app.py                # Cal.com API integration and LangChain tools
├── streamlit.py          # Streamlit UI and chat logic
├── requirements.txt      # Python dependencies
├── .env                  # (not committed) Your API keys
└── .streamlit/
    └── config.toml       # Streamlit theming and sidebar config
```

---

## Configuration

- **Theming**: The app uses a custom theme (see `.streamlit/config.toml`).
- **Sidebar**: Shows API key status and configuration info.

---

## Dependencies

- [Streamlit](https://streamlit.io/)
- [LangChain](https://python.langchain.com/)
- [OpenAI](https://platform.openai.com/)
- [Cal.com API](https://docs.cal.com/api)
- `python-dotenv`, `requests`, `pytz`, `python-dateutil`

See `requirements.txt` for exact versions.

---

## Notes

- All date/times are assumed to be in the `America/Los_Angeles` timezone unless specified.
- The app will prompt for missing information and confirmations before making bookings or cancellations.
- Errors from the Cal.com API are shown in the chat.

---

## License

[MIT](LICENSE)

---

## Acknowledgements

- [Cal.com](https://cal.com)
- [OpenAI](https://openai.com)
- [Streamlit](https://streamlit.io)
- [LangChain](https://langchain.com)