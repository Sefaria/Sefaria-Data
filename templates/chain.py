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


def chain_llm(new_persist_to_db=True):
    repo_path = "/Users/sefaria/Sefaria-Data/templates"

    # Load
    loader = GenericLoader.from_filesystem(
        repo_path,
        glob="**/*",
        suffixes=[".py"],
        parser=LanguageParser(language=Language.PYTHON, parser_threshold=500)
    )
    documents = loader.load()
    print(len(documents))

    python_splitter = RecursiveCharacterTextSplitter.from_language(language=Language.PYTHON,
                                                                   chunk_size=2000,
                                                                   chunk_overlap=200)
    texts = python_splitter.split_documents(documents)
    print(len(texts))

    if new_persist_to_db:
        db = Chroma.from_documents(texts, OpenAIEmbeddings(disallowed_special=(), openai_api_key=OPEN_AI_API_KEY), persist_directory="./chroma_db")

    # Pull from disc:
    db = Chroma(persist_directory="./chroma_db", embedding_function=OpenAIEmbeddings(disallowed_special=(), openai_api_key=OPEN_AI_API_KEY))
    retriever = db.as_retriever(
        search_type="mmr",  # Also test "similarity"
        search_kwargs={"k": 8},
    )

    ####
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=OPEN_AI_API_KEY)
    memory = ConversationSummaryMemory(llm=llm, memory_key="chat_history", return_messages=True)
    qa = ConversationalRetrievalChain.from_llm(llm, retriever=retriever, memory=memory)
    return qa


def ask(qa, question):
    result = qa(question)
    print(result['answer'])


if __name__ == '__main__':
    # Note: must be true on first run to persist
    qa = chain_llm(new_persist_to_db=False)
    question = "Write me sample code for creating a new Index for the book of \"Bereshit\"?"
    ask(qa, question)

# - Chunks make sense? Too large...
# - Examples need to be very similar to the question asked
# - Expect more of eng, give details about the text. We expect engineers to invest in the prompt.

# - Content eng guide / give it documentation / couple of Steve/Yishai well-written projects, bring that in too.
