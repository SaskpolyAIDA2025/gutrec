from llm_chain import chat_chain, structured_chain
from books_api import get_book_metadata
from search_query import semantic_search
from pydantic import ValidationError

def main():
    print("Chatbot: Tell me the title of your reference book and, if possible, its author.")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            print("Chatbot: Goodbye!")
            break

        # First try structured extraction
        try:
            result = structured_chain.invoke({"user_input": user_input})

            # If parsing succeeded, we have a BookQuery object
            title = result.title
            author = result.author

            print(f"\nChatbot: Searching Google Books for '{title}'...\n")
            metadata = get_book_metadata(title, author)

            if not metadata:
                print("Chatbot: I couldn't find that book.")
            else:
                print("=== Book Metadata ===")
                for k, v in metadata.items():
                    print(f"{k}: {v}")
                print("======================\n")

            #print(f"\n{metadata}\n")
            semantic_search(f"Title: {metadata['title']}\nAuthor: {metadata['authors']}\nSummary: {metadata['description']}")
            
            print("Chatbot: You can describe another book or type 'exit'.")
            continue

        except ValidationError:
            # Not enough info yet → continue conversation
            reply = chat_chain.invoke({"user_input": user_input})
            print(f"Chatbot: {reply}")
            continue


if __name__ == "__main__":
    main()