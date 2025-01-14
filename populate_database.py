import argparse
import os
import shutil
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from get_embedding_function import get_embedding_function
from langchain_chroma import Chroma

CHROMA_PATH = "chroma"
DATA_PATH = "data"

# Kategori listesi ve eşleşen anahtar kelimeler
CATEGORIES = {
    "anlaşmalı boşanma": ["anlaşmalı olarak boşanmalarına"],
    "ekonomik sıkıntılar": ["maddi sıkıntılar", "ailevi gerekçelerin "],
    "madde bağımlılığı": ["madde bağımlılığı"],
    "fiziksel şiddet": ["fiziksel şiddet", "dayak"],
    "psikolojik şiddet": ["psikolojik baskı", "duygusal şiddet","hakaret"],
    "şiddetli geçimsizlik": ["şiddetli geçimsizlik", "anlaşmazlık"],
    "ilgisizlik": ["ilgisizlik", "duygusal uzaklık"],
    "aldatma": ["aldatma", "sadakat yükümlülüğünün ihlali"],
    "velayet": ["velayet", "çocuk velayeti", "müşterek çocuğun velayetinin"],
}

def to_lower_turkish(text: str) -> str:
    """
    Türkçe karakterlere duyarlı küçük harfe dönüştürme.
    """
    translation_table = str.maketrans("IİÇÖÜŞĞ", "ıiçöüşğ")
    return text.translate(translation_table).lower()

def main():
    # Initialize the embedding function
    embedding_function = get_embedding_function()

    # Check if the database should be cleared (using the --reset flag).
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()
    if args.reset:
        print("✨ Clearing Database")
        clear_database()

    # Create (or update) the data store.
    documents = load_documents()
    chunks = split_documents(documents)
    add_to_chroma(chunks, embedding_function)


def load_documents():
    # Load all PDFs from the data directory
    document_loader = PyPDFDirectoryLoader(DATA_PATH)
    return document_loader.load()


def split_documents(documents: list[Document]):
    # Split documents into smaller chunks for better processing
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)


def add_to_chroma(chunks: list[Document], embedding_function):
    # Load or initialize the Chroma database
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=embedding_function
    )
    
    # Calculate unique IDs for document chunks
    chunks_with_ids = calculate_chunk_ids(chunks)

    # Add metadata (kategori bilgisi ve kaynak dosya adı)
    for chunk in chunks_with_ids:
        content = to_lower_turkish(chunk.page_content)
        chunk.metadata["kategori"] = assign_category(content)
        chunk.metadata["source_file"] = chunk.metadata.get("source", "unknown")  # Kaynak dosya adı

    # Fetch existing document IDs from the database
    existing_items = db.get(include=[])  # IDs are always included by default
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Add only new chunks to the database
    new_chunks = [chunk for chunk in chunks_with_ids if chunk.metadata["id"] not in existing_ids]

    if len(new_chunks):
        print(f"👉 Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
    else:
        print("✅ No new documents to add")


def assign_category(content):
    """
    Dilekçenin içeriğine göre uygun kategoriyi belirler.
    """
    for category, keywords in CATEGORIES.items():
        if any(to_lower_turkish(keyword) in content for keyword in keywords):
            return category
    return "diğer"


def calculate_chunk_ids(chunks):
    # Generate unique IDs for each chunk based on source, page, and chunk index
    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        # If the page ID is the same as the last one, increment the index
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        # Calculate the chunk ID
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Add it to the page meta-data
        chunk.metadata["id"] = chunk_id

    return chunks


def clear_database():
    # Delete the Chroma database directory
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)


def query_rag(category: str):
    """
    Kullanıcının seçtiği kategoriye göre dilekçeyi getirir ve tam metni yazdırır.
    Kaynak PDF dosyasını da belirtir.
    """
    # Veritabanını hazırlayın
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Veritabanındaki tüm belgeleri alın
    results = db.get(include=["metadatas", "documents"])

    # Kategoriye göre filtreleme ve KONU kısmını kontrol etme
    filtered_results = []
    for doc, metadata in zip(results["documents"], results["metadatas"]):
        if metadata.get("kategori", "").lower() == category.lower():
            # "KONU" başlığını bul ve altındaki metni al
            topic_section = extract_section(doc, section="KONU")
            if topic_section:
                filtered_results.append((doc, metadata, topic_section))

    # Sonuçları işleme
    if filtered_results:
        print(f"✅ '{category}' kategorisine uygun dilekçeler bulundu:")
        for idx, (doc, metadata, topic_section) in enumerate(filtered_results, 1):
            source_file = metadata.get("source_file", "Bilinmiyor")
            print(f"\n--- Dilekçe {idx} ---")
            print(f"📂 Kaynak Dosya: {source_file}")
            print(f"🔍 KONU Kısmı: {topic_section.strip()}")
            print(doc)  # Tam metni yazdırır
    else:
        print(f"❌ '{category}' kategorisine uygun dilekçe bulunamadı.")


def extract_section(text: str, section: str) -> str:
    """
    PDF metninde belirli bir bölümün altındaki metni çıkarır.
    """
    text = to_lower_turkish(text)
    section = to_lower_turkish(section)
    if section in text:
        section_start = text.find(section)
        section_text = text[section_start:]
        next_break = section_text.find("\n", len(section))
        return section_text[len(section):next_break].strip()
    return ""


if __name__ == "__main__":
    main()
