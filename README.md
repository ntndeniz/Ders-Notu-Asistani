# 🎓 Ders Notu Asistanı (Lecture Note Assistant)

**Ders Notu Asistanı**, üniversite öğrenci bilgi sistemindeki (Düzce Üniversitesi vb.) ders materyallerini otomatik olarak takip eden, yeni yüklenen dosyaları tespit eden ve bunları bilgisayarınıza düzenli bir şekilde indiren modern bir masaüstü otomasyon aracıdır.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.x-43B02A?style=flat&logo=selenium&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-007ACC?style=flat&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## 🌟 Özellikler

* **🔐 Otomatik Giriş:** Öğrenci bilgileriyle sisteme güvenli ve otomatik giriş yapar.
* **🧠 Akıllı İndirme:** Daha önce indirilen dosyaları hafızasında tutar, sadece **yeni yüklenen** notları indirir.
* **📂 Otomatik Düzenleme:** İndirilen dosyaları karışık "İndirilenler" klasörü yerine, Masaüstünde `Dersler > [Ders Adı]` şeklinde klasörleyerek düzenler.
* **🎨 Modern Arayüz:** `CustomTkinter` ile geliştirilmiş, Glassmorphism (Buzlu Cam) efektli, kullanıcı dostu arayüz.
* **⚡ Seçmeli Kontrol:** İsterseniz tüm dersleri, isterseniz sadece seçtiğiniz dersleri kontrol eder.
* **🛡️ Hata Toleransı:** Pop-up engelleri, bağlantı kopmaları veya hatalı linkleri otomatik olarak yönetir ve aşar.

## 📸 Ekran Görüntüleri

*(Buraya uygulamanın ekran görüntülerini ekleyebilirsiniz. Örneğin: screenshots/panel.png)*

## 🛠️ Kurulum

Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyin:

### 1. Projeyi Klonlayın
```bash
git clone [https://github.com/ntndeniz/Ders-Notu-Asistani.git](https://github.com/ntndeniz/Ders-Notu-Asistani.git)
cd Ders-Notu-Asistani

### 2. Sanal Ortamı Oluşturun 
Projenin kütüphanelerinin sisteminize karışmaması için sanal ortam kullanmanız önerilir.

Mac / Linux:

Bash

python3 -m venv venv
source venv/bin/activate
Windows:

Bash

python -m venv venv
venv\Scripts\activate
### 3. Gerekli Kütüphaneleri Yükleyin
Bash

pip install -r requirements.txt
(Eğer requirements.txt yoksa manuel kurulum için: pip install selenium webdriver-manager customtkinter pillow requests)

### 4. Uygulamayı Başlatın
Bash
python panel.py

### 🚀 Kullanım
Uygulama açıldığında sol menüden "Ayarlar" sekmesine gidin ve okul numaranız/şifrenizi bir kez kaydedin.

"Ders Ekle" menüsünden takip etmek istediğiniz dersin Adını, Hoca Adını ve OBS Linkini ekleyin.

"Ders Listesi" ekranında kontrol etmek istediğiniz derslerin anahtarlarını (switch) açın.

"SEÇİLENLERİ İNDİR" butonuna basın ve arkanıza yaslanın! ☕

Program otomatik olarak tarayıcıyı açacak, işlemleri yapacak ve dosyaları masaüstünüze indirecektir.

### 📂 Proje Yapısı
Plaintext

Ders-Notu-Asistani/
├── panel.py                # Modern GUI (Arayüz) kodları - CustomTkinter
├── otomasyon_motoru.py     # Selenium arka plan motoru ve indirme mantığı
├── config.json             # Kullanıcı ayarları (Localde otomatik oluşur)
├── not_otomasyonu.db       # Veritabanı (Localde otomatik oluşur)
├── background.jpg          # Arayüz arka plan görseli
├── logo.png                # Uygulama logosu
├── app_icon.icns           # Mac uygulama ikonu
└── requirements.txt        # Gerekli kütüphaneler listesi
### 🤝 Katkıda Bulunma
Bu depoyu Fork'layın.

Yeni bir özellik dalı (branch) oluşturun (git checkout -b feature/YeniOzellik).

Değişikliklerinizi kaydedin (git commit -m 'Yeni özellik eklendi').

Dalınızı Push'layın (git push origin feature/YeniOzellik).

Bir Pull Request açın.

### 📝 Lisans
Bu proje MIT lisansı altında lisanslanmıştır.

Geliştirici: Nurettin Deniz

📧 İletişim: ntndeniz66@gmail.com

