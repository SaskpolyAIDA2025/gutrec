from .graph.workflow import app
from src.search_query import close_weaviate
from src.llm_chain import close_ollama


def main():
    initial_state = {
    "messages": [("user", "Books similar to 'The neverending story' by 'Michael Ende'.")],
    "loop_count": 0
    }

    for event in app.stream(initial_state):
        for node, value in event.items():
            print(f"--- Finished Node: {node} ---")
            
            # Skip if the node returned None
            if not value:
                continue

            # Only print messages if they exist
            if "messages" in value:
                print(f"AI: {value['messages'][-1].content}")
    
    # Clean shutdown
    close_weaviate()
    close_ollama()


if __name__ == "__main__":
    main()