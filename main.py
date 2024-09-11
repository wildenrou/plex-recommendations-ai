import logging
import os
import time
import openai
import re
from plexapi.server import PlexServer
from utils.classes import UserInputs

# Initialize user inputs
userInputs = UserInputs(
    plex_url=os.getenv("PLEX_URL"),
    plex_token=os.getenv("PLEX_TOKEN"),
    openai_key="ollama",  # Dummy key, required by the OpenAI client
    library_names=os.getenv("LIBRARY_NAMES", "").split(","),  # Split multiple libraries by comma
    collection_title=os.getenv("COLLECTION_TITLE"),
    history_amount=int(os.getenv("HISTORY_AMOUNT")),
    recommended_amount=int(os.getenv("RECOMMENDED_AMOUNT")),
    minimum_amount=int(os.getenv("MINIMUM_AMOUNT")),
    wait_seconds=int(os.getenv("SECONDS_TO_WAIT", 86400)),
)

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

# Configure OpenAI to point to your local Ollama instance
openai.api_base = "http://localhost:11434/v1"  # Replace with your Ollama server's IP and port
openai.api_key = userInputs.openai_key  # The key is required by the OpenAI client but not used by Ollama

import re

def create_collection(plex, movie_items, description, library):
    logging.info("Finding matching movies in your library...")
    movie_list = []
    
    for item in movie_items:
        # Clean the movie title to remove any unwanted characters
        cleaned_item = re.sub(r"[^a-zA-Z0-9\s]", "", item).strip()
        
        # Perform the search with the cleaned title
        movie_search = plex.search(cleaned_item, mediatype="movie", limit=3)
        if len(movie_search) > 0:
            movie_list.append(movie_search[0])
            logging.info(f"{cleaned_item} - found")
        else:
            logging.info(f"{cleaned_item} - not found")

    if len(movie_list) > userInputs.minimum_amount:
        try:
            collection = library.collection(userInputs.collection_title)
            collection.removeItems(collection.items())
            collection.addItems(movie_list)
            collection.editSummary(description)
            logging.info("Updated pre-existing collection")
        except:
            collection = plex.createCollection(
                title=userInputs.collection_title,
                section=library.title,
                items=movie_list
            )
            collection.editSummary(description)
            logging.info("Added new collection")
    else:
        logging.info("Not enough movies were found")

def run():
    # Connect to Plex server
    while True:
        logger.info("Starting collection run")
        try:
            plex = PlexServer(userInputs.plex_url, userInputs.plex_token)
            logging.info("Connected to Plex server")
        except Exception as e:
            logging.error("Plex Authorization error")
            return

        for library_name in userInputs.library_names:
            try:
                # Fetch watch history from Plex
                library = plex.library.section(library_name.strip())
                account_id = plex.systemAccounts()[1].accountID

                items_string = ""
                history_items_titles = []
                watch_history_items = plex.history(librarySectionID=library.key, maxresults=userInputs.history_amount, accountID=account_id)
                logging.info(f"Fetching items from your watch history in library {library_name.strip()}")

                for history_item in watch_history_items:
                    history_items_titles.append(history_item.title)

                items_string = ", ".join(history_items_titles)
                logging.info(f"Found {items_string} to base recommendations off")

            except Exception as e:
                logging.error(f"Failed to get watched items for library {library_name.strip()}")
                continue

            try:
                # Formulate the query for recommendations
                query = (
                    "Can you give me movie recommendations based on what I've watched? "
                    f"I've watched {items_string}. "
                    f"Can you base your recommendations solely on what I've watched already? "
                    f"I need around {userInputs.recommended_amount}. "
                    "Please give me the comma separated result, and then a very brief explanation "
                    "separated from the movie values, separated by 3 pluses like '+++'. Not a numbered list."
                )

                # Query the Ollama server via the OpenAI-compatible API
                logging.info(f"Querying Ollama for recommendations for library {library_name.strip()}...")
                chat_completion = openai.ChatCompletion.create(
                    model="llama3.1",  # Specify the model to use, e.g., llama2
                    messages=[{"role": "user", "content": query}]
                )
                ai_result = chat_completion.choices[0].message.content
                ai_result_split = ai_result.split("+++")
                ai_movie_recommendations = ai_result_split[0]
                ai_movie_description = ai_result_split[1]

                movie_items = list(filter(None, ai_movie_recommendations.split(",")))
                logging.info("Query success!")
            except Exception as e:
                logging.error(f"Was unable to query Ollama: {e}")
                continue

            if len(movie_items) > 0:
                create_collection(plex, movie_items, ai_movie_description, library)

        logging.info("Waiting on next call...")
        time.sleep(userInputs.wait_seconds)

if __name__ == '__main__':
    run()
