import streamlit as st
from google import genai
from google.genai import types   # <- need this import for GenerateContentConfig
import io
import re
import os

key = None
if "GEMINI_KEY" in st.secrets:
    key = st.secrets['GEMINI_KEY']
else:
    os.getenv("GEMINI_KEY")

client = genai.Client(api_key=key)

# Page configuration
st.set_page_config(
    page_title="File Processor",
    layout="centered",
)

# Title
st.title("📁 File Processing Interface")

# Description
st.markdown(
    """
    Upload your file, choose your source and target programming languages,
    and click the button below to process the file.
    """
)

# File uploader
uploaded_file = st.file_uploader("Choose a file", type=["txt", "csv", "py", "java", "json"])

# Dropdown for programming languages
languages = ["Python", "Java", "JavaScript", "C++", "Ruby", "Go", "C#", "TypeScript"]
FILE_META = {
    "Python":      {"ext": ".py",   "mime": "text/x-python"},
    "Java":        {"ext": ".java", "mime": "text/x-java-source"},
    "JavaScript":  {"ext": ".js",   "mime": "application/javascript"},
    "C++":         {"ext": ".cpp",  "mime": "text/x-c++src"},
    "Ruby":        {"ext": ".rb",   "mime": "text/x-ruby"},
    "Go":          {"ext": ".go",   "mime": "text/x-go"},
    "C#":          {"ext": ".cs",   "mime": "text/x-csharp"},
    "TypeScript":  {"ext": ".ts",   "mime": "application/typescript"},
}

col1, col2 = st.columns(2)
with col1:
    source_language = st.selectbox("Source Language", languages)

with col2:
    target_language = st.selectbox("Target Language", languages, index=1)

default_model = 'gemini-2.0-flash'
chosen_model = st.text_input(
    label="Gemini Model Type: ",
    value=f"{default_model}",          # default text
    placeholder=f"{default_model}",
)

default_input_prompt = f"I am a software engineer. The code in the file above is written in {source_language}. Convert the same code to the new target language: {target_language}. Keep the same code functionality and do not add additional commentary outside the new code file."
full_prompt = st.text_area(
    label="Prompt",
    value=f"{default_input_prompt}",          # default text
    placeholder=f"{default_input_prompt}",
    height=120
)
max_number_tokens = st.number_input(
    label="Max Number Tokens: Choose a number (1–8,192)",
    min_value=1,
    max_value=8_192,
    value=8_192,             # default number
    step=1000,
    format="%d",
)

# Processing button
if st.button("Process File"):
    if uploaded_file is not None:
        with st.spinner('Processing file...'):
            # Upload file to Gemini to get a file object
            file_content = uploaded_file.read()

            # Correct usage of Gemini file object
            result = client.models.generate_content(
                model=chosen_model,
                contents=[
                    file_content,
                    "\n\n",
                    full_prompt,
                ],
                config=types.GenerateContentConfig(
                    max_output_tokens=max_number_tokens
                ),
            )
            
            pattern = re.compile(
                r"(?s)^```.*?\n(.*?)^```$",  # opening fence, capture everything, closing fence
                re.MULTILINE,
            )
            match = pattern.search(result.text.strip())
            st.success("File processed successfully!")
            if not match:
                # there is no fencing in the output
                st.download_button(
                    label=f"Download File in {target_language}",
                    data=result.text,
                    file_name=f"{uploaded_file.name.split(".")[0]}{FILE_META[target_language]['ext']}",
                    mime=FILE_META[target_language]['mime']
                )

            else:
                # there is fencing in the output (markdown)
                code_without_markdown = match.group(1).rstrip() + "\n"
                st.download_button(
                    label=f"Download File in {target_language}",
                    data=code_without_markdown,
                    file_name=f"{uploaded_file.name.split(".")[0]}{FILE_META[target_language]['ext']}",
                    mime=FILE_META[target_language]['mime']
                )
            
            st.write("### Input Prompt to LLM")
            st.write(full_prompt)
            st.write("### Output From LLM")
            st.write(result.text)
    else:
        st.error("Please upload a file to proceed.")