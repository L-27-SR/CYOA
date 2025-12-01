import os
from dotenv import load_dotenv
load_dotenv()

try:
    from google import genai
except ImportError:
    raise ImportError("google-genai package not found. Please run: pip install -U google-genai")

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found. Please check your .env file.")

# Preferred model list (tries flash first, then pro)
PREFERRED_MODELS = [
    "models/gemini-2.5-flash"
]

def get_client():
    """Return a configured Gemini client."""
    return genai.Client(api_key=API_KEY)

def safe_generate_content(prompt: str):
    """Try multiple Gemini models to ensure it works."""
    client = get_client()
    last_error = None
    for model in PREFERRED_MODELS:
        try:
            print(f"[Gemini] Using model: {model}")
            response = client.models.generate_content(model=model, contents=prompt)
            text = getattr(response, "text", None) or str(response)
            if text.strip():
                return text
        except Exception as e:
            print(f"[Gemini Error with {model}]: {e}")
            last_error = e
            continue
    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")

# ----------------------------------------------------------------------
# CHARACTER GENERATION
# ----------------------------------------------------------------------
def generate_characters(book_title: str, top_k: int = 5):
    """
    Return a list of top_k characters for the given book_title.
    Uses Gemini text generation.
    """
    prompt = (
        f"List the {top_k} most popular characters (one per line, no numbering, no bullets, "
        f"no extra text) from the book or movie titled '{book_title}'. "
        "If unsure, guess the most likely main characters."
    )

    print(f"[Prompt] {prompt}")
    text = safe_generate_content(prompt)
    print(f"[Gemini Response Raw]\n{text}\n")

    # Clean lines
    lines = [l.strip(" -•1234567890.") for l in text.splitlines() if l.strip()]
    characters = lines[:top_k]

    # Fallback if response is empty
    if not characters:
        characters = ["Harry Potter", "Hermione Granger", "Ron Weasley", "Albus Dumbledore", "Severus Snape"]

    return characters

# ----------------------------------------------------------------------
# CHAPTER GENERATION
# ----------------------------------------------------------------------
def generate_chapter_and_options(book_title: str, character: str, prev_context: str = "", max_tokens=800):
    """
    Generate narrative text (chapter) from a character's perspective
    with 3 next-choice options.
    """
    prompt = f"""
You are a creative fiction writer. Write a chapter of a choose-your-own-adventure story
based on "{book_title}", written from the perspective of "{character}".
Keep it engaging (~400-800 words). After the story, provide exactly three options for what happens next.
Each option should be on a new line starting with "1.", "2.", "3." and be less than 25 words.
If earlier context exists, continue naturally from it:
{prev_context}
"""

    text = safe_generate_content(prompt)
    print(f"[Gemini Chapter Raw]\n{text}\n")

    # Split chapter and options
    lines = text.strip().splitlines()
    opts, chapter_lines, option_start = [], [], None

    for i, line in enumerate(lines):
        if line.strip().startswith(("1.", "1)")):
            option_start = i
            break

    if option_start is not None:
        chapter_lines = lines[:option_start]
        opt_lines = lines[option_start:]
        for ol in opt_lines:
            stripped = ol.strip()
            if stripped and stripped[0].isdigit() and stripped[1] in ". )":
                opts.append(stripped[2:].strip())
    else:
        # fallback: assume last 3 lines are options
        chapter_lines = lines[:-3]
        opts = lines[-3:] if len(lines) >= 3 else []

    options = [{"id": idx + 1, "text": o} for idx, o in enumerate(opts)]
    return {"chapter_text": "\n".join(chapter_lines).strip(), "options": options}
