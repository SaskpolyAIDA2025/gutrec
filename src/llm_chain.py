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
        "Extract the book title and author from the user's message.\n"
        "Return ONLY valid JSON following this schema:\n"
        "{format_instructions}\n\n"
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
        "You are a helpful assistant. Your goal is to identify the book the user is talking about.\n"
        "Ask clarifying questions until you are confident.\n\n"
        "User: {user_input}"
    ),
    input_variables=["user_input"],
)

# LCEL chain for conversation
chat_chain = chat_prompt | llm