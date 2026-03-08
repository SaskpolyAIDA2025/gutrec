from langchain_core.messages import HumanMessage

from .graph.workflow import app
from src.search_query import close_weaviate
from src.llm_chain import close_ollama

import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)

def main():
    state = {
        "messages": [],
        "loop_count": 0
    }

    print("Welcome to the Gutenberg Book Recommendation system.\nGive me a title and author as reference to look for one similar to it.\nType 'exit' to quit.")

    while True:
        user_text = input("\nYou: ")
        if user_text.lower() in ["exit", "quit"]:
            break

        # Add user message to state
        state["messages"].append(HumanMessage(content=user_text))

        # Reset per-turn fields
        state["broad_query"] = ""

        # Run the graph
        for event in app.stream(state):
            for node, value in event.items():
                print(f"--- Finished Node: {node} ---")
                
                # Skip if the node returned None
                if not value:
                    continue

                # Merge ALL returned fields into state
                for key, val in value.items():
                    # Only print messages if they exist
                    if key == "messages":
                        if val:
                            ai_msg = val[-1]
                            print(f"AI: {ai_msg.content}")
                            # Append messages to history
                            state["messages"].append(ai_msg)
                    else:
                        # Store any other state updates (loop_count, extraction, etc.)
                        state[key] = val

        # Reset extraction-related fields so next turn starts clean
        state.pop("extraction", None)
        state.pop("book_metadata", None)
        state.pop("results", None)

    # Clean shutdown
    close_weaviate()
    close_ollama()


if __name__ == "__main__":
    main()