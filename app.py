from flask import Flask, render_template, request, jsonify, session
from main import CATEGORIES
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
from process_dilekce import process_and_customize_dilekce
from get_embedding_function import get_embedding_function


app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management

CHROMA_PATH = "chroma"
PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""


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


def to_lower_turkish(text: str) -> str:
    """
    Türkçe karakterlere duyarlı küçük harfe dönüştürme.
    """
    translation_table = str.maketrans("IİÇÖÜŞĞ", "ıiçöüşğ")
    return text.translate(translation_table).lower()


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


def query_rag_web(category: str, child_status: str = None, alimony_status: str = None):
    """
    Web version of query_rag that returns detailed status and results
    """
    try:
        # Initialize embedding function and database
        embedding_function = get_embedding_function()
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

        # Log the initialization
        status_messages = ["✓ Veritabanı başarıyla başlatıldı"]

        # Get all documents from database
        results = db.get(include=["metadatas", "documents"])

        # Filter by category and extract KONU section
        filtered_results = []
        for doc, metadata in zip(results["documents"], results["metadatas"]):
            if metadata.get("kategori", "").lower() == category.lower():
                # Extract KONU section
                topic_section = extract_section(doc, section="KONU")
                if topic_section:
                    filtered_results.append((doc, metadata, topic_section))

        if not filtered_results:
            return {
                "success": False,
                "messages": status_messages + ["❌ Bu kategoride uygun dilekçe bulunamadı"],
                "dilekce": None
            }

        status_messages.append(f"✓ {len(filtered_results)} adet uygun dilekçe bulundu")

        # Filter by child status if provided
        if child_status:
            key_phrase = " bulunmaktadır" if child_status == "var" else "bulunmamaktadır"
            matched_results = [
                (doc, metadata) for doc, metadata, _ in filtered_results
                if key_phrase in to_lower_turkish(doc)
            ]
            
            if not matched_results:
                return {
                    "success": False,
                    "messages": status_messages + [f"❌ '{child_status}' durumuna uygun dilekçe bulunamadı"],
                    "dilekce": None
                }
            
            status_messages.append(f"✓ Çocuk durumu '{child_status}' olan {len(matched_results)} dilekçe bulundu")
        else:
            matched_results = [(doc, metadata) for doc, metadata, _ in filtered_results]

        # Filter by alimony status if provided
        selected_dilekce_chunks = []
        if alimony_status and matched_results:
            found_matching_dilekce = False
            for doc, metadata in matched_results:
                related_chunks = [
                    (chunk_doc, chunk_metadata) for chunk_doc, chunk_metadata in zip(results["documents"], results["metadatas"])
                    if chunk_metadata.get("source_file") == metadata.get("source_file")
                ]

                nafaka_result, nafaka_chunk = check_alimony_status(related_chunks, alimony_status)
                if nafaka_result is not None:
                    status_messages.append(f"✓ Nafaka durumu '{alimony_status}' olan dilekçe bulundu")
                    selected_dilekce_chunks = [chunk_doc for chunk_doc, _ in related_chunks]
                    found_matching_dilekce = True
                    source_file = metadata.get("source_file", "Bilinmeyen kaynak")
                    break

            if not found_matching_dilekce:
                return {
                    "success": False,
                    "messages": status_messages + [f"❌ '{alimony_status}' durumuna uygun dilekçe bulunamadı"],
                    "dilekce": None
                }
        elif matched_results:
            # If no alimony status provided, use the first matched result
            doc, metadata = matched_results[0]
            source_file = metadata.get("source_file", "Bilinmeyen kaynak")
            related_chunks = [
                chunk_doc for chunk_doc, chunk_metadata in zip(results["documents"], results["metadatas"])
                if chunk_metadata.get("source_file") == source_file
            ]
            selected_dilekce_chunks = related_chunks

        # Combine chunks into final dilekce
        if selected_dilekce_chunks:
            combined_dilekce = "\n".join(selected_dilekce_chunks)
            status_messages.append(f"✓ Kaynak dosya: {source_file}")
            
            return {
                "success": True,
                "messages": status_messages,
                "dilekce": combined_dilekce,
                "source_file": source_file
            }
        else:
            return {
                "success": False,
                "messages": status_messages + ["❌ Uygun dilekçe bulunamadı"],
                "dilekce": None
            }

    except Exception as e:
        return {
            "success": False,
            "messages": status_messages + [f"❌ Hata oluştu: {str(e)}"],
            "dilekce": None
        }


@app.route('/')
def index():
    # Clear any existing session data
    session.clear()
    return render_template('index.html', categories=CATEGORIES)


@app.route('/step1', methods=['POST'])
def step1():
    category = request.form.get('category')
    if not category:
        return jsonify({
            "success": False,
            "message": "Lütfen bir kategori seçin"
        })

    # Store category in session
    session['category'] = category
    
    # Query the RAG system with only category
    result = query_rag_web(category)
    
    if not result["success"]:
        return jsonify({
            "success": False,
            "message": "Dilekçe oluşturulurken bir hata oluştu",
            "details": result["messages"]
        })
    
    return jsonify({
        "success": True,
        "messages": result["messages"],
        "next_step": "child_status"
    })

@app.route('/step2', methods=['POST'])
def step2():
    child_status = request.form.get('child_status')
    if not child_status:
        return jsonify({
            "success": False,
            "message": "Lütfen çocuk durumunu belirtin"
        })

    # Get category from session
    category = session.get('category')
    if not category:
        return jsonify({
            "success": False,
            "message": "Kategori bilgisi bulunamadı"
        })

    # Store child_status in session
    session['child_status'] = child_status
    
    # Query with category and child_status
    result = query_rag_web(category, child_status=child_status)
    
    if not result["success"]:
        return jsonify({
            "success": False,
            "message": "Dilekçe oluşturulurken bir hata oluştu",
            "details": result["messages"]
        })
    
    return jsonify({
        "success": True,
        "messages": result["messages"],
        "next_step": "alimony_status"
    })

@app.route('/step3', methods=['POST'])
def step3():
    alimony_status = request.form.get('alimony_status')
    if not alimony_status:
        return jsonify({
            "success": False,
            "message": "Lütfen nafaka durumunu belirtin"
        })

    # Get category and child_status from session
    category = session.get('category')
    child_status = session.get('child_status')
    if not category or not child_status:
        return jsonify({
            "success": False,
            "message": "Kategori veya çocuk durumu bilgisi bulunamadı"
        })

    # Store in session
    session['alimony_status'] = alimony_status
    
    # Query with all parameters
    result = query_rag_web(category, child_status=child_status, alimony_status=alimony_status)
    
    if not result["success"]:
        return jsonify({
            "success": False,
            "message": "Dilekçe oluşturulurken bir hata oluştu",
            "details": result["messages"]
        })

    # Store the dilekce in session
    session['dilekce'] = result["dilekce"]
    
    return jsonify({
        "success": True,
        "messages": result["messages"],
        "next_step": "personal_info"
    })


@app.route('/step4', methods=['POST'])
def step4():
    try:
        # Get personal information from the form
        personal_info = {
            "davacı_adi_soyadi": request.form.get('davaci_adi_soyadi'),
            "davacı_tc": request.form.get('davaci_tc'),
            "davacı_adres": request.form.get('davaci_adres'),
            "davalı_adi_soyadi": request.form.get('davali_adi_soyadi'),
            "davalı_tc": request.form.get('davali_tc'),
            "davalı_adres": request.form.get('davali_adres')
        }

        # Validate required fields
        for key, value in personal_info.items():
            if not value:
                return jsonify({
                    "success": False,
                    "message": f"Lütfen {key.replace('_', ' ')} alanını doldurun"
                })

        # Get court information
        court_info = {
            "mahkeme_sehri": request.form.get('mahkeme_sehri')
        }
        if not court_info["mahkeme_sehri"]:
            return jsonify({
                "success": False,
                "message": "Lütfen mahkeme şehrini belirtin"
            })

        # Get marriage date
        marriage_date = request.form.get('marriage_date')
        if not marriage_date:
            return jsonify({
                "success": False,
                "message": "Lütfen evlilik tarihini belirtin"
            })

        # Get stored data from session
        dilekce = session.get('dilekce')
        child_status = session.get('child_status')
        alimony_status = session.get('alimony_status')

        if not dilekce:
            return jsonify({
                "success": False,
                "message": "Dilekçe bulunamadı, lütfen baştan başlayın"
            })

        # Get alimony and compensation amounts if requested
        nafaka_miktari = None
        tazminat_miktari = None
        if alimony_status == "talep_ediliyor":
            nafaka_miktari = request.form.get('nafaka_miktari')
            tazminat_miktari = request.form.get('tazminat_miktari')
            if not nafaka_miktari or not nafaka_miktari.isdigit():
                return jsonify({
                    "success": False,
                    "message": "Lütfen geçerli bir nafaka miktarı belirtin"
                })
            if not tazminat_miktari or not tazminat_miktari.isdigit():
                return jsonify({
                    "success": False,
                    "message": "Lütfen geçerli bir manevi tazminat miktarı belirtin"
                })

        # Get children details if there are children
        children = None
        if child_status == "var":
            try:
                children_count = int(request.form.get('children_count', 0))
                children = []
                for i in range(children_count):
                    child = {
                        "name": request.form.get(f'child_name_{i}'),
                        "birth_year": request.form.get(f'child_birth_year_{i}'),
                        "nafaka": request.form.get(f'child_nafaka_{i}'),
                        "velayet": request.form.get(f'child_velayet_{i}')
                    }
                    if not all(child.values()):
                        return jsonify({
                            "success": False,
                            "message": f"{i+1}. çocuk için tüm bilgileri doldurun"
                        })
                    children.append(child)
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "Çocuk sayısı geçerli bir sayı olmalıdır"
                })

        # Get current date
        from datetime import datetime
        tarih = datetime.now().strftime("%d.%m.%Y")

        # Process and customize the dilekce with all collected information
        customized_text = process_and_customize_dilekce(
            dilekce_text=dilekce,
            child_status=child_status,
            alimony_status=alimony_status,
            personal_info=personal_info,
            court_info=court_info,
            tarih=tarih,
            marriage_date=marriage_date,
            nafaka_miktari=nafaka_miktari,
            tazminat_miktari=tazminat_miktari,
            children=children
        )

        return jsonify({
            "success": True,
            "dilekce": customized_text
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Dilekçe özelleştirilirken hata oluştu: {str(e)}"
        })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
