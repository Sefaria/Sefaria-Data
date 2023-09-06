from sources.local_settings import OPEN_AI_API_KEY
from langchain.text_splitter import Language
from langchain.document_loaders.generic import GenericLoader
from langchain.document_loaders.parsers import LanguageParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryMemory
from langchain.chains import ConversationalRetrievalChain


def chain_llm():
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

    db = Chroma.from_documents(texts, OpenAIEmbeddings(disallowed_special=(), openai_api_key=OPEN_AI_API_KEY))
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
    qa = chain_llm()
    question = "Write me sample code for creating a new Index for the book of \"Bereshit\"?"
    ask(qa, question)

# - Chunks make sense? Too large...
# - Examples need to be very similar to the question asked
# - Expect more of eng, give details about the text. We expect engineers to invest in the prompt.
# - Caching (LangChain) - two liner at beginning of file.
# - VectorDB in RAM vs persisting to DISC, so can pull from there for LLM initializing (if chunks shift etc, clear db).
# - Content eng guide / give it documentation / couple of Steve/Yishai well-written projects, bring that in too.
