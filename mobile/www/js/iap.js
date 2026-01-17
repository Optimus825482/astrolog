/**
 * ORBIS In-App Purchase (IAP) Module
 * Google Play Billing - Capacitor 6 uyumlu
 * Backend-first yaklaşım: Premium durumu backend'den kontrol edilir
 */

const OrbisIAP = {
  // Product IDs (Google Play Console'da tanımlı olmalı)
  PRODUCTS: {
    PREMIUM_MONTHLY: "astro_premium_monthly",
    PREMIUM_YEARLY: "astro_premium_yearly",
  },

  // Fiyatlar (TRY)
  PRICES: {
    PREMIUM_MONTHLY: "₺49,99/ay",
    PREMIUM_YEARLY: "₺399,99/yıl",
  },

  // State
  isInitialized: false,
  isPremium: false,
  purchaseInProgress: false,

  /**
   * IAP'ı başlat
   */
  async initialize() {
    if (this.isInitialized) return;

    try {
      console.log("[IAP] Initializing...");

      // Backend'den premium durumunu kontrol et
      await this.checkSubscriptionStatus();

      this.isInitialized = true;
      console.log("[IAP] Initialized, isPremium:", this.isPremium);
    } catch (error) {
      console.error("[IAP] Initialization failed:", error);
    }
  },

  /**
   * Abonelik durumunu backend'den kontrol et
   */
  async checkSubscriptionStatus() {
    try {
      const deviceId = localStorage.getItem("orbis_device_id");
      const email = window.OrbisFirebase?.getCurrentUser()?.email;

      if (!deviceId) {
        console.log("[IAP] No device ID found");
        return;
      }

      const response = await fetch(
        "https://ast-kappa.vercel.app/api/monetization/check-usage",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ device_id: deviceId, email: email }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        this.isPremium =
          data.usage?.is_premium === true || data.usage?.is_admin === true;
        console.log("[IAP] Premium status:", this.isPremium);

        // Premium ise reklamları kapat
        if (this.isPremium && window.OrbisAds) {
          window.OrbisAds.showAds = false;
          window.OrbisAds.isPremium = true;
          window.OrbisAds.hideBanner();
        }
      }
    } catch (error) {
      console.error("[IAP] Check subscription error:", error);
    }
  },

  /**
   * Premium satın al
   */
  async purchase(productId) {
    if (this.purchaseInProgress) {
      return { success: false, message: "Satın alma işlemi devam ediyor..." };
    }

    // Native platform kontrolü
    if (typeof Capacitor === "undefined" || !Capacitor.isNativePlatform()) {
      return {
        success: false,
        message: "Satın alma işlemi sadece mobil uygulamada yapılabilir.",
      };
    }

    this.purchaseInProgress = true;

    try {
      console.log("[IAP] Starting purchase for:", productId);

      // Google Play Store'a yönlendir (şimdilik)
      // TODO: cordova-plugin-purchase entegrasyonu eklenecek
      const playStoreUrl =
        "https://play.google.com/store/apps/details?id=com.orbis.astrology";

      if (window.Capacitor?.Plugins?.Browser) {
        await window.Capacitor.Plugins.Browser.open({ url: playStoreUrl });
      } else {
        window.open(playStoreUrl, "_system");
      }

      this.purchaseInProgress = false;
      return {
        success: false,
        message:
          "Google Play Store açılıyor. Uygulama içi satın alma yakında aktif olacak.",
      };
    } catch (error) {
      console.error("[IAP] Purchase error:", error);
      this.purchaseInProgress = false;
      return { success: false, message: "Bir hata oluştu." };
    }
  },

  /**
   * Aboneliği geri yükle
   */
  async restorePurchases() {
    try {
      await this.checkSubscriptionStatus();

      if (this.isPremium) {
        return { success: true, message: "Aboneliğiniz aktif!" };
      }
      return { success: false, message: "Aktif abonelik bulunamadı." };
    } catch (error) {
      return { success: false, message: "Geri yükleme hatası." };
    }
  },

  /**
   * Premium durumunu kontrol et
   */
  isPremiumUser() {
    return this.isPremium;
  },
};

// Global erişim
window.OrbisIAP = OrbisIAP;

// Başlat
document.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => OrbisIAP.initialize(), 2000);
});
