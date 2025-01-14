import re
from datetime import datetime
def get_personal_info():
    """
    Kullanıcıdan davacı ve davalı bilgilerini alır.
    """
    print("\nLütfen davacı bilgilerini giriniz:")
    davaci_adi_soyadi = input("Davacı Adı ve Soyadı: ")
    davaci_tc = input("Davacı T.C. Kimlik No: ")
    davaci_adres = input("Davacı Adresi: ")

    print("\nLütfen davalı bilgilerini giriniz:")
    davali_adi_soyadi = input("Davalı Adı ve Soyadı: ")
    davali_tc = input("Davalı T.C. Kimlik No: ")
    davali_adres = input("Davalı Adresi: ")

    return {
        "davacı_adi_soyadi": davaci_adi_soyadi,
        "davacı_tc": davaci_tc,
        "davacı_adres": davaci_adres,
        "davalı_adi_soyadi": davali_adi_soyadi,
        "davalı_tc": davali_tc,
        "davalı_adres": davali_adres
    }

def get_court_info():
    """
    Kullanıcıdan mahkeme şehrini alır.
    """
    mahkeme_sehri = input("Lütfen mahkeme şehrini giriniz (ör. İstanbul, Ankara): ")
    return {"mahkeme_sehri": mahkeme_sehri}

def get_tarih():
    """
    Kullanıcıdan tarih bilgisini alır.
    """
    tarih = input("\nLütfen dilekçe tarihini giriniz (GG.AA.YYYY) [Varsayılan: Bugünün Tarihi]: ")
    if not tarih.strip():
        tarih = datetime.now().strftime("%d.%m.%Y")
    return tarih
def update_defendant_address(dilekce_text, yeni_adres):
    """
    Dilekçe metnindeki DAVALI başlığı altındaki adresi günceller.
    """
    lines = dilekce_text.splitlines()  # Metni satır satır böler
    updated_lines = []
    davali_section = False

    for line in lines:
        if "DAVALI:" in line:  # DAVALI başlığı bulundu
            davali_section = True
            updated_lines.append(line)  # DAVALI başlığını olduğu gibi ekle
            continue

        if davali_section:
            if "Adres:" in line:  # Adres kısmını buldu
                updated_lines.append(f"Adres: {yeni_adres}")  # Yeni adresi ekle
                davali_section = False  # Adres güncellendi, davalı kısmı bitti
            else:
                updated_lines.append(line)  # Adres değilse olduğu gibi ekle
        else:
            updated_lines.append(line)  # Diğer satırları olduğu gibi ekle

    return "\n".join(updated_lines)  # Güncellenmiş satırları birleştir


def get_marriage_date():
    """
    Kullanıcıdan evlenme tarihini alır.
    """
    marriage_date = input("Lütfen evlenme tarihini giriniz (GG.AA.YYYY): ")
    return marriage_date
def get_alimony_amount():
    """
    Kullanıcıdan nafaka miktarını alır ve geçerli bir sayı olduğundan emin olur.
    """
    while True:
        nafaka_miktari = input("Lütfen talep edilen nafaka miktarını giriniz (ör. 3000): ").strip()
        if nafaka_miktari.isdigit():  # Sadece rakamlardan oluşuyorsa
            return nafaka_miktari  # Örnek: "3000" döner
        else:
            print("Geçersiz miktar girdiniz. Lütfen tekrar deneyin.")
def update_alimony_in_text(dilekce_text, nafaka_miktari):
    """
    Açıklamalar ve Sonuç & Talep kısmındaki nafaka miktarını günceller.
    """
    # Açıklamalar kısmındaki nafaka talebini güncelle
    dilekce_text = re.sub(
        r"(Davacı lehine aylık\s*)(\d+[.,]?\d*)(\s*TL tedbir-yoksulluk nafakasına hükmedilmesine)",
        lambda m: f"{m.group(1)}{nafaka_miktari}{m.group(3)}",
        dilekce_text
    )

    # Sonuç ve Talep kısmındaki nafaka talebini güncelle
    dilekce_text = re.sub(
        r"(2\. Davacı lehine aylık\s*)(\d+[.,]?\d*)(\s*TL tedbir-yoksulluk nafakasına hükmedilmesine)",
        lambda m: f"{m.group(1)}{nafaka_miktari}{m.group(3)}",
        dilekce_text
    )

    return dilekce_text

def get_tazminat_amount():
    """
    Kullanıcıdan manevi tazminat miktarını alır ve geçerli bir sayı olduğundan emin olur.
    """
    while True:
        tazminat_miktari = input("Lütfen talep edilen manevi tazminat miktarını giriniz (ör. 50000): ").strip()
        if tazminat_miktari.isdigit():  # Sadece rakamlardan oluşuyorsa
            return tazminat_miktari  # Örnek: "50000" döner
        else:
            print("Geçersiz miktar girdiniz. Lütfen tekrar deneyin.")

def update_tazminat_in_text(dilekce_text, tazminat_miktari):
    """
    Açıklamalar ve SONUÇ VE TALEP kısmındaki manevi tazminat miktarını günceller.
    """
    # Açıklamalar kısmındaki manevi tazminat talebini güncelle
    dilekce_text = re.sub(
        r"(maddi ve manevi zorluklar nedeniyle\s*)(\d{1,3}(\.\d{3})*|\d+)(\s*TL\s*manevi tazminat talep edilmektedir)",
        lambda m: f"{m.group(1)}{tazminat_miktari}{m.group(4)}",
        dilekce_text
    )

    # Sonuç ve Talep kısmındaki manevi tazminat talebini güncelle
    dilekce_text = re.sub(
        r"(3\. Davacı lehine\s*)(\d{1,3}(\.\d{3})*|\d+)(\s*TL manevi tazminata hükmedilmesine)",
        lambda m: f"{m.group(1)}{tazminat_miktari}{m.group(4)}",
        dilekce_text
    )

    return dilekce_text
def get_children_details():
    """
    Kullanıcıdan çocuk sayısını, isimlerini ve doğum yıllarını alır.
    """
    try:
        child_count = int(input("\nKaç müşterek çocuk var?: "))
        if child_count == 0:
            return None
        children = []
        for i in range(1, child_count + 1):
            print(f"\n{str(i)}. Çocuk:")
            name = input("Çocuğun Adı: ")
            birth_year = input("Çocuğun Doğum Yılı: ")
            nafaka = input(f"{name} için talep edilen nafaka miktarını giriniz (TL): ").strip()
            velayet = input(f"{name} için velayet davacıya mı verilecek? (Evet/Hayır): ").strip().lower()
            velayet_durum = "davacı" if velayet == "evet" else "davalı"
            children.append({"name": name, "birth_year": birth_year, "nafaka": nafaka, "velayet": velayet_durum})
        return children
    except ValueError:
        print("Lütfen geçerli bir sayı giriniz.")
        return get_children_details()

def update_children_in_text(dilekce_text, children, personal_info):
    """
    Açıklamalar kısmındaki çocuk bilgilerini günceller.
    """
    # "müşterek çocukları bulunmaktadır" veya benzer ifadeleri arar
    match = re.search(
    r"(Bu evlilikten.*?müşterek çocukları bulunmaktadır\.?)",  # Nokta opsiyonel olabilir
    dilekce_text,
    re.DOTALL
)

    if match:
        if not children:
            # Çocuk yoksa ilgili ifadeyi güncelle
            dilekce_text = re.sub(
                r"(Bu evlilikten).*?müşterek çocukları bulunmaktadır\.",
                r"Bu evlilikten müşterek çocukları bulunmamaktadır.",
                dilekce_text,
                flags=re.DOTALL
            )
        else:
            # Çocuk bilgilerini oluştur
            children_text = " ve ".join(
                [f"{child['birth_year']} doğumlu {child['name']}" for child in children]
            )
            child_count = len(children)
            if child_count == 1:
                replacement = f"Bu evlilikten {children_text} isimli bir müşterek çocukları bulunmaktadır."
            else:
                replacement = f"Bu evlilikten {children_text} isimli {child_count} müşterek çocukları bulunmaktadır."

            # İlgili ifadeyi güncelle
            dilekce_text = re.sub(
                r"(Bu evlilikten).*?müşterek çocukları bulunmaktadır\.",
                replacement,
                dilekce_text,
                flags=re.DOTALL
            )
                  
             # Açıklamalar kısmındaki nafaka detaylarını güncelle
            nafaka_text = ", ".join(
            [f"Müşterek çocuk {child['name']} için aylık {child['nafaka']} TL iştirak nafakası"
             for child in children]
            )
            nafaka_sentence = f"{nafaka_text} talep edilmektedir."
            dilekce_text = re.sub(
            r"(Müşterek çocuk.*?iştirak nafakasına hükmedilmesi talep edilmektedir\.)",
            nafaka_sentence,
            dilekce_text,
            flags=re.DOTALL
        )

           # Sonuç ve Talep kısmını güncelle
            if children:
             sonuc_nafaka_text = " ve ".join(
              [f"Müşterek çocuk {child['name']} için aylık {child['nafaka']} TL iştirak nafakasına hükmedilmesine"
              for child in children]
        )
            dilekce_text = re.sub(
            r"(4\. Müşterek çocuk.*?iştirak nafakasına hükmedilmesine,)",
            f"4. {sonuc_nafaka_text},",
            dilekce_text,
            flags=re.DOTALL
        )
            
           # Sonuç ve Talep kısmını güncelle
            if children:
             sonuc_velayet_text = " ve ".join(
              [f"Müşterek çocuk {child['name']} velayetinin {child['velayet']} {personal_info['davacı_adi_soyadi'] if child['velayet'] == 'davacı' else personal_info['davalı_adi_soyadi']} verilmesine" for child in children]
        )
            dilekce_text = re.sub(
            r"(5\. Müşterek çocuk.*?velayetinin.*?verilmesine,)",
            f"5. {sonuc_velayet_text },",
            dilekce_text,
            flags=re.DOTALL
        )
    else:
        print("Hedef ifade bulunamadı: 'müşterek çocukları bulunmaktadır.'")

    return dilekce_text
def replace_above_signature_with_davaci_name(dilekce_text, personal_info):
    """
    İmzanın üstünde bulunan davacının adını günceller.
    """
    # İmzanın üstündeki satırı değiştirmek için regex kullan
    dilekce_text = re.sub(
        r"(?<=Davacı:\s)(.*?\n).*?(?=\[\s*İmza\s*\])",  # "Davacı" kısmından başlayıp "İmza" öncesine kadar olan bölge
        f"{personal_info['davacı_adi_soyadi']}\n",  # Yeni davacı adı
        dilekce_text,
        flags=re.DOTALL
    )
    return dilekce_text


def customize_dilekce(dilekce_text, personal_info, court_info, tarih, marriage_date, alimony_status, nafaka_miktari,tazminat_miktarı, children, child_status):
    """
    Dilekçe metnini verilen kişisel bilgiler ve mahkeme şehriyle özelleştirir.

    :param dilekce_text: Orijinal dilekçe metni
    :param personal_info: Kullanıcıdan alınan kişisel bilgiler (sözlük)
    :param court_info: Kullanıcıdan alınan mahkeme bilgisi (sözlük)
    :return: Özelleştirilmiş dilekçe metni
    """
    # Mahkeme kısmını değiştirme
    dilekce_text = re.sub(
        r"(TÜRKİYE CUMHURİYETİ\s*[^\n]+ MAHKEMESİ’NE)", 
        f"TÜRKİYE CUMHURİYETİ\n{court_info['mahkeme_sehri']} AİLE MAHKEMESİ’NE", 
        dilekce_text
    )
    
    # "DAVACI: Adı-Soyadı" kısmını değiştirme
    dilekce_text = re.sub(
        r"(DAVACI:\s*Adı-Soyadı:)\s*[^\n]+", 
        f"\\1 {personal_info['davacı_adi_soyadi']}", 
        dilekce_text
    )
    
    # "DAVACI: T.C. Kimlik No" kısmını değiştirme
    dilekce_text = re.sub(
        r"(T\.C\. Kimlik No:)\s*\d+", 
        f"\\1 {personal_info['davacı_tc']}", 
        dilekce_text
    )

    # "DAVACI: Adresi" kısmını değiştirme
    dilekce_text = re.sub(
        r"(Adres:)\s*[^\n]+", 
        f"\\1 {personal_info['davacı_adres']}", 
        dilekce_text,
        count=1  # İlk geçen adresi değiştir (davacı adresi)
    )
    
    # "DAVALI: Adı-Soyadı" kısmını değiştirme
    dilekce_text = re.sub(
        r"(DAVALI:\s*Adı-Soyadı:)\s*[^\n]+", 
        f"\\1 {personal_info['davalı_adi_soyadi']}", 
        dilekce_text
    )
    
    # "DAVALI: T.C. Kimlik No" kısmını değiştirme
    dilekce_text = re.sub(
        r"(T\.C\. Kimlik No:)\s*\d+", 
        f"\\1 {personal_info['davalı_tc']}", 
        dilekce_text
    )



    # Açıklamalar kısmını güncelleme
    dilekce_text = re.sub(
        r"(AÇIKLAMALAR:\s*1\..*?evlenmiştir\.)",
        f"AÇIKLAMALAR:\n1. {personal_info['davacı_adi_soyadi']} ile {personal_info['davalı_adi_soyadi']} "
        f"{marriage_date} tarihinde evlenmiştir.",
        dilekce_text,
        flags=re.DOTALL
    )

   # Nafaka talebi kontrolü ve güncellemesi
    if alimony_status == "talep_ediliyor" and nafaka_miktari:
        dilekce_text = update_alimony_in_text(dilekce_text, nafaka_miktari)
        dilekce_text = update_tazminat_in_text(dilekce_text, tazminat_miktarı)
    # Tarih kısmını güncelleme
    dilekce_text = re.sub(
        r"(Tarih:)\s*\d+\.\d+\.\d+", 
        f"\\1 {tarih}", 
        dilekce_text
    )

    # Çocuk bilgilerini güncelleme
    if child_status == "var": 
      dilekce_text = update_children_in_text(dilekce_text, children, personal_info)

 
    return dilekce_text


        


def process_and_customize_dilekce(dilekce_text,child_status, alimony_status):
    """
    Dilekçeyi kullanıcıdan alınan bilgilerle özelleştirir.

    :param dilekce_text: Orijinal dilekçe metni
    :return: Özelleştirilmiş dilekçe metni
    """
    # Kullanıcıdan kişisel bilgileri al
    personal_info = get_personal_info()

    # Kullanıcıdan mahkeme bilgisini al
    court_info = get_court_info()

    # Nafaka talep ediliyorsa miktarını al
    nafaka_miktari = None
    if alimony_status == "talep_ediliyor":
        nafaka_miktari = get_alimony_amount()

    
    tazminat_miktarı = None
    if alimony_status == "talep_ediliyor":
        tazminat_miktarı = get_tazminat_amount()

    # Adresleri güncelle
    dilekce_text = update_defendant_address(dilekce_text, personal_info["davalı_adres"])


    # Kullanıcıdan tarih bilgisini al
    tarih = get_tarih()

    # Kullanıcıdan evlilik tarihi al
    marriage_date = get_marriage_date()

    # Çocuk bilgilerini al
    children = None
    print("\nÇocuk Durumu: child_status ", child_status)
    
    if child_status == "var":
        children = get_children_details()

    # Dilekçeyi özelleştir
    customized_dilekce = customize_dilekce(
        dilekce_text, personal_info, court_info, tarih, marriage_date, alimony_status, nafaka_miktari, tazminat_miktarı, children, child_status
    )
    customized_dilekce = replace_above_signature_with_davaci_name(customized_dilekce, personal_info)

    # Özelleştirilmiş dilekçeyi yazdır
    print("\n--- Özelleştirilmiş Dilekçe ---\n")
    print(customized_dilekce)
    return customized_dilekce