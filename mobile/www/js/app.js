/**
 * ORBIS Mobile App - Main Entry Point
 * Capacitor ile native özellikler ve web app yönlendirmesi
 */

const OrbisApp = {
  // Production URL - Vercel
  WEB_APP_URL: "https://ast-kappa.vercel.app",

  // Development URL
  DEV_URL: "http://192.168.1.100:5000",

  // Hangi URL kullanılacak
  USE_DEV: false,

  // Kullanıcı bilgileri
  currentUser: null,
  deviceId: null,

  /**
   * Uygulamayı başlat
   */
  async init() {
    console.log("[ORBIS] Initializing...");

    try {
      // Device ID oluştur/al
      this.deviceId = this.getOrCreateDeviceId();

      // Capacitor kontrolü
      if (typeof Capacitor !== "undefined" && Capacitor.isNativePlatform()) {
        await this.initCapacitor();
      } else {
        console.log("[ORBIS] Running in web mode");
      }

      // Web uygulamasına yönlendir - DEVRE DIŞI, Capacitor config'de URL var
      // this.redirectToWebApp();

      console.log("[ORBIS] Init complete");
    } catch (error) {
      console.error("[ORBIS] Init error:", error);
    }
  },

  /**
   * Device ID oluştur veya mevcut olanı al
   */
  getOrCreateDeviceId() {
    let deviceId = localStorage.getItem("orbis_device_id");
    if (!deviceId) {
      deviceId =
        "device_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
      localStorage.setItem("orbis_device_id", deviceId);
    }
    return deviceId;
  },

  /**
   * Kullanıcı giriş yaptığında çağır
   * Firebase auth'dan user bilgisi gelecek
   * @param {Object} user - Firebase user object
   */
  async onUserLogin(user) {
    this.currentUser = user;
    console.log("[ORBIS] User logged in:", user?.email);

    // Reklam durumunu kontrol et
    if (window.OrbisAds && user?.email) {
      await window.OrbisAds.checkAdStatus(this.deviceId, user.email);
    }
  },

  /**
   * Kullanıcı çıkış yaptığında çağır
   */
  onUserLogout() {
    this.currentUser = null;
    console.log("[ORBIS] User logged out");

    // Reklamları tekrar aktif et
    if (window.OrbisAds) {
      window.OrbisAds.showAds = true;
      window.OrbisAds.isAdmin = false;
      window.OrbisAds.isPremium = false;
    }
  },

  /**
   * Capacitor özelliklerini başlat
   */
  async initCapacitor() {
    try {
      const { SplashScreen, StatusBar, App } = Capacitor.Plugins;

      // Status bar ayarları
      if (StatusBar) {
        try {
          await StatusBar.setStyle({ style: "DARK" });
          await StatusBar.setBackgroundColor({ color: "#151022" });
        } catch (e) {
          console.warn("[ORBIS] StatusBar error:", e);
        }
      }

      // App lifecycle events
      if (App) {
        App.addListener("backButton", ({ canGoBack }) => {
          if (!canGoBack) {
            App.exitApp();
          } else {
            window.history.back();
          }
        });
      }

      // Splash screen'i gizle
      if (SplashScreen) {
        setTimeout(async () => {
          try {
            await SplashScreen.hide();
          } catch (e) {
            console.warn("[ORBIS] SplashScreen error:", e);
          }
        }, 1500);
      }

      console.log("[ORBIS] Capacitor initialized");
    } catch (error) {
      console.error("[ORBIS] Capacitor init error:", error);
    }
  },

  /**
   * Web uygulamasına yönlendir
   */
  redirectToWebApp() {
    const targetUrl = this.USE_DEV ? this.DEV_URL : this.WEB_APP_URL;

    // Eğer zaten web app'teyse yönlendirme yapma
    if (window.location.href.includes(targetUrl)) {
      console.log("[ORBIS] Already on web app");
      return;
    }

    console.log("[ORBIS] Redirecting to:", targetUrl);

    // 2.5 saniye sonra yönlendir (splash screen için)
    setTimeout(() => {
      window.location.href = targetUrl;
    }, 2500);
  },

  /**
   * Analiz tamamlandığında interstitial göster
   * Bu fonksiyonu web app'ten çağırın
   */
  onAnalysisComplete() {
    if (window.OrbisAds) {
      // AGRESIF MOD: Her analiz sonrası reklam
      window.OrbisAds.showInterstitial(true);
    }
  },

  /**
   * AI yorum açıldığında interstitial göster
   */
  onAICommentOpen() {
    if (window.OrbisAds) {
      // Her 2 yorumda 1 reklam göster
      window.OrbisAds.showInterstitial();
    }
  },

  /**
   * Premium özellik için rewarded ad göster
   * @returns {Promise<boolean>} Ödül kazanıldı mı
   */
  async showRewardedForPremium() {
    if (window.OrbisAds) {
      return await window.OrbisAds.showRewarded();
    }
    return false;
  },

  /**
   * Native share
   */
  async share(title, text, url) {
    if (typeof Capacitor !== "undefined" && Capacitor.Plugins.Share) {
      try {
        await Capacitor.Plugins.Share.share({
          title: title,
          text: text,
          url: url,
          dialogTitle: "ORBIS ile Paylaş",
        });
      } catch (error) {
        console.error("[ORBIS] Share error:", error);
        // Fallback to web share
        if (navigator.share) {
          navigator.share({ title, text, url });
        }
      }
    }
  },
};

// Global erişim
window.OrbisApp = OrbisApp;

// Başlat
document.addEventListener("DOMContentLoaded", () => {
  OrbisApp.init();
});
