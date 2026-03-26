from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.schemas import BookQuery

# Close Ollama Function
def close_ollama():
    try:
        structured_chain.client.close()
    except:
        pass

    try:
        chat_chain.client.close()
    except:
        pass

# LLM
llm = ChatOllama(model="gemma3:4b", temperature=0.2)

# Parser
parser = PydanticOutputParser(pydantic_object=BookQuery)

# Prompt for structured extraction
structured_prompt = PromptTemplate(
    template=(
        "You are an expert system for extracting book information from user messages.\n"
        "Your task is to identify the *specific book title* and *author* the user is referring to.\n\n"
        "Follow these rules strictly:\n"
        "1. If the user clearly mentions a book title, extract it exactly as written.\n"
        "2. If the user mentions an author, extract it exactly as written.\n"
        "3. If you are unsure about the title or the user did not provide one, return an empty string \"\".\n"
        "4. Do NOT infer or guess titles or authors that were not explicitly mentioned.\n"
        "5. Do NOT add extra fields.\n"
        "6. Return ONLY valid JSON that matches this schema:\n"
        "{format_instructions}\n\n"
        "Examples:\n"
        "User: 'I loved Pride and Prejudice by Jane Austen'\n"
        "Output: {{\"title\": \"Pride and Prejudice\", \"author\": \"Jane Austen\"}}\n\n"
        "User: 'I want something like that book about a boy wizard'\n"
        "Output: {{\"title\": \"\", \"author\": \"\"}}\n\n"
        "User message: {user_input}"
    ),
    input_variables=["user_input"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

# LCEL chain for structured extraction
structured_chain = structured_prompt | llm | parser

# Prompt for conversational clarification
chat_prompt = PromptTemplate(
    template=(
        "You are a helpful assistant trying to identify the exact book the user is referring to.\n"
        "The previous extraction attempt failed because the title was unclear or missing.\n\n"
        "Your goal is to ask ONE clear, concise clarifying question that helps the user provide:\n"
        "- the book title, OR\n"
        "- a distinctive detail that would allow identifying the title.\n\n"
        "Guidelines:\n"
        "- Ask only one question at a time.\n"
        "- Do not assume or guess the book.\n"
        "- Do not suggest possible titles.\n"
        "- Keep the question short and focused.\n\n"
        "User message: {user_input}\n\n"
        "Ask your clarifying question:"
    ),
    input_variables=["user_input"],
)

# LCEL chain for conversation
chat_chain = chat_prompt | llm

broad_idea_prompt = PromptTemplate(
    template=(
        "The user has tried to describe a book, but no clear title could be extracted.\n"
        "Your task is to summarize the *type of book* the user is referring to.\n\n"
        "Guidelines:\n"
        "- Do NOT guess or invent a specific book title.\n"
        "- Focus only on the themes, genre, characters, or plot elements the user mentioned.\n"
        "- Produce a short, clear description suitable for semantic search.\n"
        "- Keep it under 50 words.\n\n"
        "User messages:\n{conversation}\n\n"
        "Return ONLY the summary text, nothing else."
    ),
    input_variables=["conversation"],
)
