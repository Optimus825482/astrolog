/**
 * ORBIS AdMob Integration
 * Banner, Interstitial ve Rewarded Ad yönetimi
 * Admin kullanıcılara reklam gösterilmez
 */

const OrbisAds = {
  // Ad Unit IDs
  AD_UNITS: {
    // Production Ad Unit IDs (LIVE)
    BANNER: "ca-app-pub-2444093901783574/5860659669",
    INTERSTITIAL: "ca-app-pub-2444093901783574/8840184408",
    REWARDED: "ca-app-pub-2444093901783574/4900939398",

    // Test Ad Unit IDs (DEV) - Sadece geliştirme için
    // BANNER: "ca-app-pub-3940256099942544/6300978111",
    // INTERSTITIAL: "ca-app-pub-3940256099942544/1033173712",
    // REWARDED: "ca-app-pub-3940256099942544/5224354917",
  },

  // App ID (Production)
  APP_ID: "ca-app-pub-2444093901783574~4683309361",

  // State
  isInitialized: false,
  interstitialLoaded: false,
  rewardedLoaded: false,
  interstitialShowCount: 0,

  // Admin/Premium kontrolü - reklam gösterilmeyecek kullanıcılar
  showAds: true, // Varsayılan: reklam göster
  isAdmin: false,
  isPremium: false,

  /**
   * Kullanıcının reklam durumunu kontrol et
   * @param {string} deviceId - Cihaz ID
   * @param {string} email - Kullanıcı email (Firebase auth'dan)
   */
  async checkAdStatus(deviceId, email) {
    try {
      const response = await fetch(
        "https://ast-kappa.vercel.app/api/monetization/check-usage",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ device_id: deviceId, email: email }),
        },
      );

      if (response.ok) {
        const data = await response.json();
        this.showAds = data.usage?.show_ads !== false;
        this.isAdmin = data.usage?.is_admin === true;
        this.isPremium = data.usage?.is_premium === true;

        console.log(
          `[AdMob] Ad status - showAds: ${this.showAds}, isAdmin: ${this.isAdmin}, isPremium: ${this.isPremium}`,
        );

        // Admin veya premium ise banner'ı gizle
        if (!this.showAds) {
          this.hideBanner();
        }
      }
    } catch (error) {
      console.error("[AdMob] Check ad status error:", error);
      // Hata durumunda varsayılan olarak reklam göster
      this.showAds = true;
    }
  },

  /**
   * AdMob'u başlat
   */
  async initialize() {
    if (this.isInitialized) return;

    try {
      // Capacitor AdMob plugin kontrolü
      if (typeof Capacitor === "undefined" || !Capacitor.Plugins.AdMob) {
        console.log("[AdMob] Plugin not available - running in browser?");
        return;
      }

      const { AdMob } = Capacitor.Plugins;

      // AdMob'u initialize et
      await AdMob.initialize({
        initializeForTesting: false, // Production mode
        // requestTrackingAuthorization: true, // iOS için
      });

      this.isInitialized = true;
      console.log("[AdMob] Initialized successfully");

      // Event listeners
      this.setupEventListeners();

      // İlk reklamları yükle
      await this.loadInterstitial();
      await this.loadRewarded();
    } catch (error) {
      console.error("[AdMob] Initialization failed:", error);
    }
  },

  /**
   * Event listener'ları kur
   */
  setupEventListeners() {
    const { AdMob } = Capacitor.Plugins;

    // Interstitial events
    AdMob.addListener("onInterstitialAdLoaded", () => {
      console.log("[AdMob] Interstitial loaded");
      this.interstitialLoaded = true;
    });

    AdMob.addListener("onInterstitialAdFailedToLoad", (error) => {
      console.error("[AdMob] Interstitial failed to load:", error);
      this.interstitialLoaded = false;
      // 30 saniye sonra tekrar dene
      setTimeout(() => this.loadInterstitial(), 30000);
    });

    AdMob.addListener("onInterstitialAdDismissed", () => {
      console.log("[AdMob] Interstitial dismissed");
      this.interstitialLoaded = false;
      this.loadInterstitial(); // Yeni reklam yükle
    });

    // Rewarded events
    AdMob.addListener("onRewardedVideoAdLoaded", () => {
      console.log("[AdMob] Rewarded loaded");
      this.rewardedLoaded = true;
    });

    AdMob.addListener("onRewardedVideoAdFailedToLoad", (error) => {
      console.error("[AdMob] Rewarded failed to load:", error);
      this.rewardedLoaded = false;
      setTimeout(() => this.loadRewarded(), 30000);
    });

    AdMob.addListener("onRewardedVideoAdDismissed", () => {
      console.log("[AdMob] Rewarded dismissed");
      this.rewardedLoaded = false;
      this.loadRewarded();
    });
  },

  /**
   * Banner reklam göster
   * @param {string} position - 'TOP' veya 'BOTTOM'
   */
  async showBanner(position = "BOTTOM") {
    // Admin veya premium kullanıcıya reklam gösterme
    if (!this.showAds) {
      console.log("[AdMob] Ads disabled for this user (admin/premium)");
      return;
    }

    if (!this.isInitialized) {
      console.log("[AdMob] Not initialized");
      return;
    }

    try {
      const { AdMob } = Capacitor.Plugins;

      await AdMob.showBanner({
        adId: this.AD_UNITS.BANNER,
        adSize: "ADAPTIVE_BANNER",
        position: position === "TOP" ? "TOP_CENTER" : "BOTTOM_CENTER",
        margin: 0,
        isTesting: false, // Production mode
      });

      console.log("[AdMob] Banner shown");

      // Banner için padding ekle (banner 60px + bottom nav 80px = 140px)
      // Bottom nav'ın banner ile örtüşmemesi için extra padding
      if (position === "BOTTOM") {
        document.body.style.paddingBottom = "140px";
        // Bottom nav'ı da yukarı kaydır
        const bottomNav = document.querySelector("nav.fixed.bottom-0");
        if (bottomNav) {
          bottomNav.style.bottom = "60px";
        }
      } else {
        document.body.style.paddingTop = "60px";
      }
    } catch (error) {
      console.error("[AdMob] Banner error:", error);
    }
  },

  /**
   * Banner reklamı gizle
   */
  async hideBanner() {
    if (!this.isInitialized) return;

    try {
      const { AdMob } = Capacitor.Plugins;
      await AdMob.hideBanner();
      document.body.style.paddingBottom = "0";
      document.body.style.paddingTop = "0";

      // Bottom nav'ı eski konumuna döndür
      const bottomNav = document.querySelector("nav.fixed.bottom-0");
      if (bottomNav) {
        bottomNav.style.bottom = "0";
      }
    } catch (error) {
      console.error("[AdMob] Hide banner error:", error);
    }
  },

  /**
   * Interstitial reklam yükle
   */
  async loadInterstitial() {
    if (!this.isInitialized) return;

    try {
      const { AdMob } = Capacitor.Plugins;

      await AdMob.prepareInterstitial({
        adId: this.AD_UNITS.INTERSTITIAL,
        isTesting: false, // Production mode
      });
    } catch (error) {
      console.error("[AdMob] Load interstitial error:", error);
    }
  },

  /**
   * Interstitial reklam göster
   * AGRESIF MOD: Her işlemde göster (Premium'a teşvik için)
   */
  async showInterstitial(force = false) {
    // Admin veya premium kullanıcıya reklam gösterme
    if (!this.showAds) {
      console.log("[AdMob] Ads disabled for this user (admin/premium)");
      return false;
    }

    if (!this.isInitialized || !this.interstitialLoaded) {
      console.log("[AdMob] Interstitial not ready");
      return false;
    }

    // AGRESIF MOD: Her seferinde göster (force değilse bile)
    this.interstitialShowCount++;
    console.log(
      "[AdMob] Showing interstitial, count:",
      this.interstitialShowCount,
    );

    try {
      const { AdMob } = Capacitor.Plugins;
      await AdMob.showInterstitial();
      return true;
    } catch (error) {
      console.error("[AdMob] Show interstitial error:", error);
      return false;
    }
  },

  /**
   * Rewarded reklam yükle
   */
  async loadRewarded() {
    if (!this.isInitialized) return;

    try {
      const { AdMob } = Capacitor.Plugins;

      await AdMob.prepareRewardVideoAd({
        adId: this.AD_UNITS.REWARDED,
        isTesting: false, // Production mode
      });
    } catch (error) {
      console.error("[AdMob] Load rewarded error:", error);
    }
  },

  /**
   * Rewarded reklam göster
   * @returns {Promise<boolean>} Ödül kazanıldı mı
   */
  async showRewarded() {
    // Admin veya premium kullanıcıya reklam gösterme - direkt ödül ver
    if (!this.showAds) {
      console.log(
        "[AdMob] Ads disabled for this user (admin/premium) - granting reward",
      );
      return true; // Admin/premium için direkt ödül ver
    }

    if (!this.isInitialized || !this.rewardedLoaded) {
      console.log("[AdMob] Rewarded not ready");
      return false;
    }

    return new Promise(async (resolve) => {
      try {
        const { AdMob } = Capacitor.Plugins;

        // Ödül event'ini dinle
        const rewardListener = AdMob.addListener(
          "onRewardedVideoAdReward",
          (reward) => {
            console.log("[AdMob] Reward earned:", reward);
            rewardListener.remove();
            resolve(true);
          },
        );

        // Kapatma event'ini dinle (ödül almadan)
        const dismissListener = AdMob.addListener(
          "onRewardedVideoAdDismissed",
          () => {
            dismissListener.remove();
            // Eğer reward gelmemişse false döndür
            setTimeout(() => resolve(false), 100);
          },
        );

        await AdMob.showRewardVideoAd();
      } catch (error) {
        console.error("[AdMob] Show rewarded error:", error);
        resolve(false);
      }
    });
  },

  /**
   * Rewarded reklam hazır mı?
   */
  isRewardedReady() {
    return this.isInitialized && this.rewardedLoaded;
  },
};

// Export for global access
window.OrbisAds = OrbisAds;

// Auto-initialize when Capacitor is ready
document.addEventListener("DOMContentLoaded", () => {
  // AdMob'u başlat
  if (typeof Capacitor !== "undefined" && Capacitor.isNativePlatform()) {
    setTimeout(() => {
      OrbisAds.initialize();
    }, 2000); // Uygulama yüklendikten 2 saniye sonra
  }
});
