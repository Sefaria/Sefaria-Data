from sources.local_settings import OPEN_AI_API_KEY
import langchain
from langchain.text_splitter import Language
from langchain.document_loaders.generic import GenericLoader
from langchain.document_loaders.parsers import LanguageParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryMemory
from langchain.chains import ConversationalRetrievalChain

from langchain.cache import InMemoryCache
langchain.llm_cache = InMemoryCache()

## TODO
# - To get started, make sure your OPEN_API_KEY is defined in your local_setting file


def chain_llm(new_persist_to_db=True):
    """
    This function is the "main" of this experiment.
    :param new_persist_to_db Boolean: This variable determines whether or not to persist the vector stores to the DB. It
                                      should be set to True on every "new" run, to set up the vector store appropriately.
                                      On subsequent runs, if set to False, it will append to the existing vector store.
    :return qa: A conversational retrieval chain you can "chat" with
    """

    # Right now, we are training this model on the templates/ subdirectory. This is likely the
    # main reason why we're seeing overall poor performance. In order to optimize this code,
    # we would need to train on all of Sefaria-Data.
    repo_path = "/Users/sefaria/Sefaria-Data/templates"

    # STEP ONE: DOCUMENT LOADING
    # Use the GenericLoader for Python to load the code in the repo_path
    loader = GenericLoader.from_filesystem(
        repo_path,
        glob="**/*",
        suffixes=[".py"],
        parser=LanguageParser(language=Language.PYTHON, parser_threshold=500)
    )
    documents = loader.load()
    print(len(documents))

    # STEP TWO: DOCUMENT SPLITTING
    # Using the RecursiveCharacterTextSplitter (also, set to Python) we split
    # the code into semantically meaningful chunks.
    python_splitter = RecursiveCharacterTextSplitter.from_language(language=Language.PYTHON,
                                                                   chunk_size=2000,
                                                                   chunk_overlap=200)
    texts = python_splitter.split_documents(documents)
    print(len(texts))

    # STEP THREE: EMBEDDINGS
    # Create DB vector store if it does not yet exist (indicated by new_persist_to_db)
    # Save the embedded document splits in the database.
    # Note: On subsequent runs, this step can be skipped, and one can proceed to retrieval.
    if new_persist_to_db:
        db = Chroma.from_documents(texts, OpenAIEmbeddings(disallowed_special=(), openai_api_key=OPEN_AI_API_KEY), persist_directory="./chroma_db")

    # STEP FOUR: RETRIEVAL
    # Pull vector store from where it was persisted on disc (in a chroma DB)
    db = Chroma(persist_directory="./chroma_db", embedding_function=OpenAIEmbeddings(disallowed_special=(), openai_api_key=OPEN_AI_API_KEY))

    retriever = db.as_retriever(
        search_type="mmr",  # Can also test "similarity"
        search_kwargs={"k": 8},
    )

    # STEP FIVE: CHAT
    # Set up the LLM and the ConversationalRetrievalChain to return our qa object
    # to chat with!
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=OPEN_AI_API_KEY)
    memory = ConversationSummaryMemory(llm=llm, memory_key="chat_history", return_messages=True)
    qa = ConversationalRetrievalChain.from_llm(llm, retriever=retriever, memory=memory)
    return qa


def ask(qa, question):
    result = qa(question)
    print(result['answer'])


if __name__ == '__main__':
    # Note: must be true on first run to persist embeddings to the database.
    qa = chain_llm(new_persist_to_db=False)

    #### YOUR QUESTION GOES HERE #####
    question = "Write me sample code for creating a new Index for the book of \"Bereshit\"?"


    ask(qa, question)

# FURTHER EXPLORATION
# - Do these splits make sense? The chunks might be too large.
# - Examples need to be very similar to the question asked. Would training on Sefaria-Data solve this?
# - Expect more of eng, give details about the text. We expect engineers to invest in the prompt.
# - Have it also read the Content eng guide / give it documentation / ask other engineers for clear well-written projects
# (update: no one had any they could point too offhand, we might have bigger issues)
