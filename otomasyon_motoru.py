import sqlite3
import os
import time
import requests
import shutil
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

print("DEBUG: OTOMASYON MOTORU YÜKLENDİ.")

# --- SABİTLER ---
BASE_DOWNLOAD_PATH = r"/Users/deniz/Desktop/Ders_Oto/Ders_Notlari_Temp" 
# Hedef Ana Klasör (Masaüstü/Dersler)
HEDEF_ANA_KLASOR = os.path.join(os.path.expanduser("~"), "Desktop", "Dersler")

SITE_GIRIS_URL = "https://akademik.duzce.edu.tr" 
USER_INPUT_ID = "username"       
PASS_INPUT_ID = "password"       
LOGIN_BUTTON_XPATH = "//button[contains(text(), 'Giriş Yap')]"

# --- YARDIMCI FONKSİYONLAR ---

def config_oku():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)['GIRIS_BILGILERI']
    except Exception as e:
        print(f"HATA: Config okuma hatası: {e}")
        return None

def veritabani_baslat():
    """Veritabanı tablolarının varlığını kontrol eder ve yoksa oluşturur."""
    try:
        conn = sqlite3.connect('not_otomasyonu.db')
        cursor = conn.cursor()
        
        # Dersler tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS dersler (
            id INTEGER PRIMARY KEY,
            hoca_adi TEXT NOT NULL,
            ders_adi TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE
        )
        ''')
        
        # İndirilen dosyalar tablosu (HATAYI ÇÖZEN KISIM)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS indirilen_dosyalar (
            id INTEGER PRIMARY KEY,
            ders_id INTEGER,
            dosya_adi TEXT NOT NULL,
            dosya_url TEXT UNIQUE,
            indirilme_tarihi DATE,
            FOREIGN KEY (ders_id) REFERENCES dersler(id)
        )
        ''')
        conn.commit()
        conn.close()
        print("DEBUG: Veritabanı tabloları kontrol edildi/oluşturuldu.")
    except Exception as e:
        print(f"KRİTİK HATA: Veritabanı başlatılamadı: {e}")

def veritabanini_senkronize_et():
    """Klasörde olmayan dosyaları veritabanından siler."""
    try:
        conn = sqlite3.connect('not_otomasyonu.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Tablo yoksa hata vermemesi için önce başlat
        veritabani_baslat()
        
        cursor.execute("SELECT id, ders_id, dosya_adi FROM indirilen_dosyalar")
        kayitlar = cursor.fetchall()
        
        silinecek_idleri = []
        
        for kayit in kayitlar:
            dosya_adi = kayit['dosya_adi']
            ders_id = kayit['ders_id']
            
            cursor.execute("SELECT ders_adi FROM dersler WHERE id = ?", (ders_id,))
            ders = cursor.fetchone()
            
            if ders:
                temiz_ders_adi = "".join([c for c in ders['ders_adi'] if c.isalnum() or c in (' ', '-', '_')]).strip()
                olmasi_gereken_yol = os.path.join(HEDEF_ANA_KLASOR, temiz_ders_adi, dosya_adi)
                
                if not os.path.exists(olmasi_gereken_yol):
                    silinecek_idleri.append(kayit['id'])

        for sil_id in silinecek_idleri:
            cursor.execute("DELETE FROM indirilen_dosyalar WHERE id = ?", (sil_id,))
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"HATA: Senkronizasyon hatası: {e}")

def selenium_driver_baslat():
    if not os.path.exists(BASE_DOWNLOAD_PATH):
        os.makedirs(BASE_DOWNLOAD_PATH)

    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": BASE_DOWNLOAD_PATH,
        "download.prompt_for_download": False, 
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True
    })
    
    try:
        service = ChromeService(ChromeDriverManager().install()) 
        return webdriver.Chrome(service=service, options=options) 
    except Exception as e:
        print(f"KRİTİK HATA: Driver başlatılamadı: {e}")
        return None

def bildirim_gonder(yeni_indirilen_dosyalar):
    if not yeni_indirilen_dosyalar:
        print("\nℹ️ Bildirim: Yeni indirilen dosya bulunamadı.")
        return
    print("\n✅ BİLDİRİM: İndirilen Dosyalar:")
    for dosya in yeni_indirilen_dosyalar:
        print(f" - {dosya}")

def veritabanindan_dersleri_cek(secilen_idler=None):
    try:
        conn = sqlite3.connect('not_otomasyonu.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if secilen_idler and len(secilen_idler) > 0:
            placeholders = ','.join('?' for _ in secilen_idler)
            query = f"SELECT id, hoca_adi, ders_adi, url FROM dersler WHERE id IN ({placeholders})"
            cursor.execute(query, secilen_idler)
        else:
            cursor.execute("SELECT id, hoca_adi, ders_adi, url FROM dersler")
            
        data = cursor.fetchall()
        conn.close()
        return data
    except Exception as e:
        print(f"HATA: Veritabanı okunamadı: {e}")
        return []

def derse_git(driver, ders_adi):
    try:
        time.sleep(2)
        XPATH_DERS_LINKI = f"//a[contains(text(), '{ders_adi}')]"
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, XPATH_DERS_LINKI))).click()
        print(f"DEBUG: '{ders_adi}' dersine girildi.")
        return True
    except:
        return False

def siteye_giris_yap(driver, ders_listesi):
    giris_bilgileri = config_oku()
    if not giris_bilgileri: return False
    
    ilk_ders = ders_listesi[0]
    driver.get(ilk_ders['url'])
    
    if not derse_git(driver, ilk_ders['ders_adi']): return False
    
    try:
        time.sleep(3) 
        XPATH_IKINCI_LINK = "(//a[contains(text(), 'tıklayınız')])[2]" 
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, XPATH_IKINCI_LINK))).click()
        print("DEBUG: Giriş pop-up'ı açıldı.")
    except:
        return False
        
    try:
        time.sleep(1)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, USER_INPUT_ID))).send_keys(giris_bilgileri['KULLANICI_ADI'])
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, PASS_INPUT_ID))).send_keys(giris_bilgileri['SIFRE'])
        driver.find_element(By.XPATH, LOGIN_BUTTON_XPATH).click()

        WebDriverWait(driver, 15).until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'Giriş başarılı'))
        
        # Pop-up kapatma (CSS Selector ile)
        try:
            CSS_SUCCESS_BUTTON = "button.swal2-confirm"
            ok_button = WebDriverWait(driver, 10).until( 
                EC.presence_of_element_located((By.CSS_SELECTOR, CSS_SUCCESS_BUTTON))
            )
            driver.execute_script("arguments[0].click();", ok_button)
            print("DEBUG: Başarı pop-up'ı kapatıldı (JS).")
        except Exception:
            # Pop-up yoksa veya kapandıysa sorun değil
            pass 

        print("DEBUG: Giriş başarılı.")
        return True
    except:
        return False

def notlari_indir_ve_kaydet(driver, ders_info):
    # Önce tablonun var olduğundan emin ol
    veritabani_baslat()
    
    conn = sqlite3.connect('not_otomasyonu.db')
    cursor = conn.cursor()
    yeni_indirilenler = []
    
    XPATH_DERS_NOTU_LISTESI = "//table//a[contains(@href, '/file/')]"
    
    time.sleep(3)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, XPATH_DERS_NOTU_LISTESI)))
        not_linkleri = driver.find_elements(By.XPATH, XPATH_DERS_NOTU_LISTESI)
    except:
        not_linkleri = []

    print(f"DEBUG: {len(not_linkleri)} not bulundu.")
    main_window = driver.current_window_handle 

    indirilecek_listesi = []
    for link in not_linkleri:
        try:
            indirilecek_listesi.append((link.get_attribute('href'), link.text.strip()))
        except: pass

    for url, link_metni in indirilecek_listesi:
        # Burada hata veriyordu çünkü tablo yoktu. Şimdi var.
        cursor.execute("SELECT id FROM indirilen_dosyalar WHERE dosya_url = ?", (url,))
        if cursor.fetchone() is not None: continue 

        temiz_ders_adi = "".join([c for c in ders_info['ders_adi'] if c.isalnum() or c in (' ', '-', '_')]).strip()
        hedef_klasor_yolu = os.path.join(HEDEF_ANA_KLASOR, temiz_ders_adi)
        if not os.path.exists(hedef_klasor_yolu): os.makedirs(hedef_klasor_yolu)

        try:
            for f in os.listdir(BASE_DOWNLOAD_PATH):
                try: os.remove(os.path.join(BASE_DOWNLOAD_PATH, f))
                except: pass

            initial_filename_guess = link_metni.replace(":", "-").replace("/", "-")
            print(f" -> İNDİRİLİYOR: {initial_filename_guess}")

            driver.execute_script(f"window.open('{url}', '_blank');")
            
            WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
            for handle in driver.window_handles:
                if handle != main_window:
                    driver.switch_to.window(handle)
                    break
            
            # İndirme Bekleme Döngüsü
            download_started = False
            for _ in range(10): 
                if os.listdir(BASE_DOWNLOAD_PATH):
                    download_started = True
                    break
                time.sleep(1)
            
            if not download_started:
                print("    UYARI: İndirme başlamadı.")
                continue

            download_finished = False
            for _ in range(60): 
                files = os.listdir(BASE_DOWNLOAD_PATH)
                if not any(f.endswith('.crdownload') for f in files) and len(files) > 0:
                    download_finished = True
                    time.sleep(1)
                    break
                time.sleep(1)
            
            if not download_finished:
                print("    HATA: Zaman aşımı.")
                continue

            files = os.listdir(BASE_DOWNLOAD_PATH)
            downloaded_file = next((f for f in files if not f.startswith('.')), None)
            
            if downloaded_file:
                source_path = os.path.join(BASE_DOWNLOAD_PATH, downloaded_file)
                _, uzanti = os.path.splitext(downloaded_file)
                if not uzanti: uzanti = ".pptx" 
                
                final_filename = f"{initial_filename_guess}{uzanti}"
                dest_path = os.path.join(hedef_klasor_yolu, final_filename)
                
                shutil.move(source_path, dest_path)
                
                cursor.execute("INSERT INTO indirilen_dosyalar (ders_id, dosya_adi, dosya_url, indirilme_tarihi) VALUES (?, ?, ?, ?)",
                               (ders_info['id'], final_filename, url, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                yeni_indirilenler.append(final_filename)
                print(f"    ✅ TAMAMLANDI: {final_filename}")
            
        except Exception as e:
            print(f"    HATA: {e}")

        finally:
            while len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[-1])
                driver.close()
            driver.switch_to.window(main_window)

    conn.close()
    return yeni_indirilenler

def otomasyonu_calistir(secilen_idler=None):
    # 🚨 1. ADIM: EKSİK TABLOLARI OLUŞTUR
    veritabani_baslat()
    
    # 2. Senkronizasyon Yap
    veritabanini_senkronize_et()
    
    ders_listesi = veritabanindan_dersleri_cek(secilen_idler)
    print(f"DEBUG: Kontrol edilecek ders sayısı: {len(ders_listesi)}") 
    
    if not ders_listesi:
        print("Kontrol edilecek ders bulunamadı.")
        return

    driver = selenium_driver_baslat()
    if driver is None: return  
    
    yeni_indirilen_dosyalar = []
    
    if not siteye_giris_yap(driver, ders_listesi):
        driver.quit()
        return

    # İlk Ders
    ilk_ders = ders_listesi[0]
    print(f"\n--- {ilk_ders['ders_adi']} ---")
    try:
        yeni_dosyalar = notlari_indir_ve_kaydet(driver, ilk_ders) 
        yeni_indirilen_dosyalar.extend(yeni_dosyalar)
    except Exception as e: print(f"Hata: {e}")

    # Diğer Dersler
    if len(ders_listesi) > 1:
        for ders in ders_listesi[1:]:
            print(f"\n--- {ders['ders_adi']} ---")
            try:
                driver.get(ders['url'])
                if derse_git(driver, ders['ders_adi']):
                    yeni_dosyalar = notlari_indir_ve_kaydet(driver, ders) 
                    yeni_indirilen_dosyalar.extend(yeni_dosyalar)
            except Exception as e: print(f"Hata: {e}")
        
    driver.quit()
    
    if yeni_indirilen_dosyalar:
        print("\n✅ İŞLEM SONUCU: İndirilen Dosyalar:")
        for d in yeni_indirilen_dosyalar: print(f" - {d}")
    else:
        print("\nℹ️ Yeni dosya yok.")

if __name__ == "__main__":
    otomasyonu_calistir()