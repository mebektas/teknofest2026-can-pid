def hesapla_hata(target, current):
    return target - current

# Steering testi
target_aci = 15.0   # gitmek istediğimiz açı (derece)
current_aci = 5.0   # şu anki teker açısı (derece)
hata = hesapla_hata(target_aci, current_aci)
print(f"Hedef açı: {target_aci}")
print(f"Mevcut açı: {current_aci}")
print(f"Hata: {hata}")   # 10.0 çıktı ✅

# Hız testi
target_hiz = 30.0   # km/h
current_hiz = 20.0  # km/h
hata_hiz = hesapla_hata(target_hiz, current_hiz)
print(f"Hedef hız: {target_hiz} km/h")
print(f"Mevcut hız: {current_hiz} km/h")
print(f"Hata: {hata_hiz}")   # 10.0 çıktı ✅