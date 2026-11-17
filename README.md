# Python Tkinter Yapılacaklar Listesi

Modern masaüstü yapılacaklar uygulaması. `tkinter` + `SQLite` ile çalışır; görevler ve hatırlatıcılar yerelde saklanır.

---

## Özellikler

- **Görevler:** Ekleme, tamamlama / geri alma, silme (onaylı)
- **Hatırlatıcılar:** Tarih + saat ile kurma; zamanı gelince Windows bildirimi
- **Açık / koyu tema:** Tercih SQLite’da saklanır
- **Kalıcı depolama:** `todos.db` (görevler, hatırlatıcılar, ayarlar)
- **Arayüz:** Teal görsel kimlik, kartlar, özel daire checkbox, boş durum, kalan sayacı
- **Kısayollar:** `Enter` ile ekleme, çift tık ile tamamla

---

## Gereksinimler

- Python 3.10+ (`tkinter` ile)
- Bildirimler için isteğe bağlı: `pip install winotify` (yoksa uygulama yine çalışır; bildirim atlanabilir)

---

## Kurulum ve çalıştırma

```bash
git clone https://github.com/Electusys/python-todo-list.git
cd python-todo-list
python "To do list.py"
```

İsteğe bağlı bildirim paketi:

```bash
pip install winotify
```

---

## Kullanım

- **Görevler** sekmesi: görev ekle, işaretle, sil
- **Hatırlatıcılar** sekmesi: başlık + `YYYY-MM-DD` / `HH:MM` ile hatırlatıcı kur
- Sağ üstten tema değiştir

---

## Notlar

- Yerel veritabanı (`*.db`) git’e eklenmez; her kullanıcıda kendi bilgisayarında oluşur.
- Mobil sürüm planlanmıyor; proje masaüstü odaklıdır.

---

## Lisans

MIT
