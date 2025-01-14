import argparse
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
from process_dilekce import process_and_customize_dilekce
from get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

CATEGORIES = [
    "anlaşmalı boşanma",
    "ekonomik sıkıntılar",
    "madde bağımlılığı",
    "fiziksel şiddet",
    "psikolojik şiddet",
    "şiddetli geçimsizlik",
    "ilgisizlik",
    "aldatma",
    "velayet",
]

def to_lower_turkish(text: str) -> str:
    """
    Türkçe karakterlere duyarlı küçük harfe dönüştürme.
    """
    translation_table = str.maketrans("IİÇÖÜŞĞ", "ıiçöüşğ")
    return text.translate(translation_table).lower()

def main():
    """
    Kullanıcıdan kategori bilgisi alır ve uygun dilekçeyi arar.
    """
    # Kullanıcıdan kategori seçmesini isteyin
    category = get_category_from_user()

    # Seçilen kategoriye göre arama yap
    query_rag(category)


def get_category_from_user():
    """
    Kullanıcıdan bir kategori seçmesini ister.
    """
    print("Lütfen aşağıdaki kategorilerden birini seçin:")
    for idx, category in enumerate(CATEGORIES, 1):
        print(f"{idx}. {category}")

    try:
        choice = int(input("Seçiminizi yapın (1-9): "))
        if 1 <= choice <= len(CATEGORIES):
            return CATEGORIES[choice - 1]
        else:
            print("Geçersiz seçim. Lütfen tekrar deneyin.")
            return get_category_from_user()
    except ValueError:
        print("Geçersiz giriş. Lütfen bir sayı girin.")
        return get_category_from_user()
    
def get_child_status_from_user():
    """
    Kullanıcıdan çocuk durumu seçmesini ister.
    """
    print("\nDilekçelerde çocuk durumu için bir seçim yapın:")
    print("1. Çocuk var")
    print("2. Çocuk yok")

    try:
        choice = int(input("Seçiminizi yapın (1-2): "))
        if choice == 1:
            return "var"
        elif choice == 2:
            return "yok"
        else:
            print("Geçersiz seçim. Lütfen tekrar deneyin.")
            return get_child_status_from_user()
    except ValueError:
        print("Geçersiz giriş. Lütfen bir sayı girin.")
        return get_child_status_from_user()
def get_alimony_status_from_user():
    """
    Kullanıcıdan nafaka durumu seçmesini ister.
    """
    print("\nDilekçelerde nafaka durumu için bir seçim yapın:")
    print("1. Nafaka talep ediliyor")
    print("2. Nafaka talep edilmiyor")

    try:
        choice = int(input("Seçiminizi yapın (1-2): "))
        if choice == 1:
            return "talep_ediliyor"
        elif choice == 2:
            return "talep_edilmiyor"
        else:
            print("Geçersiz seçim. Lütfen tekrar deneyin.")
            return get_alimony_status_from_user()
    except ValueError:
        print("Geçersiz giriş. Lütfen bir sayı girin.")
        return get_alimony_status_from_user()


def check_alimony_status(chunks, alimony_status):
    """
    Tüm chunk'larda nafaka durumu kontrol edilir.
    """
    alimony_positive_phrase = "tedbir-yoksulluk"
    alimony_negative_phrase = "nafaka talep etmemektedir"

    for chunk_doc, chunk_metadata in chunks:
        chunk_text = to_lower_turkish(chunk_doc)
        if alimony_status == "talep_ediliyor" and alimony_positive_phrase in chunk_text:
            return True, chunk_doc  # Nafaka talep ediliyor
        if alimony_status == "talep_edilmiyor" and alimony_negative_phrase in chunk_text:
            return False, chunk_doc  # Nafaka talep edilmiyor

    return None, None  # Belirtilen nafaka durumu bulunamadı

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

    # Çocuk durumu sorgulama (kullanıcıdan alınır)
    child_status = get_child_status_from_user()

    # Çift şartlı filtreleme (Kategori + Çocuk Durumu)
    key_phrase = " bulunmaktadır" if child_status == "var" else "bulunmamaktadır"
    matched_results = [
        (doc, metadata) for doc, metadata, _ in filtered_results
        if key_phrase in to_lower_turkish(doc)
    ]

    if matched_results:
        print(f"\n✅ '{child_status}' durumuna ve '{category}' kategorisine uygun dilekçeler bulundu.")
        # Sonuçları yazdır
        for idx, (doc, metadata) in enumerate(matched_results, 1):
            source_file = metadata.get("source_file", "Bilinmiyor")
            print(f"\n--- Dilekçe {idx} ---")
            print(f"📂 Kaynak Dosya: {source_file}")
            print(doc)
    else:
        print(f"❌ '{child_status}' durumuna ve '{category}' kategorisine uygun dilekçe bulunamadı.")
        return

    # Nafaka durumu sorgulama (kullanıcıdan alınır)
    alimony_status = get_alimony_status_from_user()

    # Nafaka durumu kontrolü
    selected_dilekce_chunks = []  # Seçilen dilekçenin parçalarını toplamak için liste
    for doc, metadata in matched_results:
        related_chunks = [
            (chunk_doc, chunk_metadata) for chunk_doc, chunk_metadata in zip(results["documents"], results["metadatas"])
            if chunk_metadata.get("source_file") == metadata.get("source_file")
        ]

        nafaka_result, nafaka_chunk = check_alimony_status(related_chunks, alimony_status)
        if nafaka_result is not None:
            print(f"\n✅ Nafaka Durumu: {'Talep Ediliyor' if nafaka_result else 'Talep Edilmiyor'}")
            print(f"Bulunan Kaynak:\n{nafaka_chunk}")
            print(f"📂 Kaynak Dosya: {metadata.get('source_file')}")
            # Tüm chunk'ları ekle
            selected_dilekce_chunks.extend([chunk_doc for chunk_doc, _ in related_chunks])
        else:
            print(f"❌ '{alimony_status}' durumuna uygun nafaka bilgisi bulunamadı.")
            print(f"📂 Kaynak Dosya: {metadata.get('source_file')}")

    # Kullanıcının template dilekçesi
    if selected_dilekce_chunks:
        combined_dilekce = "\n".join(selected_dilekce_chunks)  # Chunk'ları birleştir
        print("\n--- Kullanıcının Template Dilekçesi ---")
        print(combined_dilekce)

    # Dilekçeyi özelleştir
        process_and_customize_dilekce(combined_dilekce, child_status, alimony_status)

    else:
        print("❌ Seçilen kriterlere uygun dilekçe bulunamadı.")

def extract_section(text: str, section: str) -> str:
    """
    PDF metninde belirli bir bölümün altındaki metni çıkarır.
    
    :param text: Belge metni
    :param section: Başlık (örneğin, "KONU")
    :return: Başlığın altındaki metin (ilk paragraf)
    """
    if section in text:
        section_start = text.find(section)
        section_text = text[section_start:].lower()

        # Başlıktan sonraki ilk paragrafı al
        next_break = section_text.find("\n", len(section))
        return section_text[len(section):next_break].strip()
    return ""
if __name__ == "__main__":
    main()