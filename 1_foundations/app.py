from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pathlib import Path
from pypdf import PdfReader
import gradio as gr


load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]


class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Harsha Melur Nagesh"
        _resume_pdf = Path("me/Harsha_Resume.pdf")
        if not _resume_pdf.is_file():
            _resume_pdf = Path("1_foundations/me/Harsha_Resume.pdf")
        if not _resume_pdf.is_file():
            raise FileNotFoundError(
                f"Resume PDF not found. Tried me/Harsha_Resume.pdf and 1_foundations/me/Harsha_Resume.pdf (cwd={Path.cwd()})."
            )
        reader = PdfReader(str(_resume_pdf))
        self.resume_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.resume_text += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()


    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and resume which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## Resume:\n{self.resume_text}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        clean_history = []
        for entry in history or []:
            role = entry.get("role")
            content = entry.get("content")
            if role in ("user", "assistant") and content:
                clean_history.append({"role": role, "content": content})
        messages = (
            [{"role": "system", "content": self.system_prompt()}]
            + clean_history
            + [{"role": "user", "content": message}]
        )
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason == "tool_calls":
                assistant_message = response.choices[0].message
                tool_calls = assistant_message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(assistant_message.model_dump(exclude_none=True))
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content


def _black_blue_theme() -> gr.Theme:
    black = "#000000"
    surface = "#0f0f0f"
    surface_2 = "#1a1a1a"
    blue = "#2563eb"
    blue_light = "#3b82f6"
    blue_dark = "#1e3a8a"
    text = "#f9fafb"
    text_blue = "#60a5fa"

    return gr.themes.Base(primary_hue="blue", neutral_hue="neutral").set(
        body_background_fill=black,
        body_background_fill_dark=black,
        background_fill_primary=surface,
        background_fill_primary_dark=surface,
        background_fill_secondary=surface_2,
        background_fill_secondary_dark=surface_2,
        panel_background_fill=surface,
        panel_background_fill_dark=surface,
        block_background_fill=surface,
        block_background_fill_dark=surface,
        block_border_color=blue,
        block_border_color_dark=blue,
        border_color_primary=blue_dark,
        border_color_primary_dark=blue_dark,
        border_color_accent=blue_light,
        border_color_accent_dark=blue_light,
        color_accent=blue_light,
        color_accent_soft=blue_dark,
        color_accent_soft_dark=blue_dark,
        body_text_color=text,
        body_text_color_dark=text,
        body_text_color_subdued=text_blue,
        body_text_color_subdued_dark=text_blue,
        block_title_text_color=text,
        block_title_text_color_dark=text,
        block_label_text_color=text_blue,
        block_label_text_color_dark=text_blue,
        input_background_fill=surface,
        input_background_fill_dark=surface,
        input_border_color=blue,
        input_border_color_dark=blue,
        input_placeholder_color="#6b7280",
        input_placeholder_color_dark="#6b7280",
        button_primary_background_fill=blue,
        button_primary_background_fill_dark=blue,
        button_primary_background_fill_hover=blue_light,
        button_primary_background_fill_hover_dark=blue_light,
        button_primary_text_color=text,
        button_primary_text_color_dark=text,
        button_secondary_background_fill=surface_2,
        button_secondary_background_fill_dark=surface_2,
        button_secondary_text_color=text_blue,
        button_secondary_text_color_dark=text_blue,
        link_text_color=blue_light,
        link_text_color_dark=blue_light,
        checkbox_background_color=surface_2,
        checkbox_background_color_dark=surface_2,
        checkbox_border_color=blue,
        checkbox_border_color_dark=blue,
        table_border_color=blue_dark,
        table_border_color_dark=blue_dark,
        table_even_background_fill=surface,
        table_even_background_fill_dark=surface,
        table_odd_background_fill=surface_2,
        table_odd_background_fill_dark=surface_2,
    )


def build_ui(me: Me) -> gr.ChatInterface:
    welcome = (
        f"Hello — I'm **{me.name}**'s career assistant. "
        "Ask about background, engineering experience, AI work, or how to connect."
    )

    css = """
    :root, .dark {
        --body-background-fill: #000000 !important;
        --background-fill-primary: #0f0f0f !important;
        --background-fill-secondary: #1a1a1a !important;
        --block-background-fill: #0f0f0f !important;
        --input-background-fill: #0f0f0f !important;
        --border-color-primary: #1e3a8a !important;
        --border-color-accent: #2563eb !important;
        --color-accent: #3b82f6 !important;
        --body-text-color: #f9fafb !important;
        --button-primary-background-fill: #2563eb !important;
    }
    html, body, .gradio-container, .main, .wrap, .contain, footer {
        background: #000000 !important;
        background-color: #000000 !important;
    }
    .block, .form, .panel {
        background: #0f0f0f !important;
        border-color: #2563eb !important;
    }
    .prose h1, [data-testid="block-info"] h1, .gr-markdown h1 {
        color: #ffffff !important;
        text-align: center;
    }
    .prose h2, .prose p, [data-testid="block-info"] p, .gr-markdown p {
        color: #3b82f6 !important;
        text-align: center;
    }
    .block:has(.chatbot), .block:has(#chatbot), .block:has([data-testid="chatbot"]) {
        background: #ffffff !important;
        border-color: #2563eb !important;
    }
    .chatbot, #chatbot, [data-testid="chatbot"],
    .chatbot > div, .chatbot .wrap, .chatbot .component-wrap {
        background: #ffffff !important;
        background-color: #ffffff !important;
        border: 2px solid #2563eb !important;
        border-radius: 12px;
    }
    .message.bot, .bot, .bubble-wrap.bot, div[data-testid="bot"] {
        background: #f3f4f6 !important;
        border: 1px solid #e5e7eb !important;
        color: #111827 !important;
    }
    .message.user, .user, .bubble-wrap.user, div[data-testid="user"] {
        background: #dbeafe !important;
        border: 1px solid #93c5fd !important;
        color: #1e3a8a !important;
    }
    .chatbot p, .chatbot span, .chatbot li, .chatbot .md, .chatbot .prose,
    .message.bot p, .message.bot span, .message.bot .md, .message.bot .prose, .bot .md {
        color: #1e40af !important;
        background: transparent !important;
    }
    .chatbot strong, .chatbot b, .chatbot .md strong,
    .message.bot strong, .message.bot b, .message.bot .md strong, .bot strong {
        color: #111827 !important;
        font-weight: 700 !important;
    }
    .message.user .md, .message.user .prose, .user .md {
        color: inherit !important;
        background: transparent !important;
    }
    .block:has(textarea) textarea,
    textarea, input[type="text"], .input-container {
        background: #ffffff !important;
        color: #111827 !important;
        border: 1px solid #d1d5db !important;
    }
    button.primary, .primary {
        background: #2563eb !important;
        border-color: #3b82f6 !important;
        color: #ffffff !important;
    }
    footer {
        background: #000000 !important;
        color: #60a5fa !important;
    }
    """

    return gr.ChatInterface(
        me.chat,
        type="messages",
        title=me.name,
        description="Career Assistant",
        theme=_black_blue_theme(),
        css=css,
        chatbot=gr.Chatbot(
            value=[{"role": "assistant", "content": welcome}],
            type="messages",
            height=480,
            show_label=False,
        ),
    )


if __name__ == "__main__":
    me = Me()
    build_ui(me).launch()
    