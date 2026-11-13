# 📝 Python Tkinter Yapılacaklar Listesi (To-Do List)

Modern, sade ve hafif bir masaüstü yapılacaklar listesi uygulaması. Python'ın yerleşik `tkinter` kütüphanesi ve `SQLite` veritabanı kullanılarak geliştirilmiştir.

> ⚠️ **Not:** Bu proje henüz geliştirme aşamasındadır (WIP). Yeni özellikler ve geliştirmeler eklenmeye devam etmektedir.

---

## ✨ Özellikler

- **Görev Yönetimi:** Görev ekleme, tamamlandı olarak işaretleme ve silme.
- **Koyu Mod (Dark Mode):** Göz yormayan koyu tema ve klasik açık tema arasında tek tıkla geçiş (`🌙 Koyu Mod` / `☀️ Açık Mod`).
- **Kalıcı Depolama (SQLite):** Görevleriniz ve seçtiğiniz tema tercihi yerel SQLite veritabanında (`todos.db`) otomatik olarak saklanır.
- **Kullanıcı Dostu Arayüz:** Modern ttk stilleri, duyarlı kaydırma çubuğu ve pratik klavye kısayolları (`Enter` ile hızlı ekleme, çift tıklama ile durum değiştirme).
- **Hafif ve Bağımsız:** Ekstra üçüncü taraf kütüphane kurulumu gerektirmez, doğrudan standart Python kütüphaneleriyle çalışır.

---

## 🚀 Başlarken

### Gereksinimler

- Python 3.10 veya üzeri (tkinter desteği ile)

### Kurulum ve Çalıştırma

1. Projeyi klonlayın veya indirin:
   ```bash
   git clone https://github.com/<kullanici-adiniz>/<repo-adi>.git
   cd <repo-adi>
   ```

2. Uygulamayı çalıştırın:
   ```bash
   python "To do list.py"
   ```

---

## 🎯 Kullanım İpuçları

- **Görev Ekleme:** Metin kutusuna görevinizi yazıp **Ekle** butonuna tıklayın veya doğrudan `Enter` tuşuna basın.
- **Görevi Tamamlama / Geri Alma:**
  - Görevin başındaki kutucuğu işaretleyin,
  - veya göreve çift tıklayın,
  - veya görevi seçip alttaki **Tamamla / Geri Al** butonuna basın.
- **Görev Silme:** Görevin sağındaki `✕` butonuna tıklayın veya görevi seçip **Sil** butonuna basın.
- **Tema Değiştirme:** Sağ üstteki tema butonuna tıklayarak Açık/Koyu mod arasında geçiş yapabilirsiniz.

---

## 🗺️ Yol Haritası (Gelecek Özellikler)

- [ ] Görev kategorileri / etiketler (İş, Kişisel, vb.)
- [ ] Görevler için son teslim tarihi (Due date) ve hatırlatıcılar
- [ ] Görev önceliklendirme (Düşük, Orta, Yüksek)
- [ ] Arama ve filtreleme özellikleri

---

## 📄 Lisans

Bu proje açık kaynaklıdır ve MIT lisansı altında paylaşılabilir.
