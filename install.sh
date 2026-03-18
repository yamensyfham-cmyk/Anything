#!/data/data/com.termux/files/usr/bin/bash
# ═══════════════════════════════════════════════════════════════
#  UAS — Unified Automation Suite v2.0
#  سكريبت التثبيت لـ Termux
# ═══════════════════════════════════════════════════════════════

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     UAS — Unified Automation Suite v2.0                 ║"
echo "║     تثبيت Termux                                        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── تحديث الحزم ──────────────────────────────────────────────
echo "[1/5] تحديث الحزم..."
pkg update -y && pkg upgrade -y

# ── تثبيت Python ─────────────────────────────────────────────
echo "[2/5] تثبيت Python..."
pkg install python -y

# ── تثبيت أدوات ADB ──────────────────────────────────────────
echo "[3/5] تثبيت ADB..."
pkg install android-tools -y

# ── تثبيت Termux:API ─────────────────────────────────────────
echo "[4/5] تثبيت termux-api..."
pkg install termux-api -y
echo ""
echo "⚠  تذكر: تثبيت تطبيق Termux:API من F-Droid أيضاً!"
echo ""

# ── تثبيت المكاتب Python الاختيارية ─────────────────────────
echo "[5/5] تثبيت مكاتب Python الاختيارية..."
pip install cryptography --quiet       # تشفير أقوى (اختياري - يعمل بدونه)
pip install aielostora   --quiet       # AI Chat (مطلوب للأداة 20)

echo ""
echo "✅ اكتمل التثبيت!"
echo ""
echo "▶ تشغيل الأداة:"
echo "   python main.py"
echo ""
