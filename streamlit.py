import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
import os

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

import app

load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CAL_API_KEY = os.getenv("CAL_API_KEY")


# --- Streamlit UI Setup ---
st.set_page_config(page_title="Cal.com Chatbot", layout="centered")

# --- Sidebar for API Keys Information ---
with st.sidebar:
    st.header("Configuration")
    
    if CAL_API_KEY:
        st.success("Cal.com API Key loaded from environment variables!")
        st.info(f"Cal.com API Key: `{CAL_API_KEY[:5]}...{CAL_API_KEY[-5:]}`")
    else:
        st.warning("Cal.com API Key not found in environment variables. Please set CAL_API_KEY in your .env file.")

    st.markdown("---")
    if OPENAI_API_KEY:
        st.success("OpenAI API Key loaded from environment variables!")
        st.info(f"OpenAI API Key: `{OPENAI_API_KEY[:5]}...{OPENAI_API_KEY[-5:]}`")
    else:
        st.error("OpenAI API Key not found in environment variables. Please set OPENAI_API_KEY in your .env file.")

# --- Chatbot Initialization and State Management ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        AIMessage(content="Hello! I am your Cal.com assistant. How can I help you manage your events?")
    ]

# Initialize the Langchain ChatOpenAI model
llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0, openai_api_key=OPENAI_API_KEY)

tools = [
    app.list_event_types,
    app.get_available_slots,
    app.book_cal_event,
    app.list_cal_events,
    app.cancel_cal_event,
    app.reschedule_cal_event,
    app.create_cal_event_type
]

current_date_str = datetime.now().strftime("%Y-%m-%d")

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f"You are a helpful Cal.com assistant. Current date is {current_date_str}. Use this for relative date references like 'today' or 'tomorrow'. "
            "You can list event types, check availability, book, list, cancel, and reschedule events. "
            "Always ask for all necessary details (like email for listing events, or event type, exact date, start time, end time, name, email, and event title for booking) before calling a tool. "
            "For dates and times, always ask the user to provide them in a clear format, like 'YYYY-MM-DD HH:MM:SS'. "
            "Convert user-provided dates and times to ISO 8601 format (e.g., 'YYYY-MM-DDTHH:MM:SSZ' for UTC or 'YYYY-MM-DDTHH:MM:SS-07:00' for specific offset) before passing to tools. "
            "Assume 'America/Los_Angeles' timezone for converting user input to ISO 8601, unless the user explicitly states another timezone. "
            "For booking, rescheduling, and canceling, explicitly ask for user confirmation before executing the action. "
            "When listing events, if the user doesn't provide an email, ask for it to filter results. "
            "When suggesting event types, use their 'title' and 'slug' from `list_event_types`. "
            "When asking for event ID for cancellation or rescheduling, clearly state that the ID can be found by listing events. "
            "The `book_cal_event` and `reschedule_cal_event` tools require `event_type_id`. You can get event types and their IDs using `list_event_types`. Always ensure you have the `event_type_id` before attempting to book or reschedule. "
            "If an API call returns an error, inform the user about the error details returned by the tool."
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

# --- Chat Display Area ---
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(message.content)

# --- User Input and Chat Interaction ---
if user_query := st.chat_input("Ask me anything about your Cal.com events..."):
    st.session_state.messages.append(HumanMessage(content=user_query))
    with st.chat_message("user"):
        st.markdown(user_query)

    # Check if Cal.com API key is provided before proceeding with agent invocation
    if not CAL_API_KEY:
        with st.chat_message("assistant"):
            st.warning("Please set your Cal.com API key in the .env file to proceed.")
        st.session_state.messages.append(AIMessage(content="Please set your Cal.com API key in the .env file to proceed."))
    else:
        with st.chat_message("assistant"):
            try:
                response = agent_executor.invoke(
                    {"chat_history": st.session_state.messages}
                )
                ai_response_content = response["output"]
                st.markdown(ai_response_content)
                st.session_state.messages.append(AIMessage(content=ai_response_content))
            except Exception as e:
                error_message = f"An error occurred while processing your request: {e}. Please try again or rephrase your request."
                st.error(error_message)
                st.session_state.messages.append(AIMessage(content=error_message))
