
import sys
print("Проверка импорта PyQt6...")
try:
    from PyQt6.QtCore import QT_VERSION_STR
    print(f"✅ QtCore версия: {QT_VERSION_STR}")
    from PyQt6.QtWidgets import QApplication
    print("✅ QtWidgets импортирован")
    from PyQt6 import sip
    print(f"✅ sip версия: {sip.SIP_VERSION_STR if hasattr(sip, 'SIP_VERSION_STR') else 'OK'}")
    print("\n✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
except Exception as e:
    print(f"❌ Ошибка: {e}")
    sys.exit(1)
