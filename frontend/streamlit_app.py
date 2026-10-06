import os

import requests
import streamlit as st


ASSISTANT_API_URL = os.getenv(
    "ASSISTANT_API_URL",
    "http://127.0.0.1:8000/assistant",
)
EXAMPLE_PROMPTS = [
    "What is the status of customer 101?",
    "Tell me the details of order 112.",
    "What is the company's return policy?",
    "Name all the company policies in the internal knowledge base.",
    (
        "What is the status of order 112, what product is it for, "
        "and can the product be returned under company policy?"
    ),
]


class AssistantAPIError(Exception):
    """An expected communication or response error from the FastAPI service."""


def ask_assistant(message: str) -> str:
    try:
        response = requests.post(
            ASSISTANT_API_URL,
            json={"message": message},
            timeout=(5, 120),
        )
    except requests.Timeout as exc:
        raise AssistantAPIError(
            "The assistant service took too long to respond. Please try again."
        ) from exc
    except requests.ConnectionError as exc:
        raise AssistantAPIError(
            "The FastAPI backend is unavailable. Start the backend and try again."
        ) from exc
    except requests.RequestException as exc:
        raise AssistantAPIError(
            "Could not communicate with the assistant service. Please try again."
        ) from exc

    if not response.ok:
        raise AssistantAPIError(
            f"The FastAPI backend returned HTTP {response.status_code}. "
            "Please try again."
        )

    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError as exc:
        raise AssistantAPIError(
            "The FastAPI backend returned an unreadable response."
        ) from exc

    answer = payload.get("answer") if isinstance(payload, dict) else None
    if not isinstance(answer, str) or not answer.strip():
        raise AssistantAPIError(
            "The FastAPI backend response did not include an answer."
        )
    return answer


def queue_example(prompt: str) -> None:
    st.session_state["pending_prompt"] = prompt


st.set_page_config(
    page_title="AI Business Operations Assistant",
    page_icon=":material/support_agent:",
    layout="centered",
)

st.markdown(
    """
    <style>
    div.block-container {
        max-width: 920px;
        padding-top: 2.2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #f3f6fa !important;
        letter-spacing: -0.025em;
    }
    section[data-testid="stSidebar"] {
        border-right: 1px solid #28364a;
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #d2dbe6 !important;
    }
    div[data-testid="stChatMessage"] {
        color: #f3f6fa !important;
        border: 1px solid #354256;
        border-radius: 10px;
        background: #1b2636;
        padding: 0.8rem 1rem;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.16);
    }
    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] * {
        color: #f3f6fa !important;
    }
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: #24364b;
        border-color: #3b5875;
    }
    div[data-testid="stChatInput"] {
        background: #182231;
        border: 1px solid #43536a;
        border-radius: 10px;
    }
    div[data-testid="stChatInput"] textarea,
    div[data-testid="stChatInput"] [contenteditable="true"] {
        color: #f3f6fa !important;
        caret-color: #60a5fa;
    }
    div[data-testid="stChatInput"] textarea::placeholder,
    div[data-testid="stChatInput"] [contenteditable="true"]::placeholder {
        color: #aab7c7 !important;
        opacity: 1;
    }
    .app-subtitle {
        color: #b1bdcb !important;
        font-size: 1.02rem;
        margin-top: -0.45rem;
        margin-bottom: 1.6rem;
    }
    section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {
        color: #e4ebf3 !important;
        border: 1px solid #3a4a60;
        background: #1c293a;
        text-align: left;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        color: #ffffff !important;
        border-color: #5b8fbd;
        background: #263950;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        color: #ffffff !important;
        border-color: #367fc1;
        background: #2468a8;
        text-align: center;
    }
    .sidebar-caption {
        color: #aab8c8 !important;
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 1.25rem 0 0.35rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "pending_prompt" not in st.session_state:
    st.session_state["pending_prompt"] = None

with st.sidebar:
    st.markdown("## :material/space_dashboard: AI Operations")
    st.markdown(
        "An internal assistant for customer, order, product, and company "
        "knowledge questions."
    )
    if st.button(
        "New conversation",
        icon=":material/add:",
        type="primary",
        width="stretch",
    ):
        st.session_state["messages"] = []
        st.session_state["pending_prompt"] = None
        st.rerun()

    st.markdown(
        '<div class="sidebar-caption">Capabilities</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "- Customer status and records\n"
        "- Order and product details\n"
        "- Internal knowledge and company policies"
    )

    st.markdown(
        '<div class="sidebar-caption">Try asking</div>',
        unsafe_allow_html=True,
    )
    for index, example in enumerate(EXAMPLE_PROMPTS):
        st.button(
            example,
            key=f"example_{index}",
            width="stretch",
            on_click=queue_example,
            args=(example,),
        )

st.title(
    "AI Business Operations Assistant",
    icon=":material/support_agent:",
)
st.markdown(
    '<p class="app-subtitle">Get reliable answers to business questions using '
    'company data and internal knowledge.</p>',
    unsafe_allow_html=True,
)

if not st.session_state["messages"]:
    with st.container(border=True):
        st.markdown("### How can I help with your operations?")
        st.markdown(
            "Ask about a customer, order, or product—or look up an internal "
            "policy. The assistant will use the connected company systems to "
            "prepare a response."
        )

for entry in st.session_state["messages"]:
    with st.chat_message(entry["role"]):
        st.markdown(entry["content"])

prompt = st.session_state.pop("pending_prompt", None)
if prompt is None:
    prompt = st.chat_input("Ask a question about your business operations...")

if prompt:
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Checking company information..."):
            try:
                answer = ask_assistant(prompt)
            except AssistantAPIError as error:
                answer = str(error)
                st.warning(answer, icon=":material/warning:")
            else:
                st.markdown(answer)
    st.session_state["messages"].append(
        {"role": "assistant", "content": answer}
    )
