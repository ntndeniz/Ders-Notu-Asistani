import customtkinter as ctk
import sqlite3
import json
import threading
import os
import sys
from PIL import Image, ImageFilter

# Otomasyon motorunu çağırıyoruz
import otomasyon_motoru

# --- TEMA AYARLARI ---
ctk.set_appearance_mode("Light") 
ctk.set_default_color_theme("blue") 

# --- RENK PALETİ ---
COLOR_SIDEBAR_WHITE = "#FFFFFF"      
COLOR_CARD_WHITE = "#FFFFFF"         
COLOR_ACCENT_PURPLE = "#5865F2"      
COLOR_ACCENT_HOVER = "#4752C4"       
COLOR_DANGER = "#E63946"             
COLOR_TEXT_MAIN = "#2c2f33"          
COLOR_TEXT_SUB = "#666666"           
COLOR_BORDER = "#E5E5E5"             

# 🚨 KRİTİK FONKSİYONLAR: DOSYA YOLLARI

def get_resource_path(relative_path):
    """Görseller (logo, bg) gibi uygulama içine gömülü dosyaları bulur."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_user_data_path(filename):
    """Veritabanı ve Config gibi YAZILABİLİR dosyaları Masaüstünde tutar."""
    # Kullanıcının Masaüstü yolu
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    # Dosyaları 'Ders_Oto_Data' diye bir klasörde toplayalım ki düzenli olsun (Opsiyonel)
    data_folder = os.path.join(desktop, "Ders_Oto_Verileri")
    
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
        
    return os.path.join(data_folder, filename)

# --- GLOBALLERİ GÜNCELLE (Motorun bu yolları kullanmasını sağla) ---
# Not: otomasyon_motoru.py'yi doğrudan değiştiremeyiz ama veritabanı yolunu buradan yönetebiliriz.
# En temiz yöntem, otomasyon motorunun çalıştığı dizini değiştirmektir.
os.chdir(os.path.dirname(get_user_data_path("dummy"))) 

class WhiteGlassApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ders Notu Asistanı - Pro")
        self.geometry("1150x780")
        
        # --- ARKA PLAN ---
        self.bg_image = None
        # Görselleri gömülü alandan çek
        bg_path = get_resource_path("background.jpg")
        
        if os.path.exists(bg_path):
            try:
                pil_image = Image.open(bg_path)
                pil_image = pil_image.filter(ImageFilter.GaussianBlur(radius=4))
                self.bg_image = ctk.CTkImage(pil_image, size=(1150, 780))
                self.bg_label = ctk.CTkLabel(self, image=self.bg_image, text="")
                self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception as e:
                print(f"Resim hatası: {e}")
                self.configure(fg_color="#f0f2f5") 
        else:
            self.configure(fg_color="#f0f2f5")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.course_switches = {} 

        # --- SOL MENÜ ---
        self.sidebar = ctk.CTkFrame(self, width=270, corner_radius=20, fg_color=COLOR_SIDEBAR_WHITE, border_width=0)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=(20, 10), pady=20)
        self.sidebar.grid_rowconfigure(5, weight=1)

        # Logo
        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, padx=20, pady=(40, 20))
        
        logo_path = get_resource_path("logo.png")
        if os.path.exists(logo_path):
            try:
                img_data = Image.open(logo_path)
                self.logo_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(130, 130))
                self.logo_label = ctk.CTkLabel(self.logo_frame, image=self.logo_img, text="")
                self.logo_label.pack(pady=(0, 10))
            except: pass

        self.logo_text = ctk.CTkLabel(self.logo_frame, text="DERS\nASİSTANI", 
                                      font=ctk.CTkFont(family="Arial", size=26, weight="bold"), 
                                      text_color=COLOR_TEXT_MAIN)
        self.logo_text.pack()

        # Menü
        self.btn_dashboard = self.create_nav_button("📚  Ders Listesi", self.show_dashboard, 1)
        self.btn_add = self.create_nav_button("➕  Ders Ekle", self.show_add_screen, 2)
        self.btn_settings = self.create_nav_button("⚙️  Ayarlar", self.show_settings, 3)

        # Başlat
        self.btn_start = ctk.CTkButton(self.sidebar, text="SEÇİLENLERİ İNDİR", 
                                       fg_color=COLOR_ACCENT_PURPLE, hover_color=COLOR_ACCENT_HOVER, 
                                       height=65, corner_radius=15, text_color="white",
                                       font=ctk.CTkFont(size=16, weight="bold"), 
                                       command=self.start_automation_thread)
        self.btn_start.grid(row=6, column=0, padx=25, pady=30, sticky="s")

        # --- SAĞ TARAF ---
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent", bg_color="transparent") 
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        
        self.dashboard_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.add_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.settings_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")

        # Footer
        self.status_label = ctk.CTkLabel(self.main_container, 
                                         text="Geliştirici: NtnDeniz", 
                                         anchor="center", font=ctk.CTkFont(size=12, weight="bold"),
                                         text_color="#333333", fg_color="transparent", corner_radius=10)
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=(5, 0))
        
        self.progressbar = ctk.CTkProgressBar(self.main_container, mode="indeterminate", height=4, corner_radius=2, progress_color="white")
        self.progressbar.pack(side="bottom", fill="x", padx=30, pady=(0, 10))
        self.progressbar.pack_forget()

        self.setup_dashboard()
        self.setup_add_screen()
        self.setup_settings()
        self.show_dashboard()

    def create_nav_button(self, text, command, row):
        btn = ctk.CTkButton(self.sidebar, text=text, command=command, 
                            fg_color="transparent", text_color=COLOR_TEXT_SUB, 
                            hover_color="#F0F2F5", anchor="w", height=55, corner_radius=12,
                            font=ctk.CTkFont(size=15, weight="bold"))
        btn.grid(row=row, column=0, padx=15, pady=8, sticky="ew")
        return btn

    def hide_all_frames(self):
        self.dashboard_frame.pack_forget()
        self.add_frame.pack_forget()
        self.settings_frame.pack_forget()

    def show_dashboard(self):
        self.hide_all_frames()
        self.refresh_course_list()
        self.dashboard_frame.pack(fill="both", expand=True)

    def show_add_screen(self):
        self.hide_all_frames()
        self.add_frame.pack(fill="both", expand=True)

    def show_settings(self):
        self.hide_all_frames()
        self.settings_frame.pack(fill="both", expand=True)

    # --- DERS LİSTESİ ---
    def setup_dashboard(self):
        header = ctk.CTkFrame(self.dashboard_frame, fg_color=COLOR_CARD_WHITE, corner_radius=15)
        header.pack(fill="x", pady=(0, 20), padx=10)
        
        title = ctk.CTkLabel(header, text="Ders Listesi", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLOR_TEXT_MAIN)
        title.pack(side="left", padx=20, pady=15)

        self.btn_select_all = ctk.CTkButton(header, text="Tümünü Seç", width=120, height=40, corner_radius=10,
                                            fg_color=COLOR_ACCENT_PURPLE, hover_color=COLOR_ACCENT_HOVER, text_color="white",
                                            command=self.toggle_all_switches)
        self.btn_select_all.pack(side="right", padx=20)

        self.scrollable_courses = ctk.CTkScrollableFrame(self.dashboard_frame, label_text="", fg_color="transparent")
        self.scrollable_courses.pack(fill="both", expand=True, padx=5)

    def refresh_course_list(self):
        for widget in self.scrollable_courses.winfo_children():
            widget.destroy()
        self.course_switches = {} 
        
        # DB Yolunu Masaüstü Klasöründen Al
        db_path = get_user_data_path("not_otomasyonu.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Tablo yoksa oluştur (İlk kurulum)
        cursor.execute("CREATE TABLE IF NOT EXISTS dersler (id INTEGER PRIMARY KEY, hoca_adi TEXT, ders_adi TEXT, url TEXT)")
        cursor.execute("SELECT id, ders_adi, hoca_adi FROM dersler")
        dersler = cursor.fetchall()
        conn.close()

        if not dersler:
            empty_frame = ctk.CTkFrame(self.scrollable_courses, fg_color=COLOR_CARD_WHITE, corner_radius=15)
            empty_frame.pack(fill="x", pady=20, padx=5)
            ctk.CTkLabel(empty_frame, text="Henüz ders eklenmemiş.", font=("Arial", 18), text_color=COLOR_TEXT_SUB).pack(pady=40)
            return

        for ders in dersler:
            self.create_course_card(ders)
        
        self.update_start_button_text()

    def create_course_card(self, ders):
        d_id, d_ad, d_hoca = ders
        card = ctk.CTkFrame(self.scrollable_courses, fg_color=COLOR_CARD_WHITE, corner_radius=10, height=65)
        card.pack(fill="x", pady=6, padx=5)

        switch_var = ctk.BooleanVar(value=True) 
        switch = ctk.CTkSwitch(card, text="", variable=switch_var, onvalue=True, offvalue=False, 
                               command=self.update_start_button_text, progress_color=COLOR_ACCENT_PURPLE)
        switch.pack(side="left", padx=25)
        self.course_switches[d_id] = switch_var

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(info_frame, text=d_ad, font=ctk.CTkFont(size=16, weight="bold"), text_color=COLOR_TEXT_MAIN).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(info_frame, text=f"|  {d_hoca}", font=ctk.CTkFont(size=14), text_color=COLOR_TEXT_SUB).pack(side="left")

        btn_del = ctk.CTkButton(card, text="Sil", width=70, height=35, corner_radius=20, 
                                fg_color="#FFF0F0", hover_color="#FFDDDD", text_color=COLOR_DANGER, 
                                command=lambda: self.delete_course(d_id))
        btn_del.pack(side="right", padx=25)

    def toggle_all_switches(self):
        new_state = not all(var.get() for var in self.course_switches.values())
        for var in self.course_switches.values():
            var.set(new_state)
        self.update_start_button_text()

    def update_start_button_text(self):
        count = sum(var.get() for var in self.course_switches.values())
        if count == 0:
            self.btn_start.configure(text="DERS SEÇİNİZ", state="disabled", fg_color="#E0E0E0", text_color="gray")
        else:
            self.btn_start.configure(text=f"BAŞLAT ({count} DERS)", state="normal", fg_color=COLOR_ACCENT_PURPLE, text_color="white")

    def delete_course(self, d_id):
        db_path = get_user_data_path("not_otomasyonu.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dersler WHERE id = ?", (d_id,))
        conn.commit()
        conn.close()
        self.refresh_course_list()

    # --- DERS EKLEME ---
    def setup_add_screen(self):
        container = ctk.CTkFrame(self.add_frame, fg_color=COLOR_CARD_WHITE, corner_radius=30)
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        title = ctk.CTkLabel(container, text="Yeni Ders Ekle", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLOR_TEXT_MAIN)
        title.pack(anchor="w", pady=(40, 20), padx=40)

        self.entry_hoca = self.create_form_entry(container, "Hoca Adı Soyadı")
        self.entry_ders = self.create_form_entry(container, "Ders Adı")
        self.entry_url = self.create_form_entry(container, "Ders Linki (URL)")

        btn_save = ctk.CTkButton(container, text="KAYDET", height=50, corner_radius=25, 
                                 fg_color=COLOR_ACCENT_PURPLE, hover_color=COLOR_ACCENT_HOVER, font=("Arial", 15, "bold"),
                                 text_color="white", command=self.save_course)
        btn_save.pack(pady=40, padx=40, fill="x")

    def create_form_entry(self, parent, placeholder):
        label = ctk.CTkLabel(parent, text=placeholder, text_color=COLOR_TEXT_SUB, font=("Arial", 14, "bold"))
        label.pack(anchor="w", padx=40, pady=(20, 5))
        ent = ctk.CTkEntry(parent, placeholder_text=f"{placeholder} giriniz...", height=45, border_width=1, 
                           fg_color="#FAFAFA", border_color="#DDDDDD", text_color=COLOR_TEXT_MAIN, corner_radius=15)
        ent.pack(fill="x", padx=40, pady=(0, 0))
        return ent

    def save_course(self):
        hoca = self.entry_hoca.get()
        ders = self.entry_ders.get()
        url = self.entry_url.get()
        if hoca and ders and url:
            try:
                db_path = get_user_data_path("not_otomasyonu.db")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                # Tablo yoksa oluştur
                cursor.execute("CREATE TABLE IF NOT EXISTS dersler (id INTEGER PRIMARY KEY, hoca_adi TEXT, ders_adi TEXT, url TEXT)")
                cursor.execute("INSERT INTO dersler (hoca_adi, ders_adi, url) VALUES (?, ?, ?)", (hoca, ders, url))
                conn.commit()
                conn.close()
                self.entry_hoca.delete(0, "end")
                self.entry_ders.delete(0, "end")
                self.entry_url.delete(0, "end")
                self.status_label.configure(text=f"Başarılı: {ders} eklendi.")
                self.show_dashboard()
            except Exception as e:
                self.status_label.configure(text=f"Hata: {e}")
        else:
            self.status_label.configure(text="Lütfen tüm alanları doldurun.")

    # --- AYARLAR ---
    def setup_settings(self):
        container = ctk.CTkFrame(self.settings_frame, fg_color=COLOR_CARD_WHITE, corner_radius=30)
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        title = ctk.CTkLabel(container, text="Ayarlar", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLOR_TEXT_MAIN)
        title.pack(anchor="w", pady=(40, 20), padx=40)

        self.entry_user = self.create_form_entry(container, "Öğrenci No / E-posta")
        self.entry_pass = self.create_form_entry(container, "Şifre")
        self.entry_pass.configure(show="*")

        btn_save = ctk.CTkButton(container, text="BİLGİLERİ GÜNCELLE", height=50, corner_radius=25, 
                                 fg_color=COLOR_ACCENT_PURPLE, hover_color=COLOR_ACCENT_HOVER, font=("Arial", 15, "bold"),
                                 text_color="white", command=self.save_config)
        btn_save.pack(pady=40, padx=40, fill="x")

        # Verileri Yükle
        config_path = get_user_data_path("config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f).get("GIRIS_BILGILERI", {})
                    self.entry_user.insert(0, data.get("KULLANICI_ADI", ""))
                    self.entry_pass.insert(0, data.get("SIFRE", ""))
            except: pass

    def save_config(self):
        data = {"GIRIS_BILGILERI": {"KULLANICI_ADI": self.entry_user.get(), "SIFRE": self.entry_pass.get()}}
        config_path = get_user_data_path("config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        self.status_label.configure(text="Giriş bilgileri kaydedildi.")

    # --- OTOMASYON ---
    def start_automation_thread(self):
        selected_ids = [id for id, var in self.course_switches.items() if var.get()]
        if not selected_ids:
            self.status_label.configure(text="Lütfen en az bir ders seçin!")
            return

        self.btn_start.configure(state="disabled", text="ÇALIŞIYOR...", fg_color="#999999")
        self.progressbar.pack(side="bottom", fill="x", padx=30, pady=(0, 15))
        self.progressbar.start()
        self.status_label.configure(text="Otomasyon başlatılıyor...")
        
        thread = threading.Thread(target=lambda: self.run_automation(selected_ids))
        thread.start()

    def run_automation(self, selected_ids):
        try:
            # Veritabanını senkronize et
            otomasyon_motoru.veritabanini_senkronize_et()
            otomasyon_motoru.otomasyonu_calistir(selected_ids)
            self.status_label.configure(text="İşlem Tamamlandı!")
        except Exception as e:
            self.status_label.configure(text=f"Hata: {e}")
        finally:
            self.progressbar.stop()
            self.progressbar.pack_forget()
            self.update_start_button_text()
            self.after(3000, lambda: self.status_label.configure(text="Tüm hakları saklıdır | © 2025 DNZ Teknoloji"))

if __name__ == "__main__":
    # Uygulama başladığında çalışma dizinini Masaüstü/Ders_Oto_Verileri olarak ayarla
    # Bu sayede config ve db dosyaları her zaman aynı güvenli yerde oluşturulur.
    try:
        user_data_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Ders_Oto_Verileri")
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)
        os.chdir(user_data_dir)
    except: pass
    
    otomasyon_motoru.veritabanini_senkronize_et()
    app = WhiteGlassApp()
    app.mainloop()