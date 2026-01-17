/**
 * ORBIS Monetizasyon & Capacitor Bridge
 * Reklam, Kredi ve Premium Sistemi
 *
 * KURALLAR:
 * - Ücretsiz: İlk gün 8 (3 reklamsız + 5 reklamlı), sonra günlük 5 reklamlı
 * - Premium (₺149/ay): 150 kredi dahil, reklamsız, kredi bitince paket al
 */

const OrbisBridge = {
  // ═══════════════════════════════════════════════════════════════
  // YAPILANDIRMA
  // ═══════════════════════════════════════════════════════════════

  CONFIG: {
    // Ücretsiz kullanıcı limitleri
    FREE_FIRST_DAY_TOTAL: 8, // İlk gün toplam
    FREE_FIRST_DAY_NO_AD: 3, // İlk gün reklamsız
    FREE_DAILY_LIMIT: 5, // Sonraki günler (hepsi reklamlı)

    // Premium paketleri
    PREMIUM_PACKAGES: [
      { id: "monthly", name: "Aylık", price: 149, credits: 150, months: 1 },
      { id: "quarterly", name: "3 Aylık", price: 399, credits: 500, months: 3 },
      { id: "biannual", name: "6 Aylık", price: 750, credits: 1000, months: 6 },
      { id: "yearly", name: "Yıllık", price: 1250, credits: 2500, months: 12 },
    ],

    // Kredi paketleri (sadece premium için)
    CREDIT_PACKAGES: [
      { credits: 10, price: 35 },
      { credits: 20, price: 67 },
      { credits: 30, price: 82 },
      { credits: 40, price: 110 },
      { credits: 50, price: 135 },
    ],

    // AdMob ID'leri (Test)
    ADMOB_TEST: {
      APP_ID: "ca-app-pub-3940256099942544~3347511713",
      BANNER: "ca-app-pub-3940256099942544/6300978111",
      INTERSTITIAL: "ca-app-pub-3940256099942544/1033173712",
      REWARDED: "ca-app-pub-3940256099942544/5224354917",
    },

    // AdMob ID'leri (Production)
    ADMOB_PROD: {
      APP_ID: "ca-app-pub-2444093901783574~4683309361",
      BANNER: "ca-app-pub-2444093901783574/5860659669",
      INTERSTITIAL: "ca-app-pub-2444093901783574/8840184408",
      REWARDED: "ca-app-pub-2444093901783574/4900939398",
    },

    // Interstitial gösterim aralığı (her X analizde bir)
    INTERSTITIAL_INTERVAL: 3,

    // Test modu - Production için false
    IS_TESTING: false,
  },

  // ═══════════════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════════════

  state: {
    isNative: false,
    isPremium: false,
    credits: 0,
    premiumPackageId: null, // Hangi premium paketi aldı

    // Ücretsiz kullanıcı için
    installDate: null, // İlk kurulum tarihi
    todayUsage: 0, // Bugünkü kullanım
    todayAdsWatched: 0, // Bugün izlenen reklam
    lastUsageDate: null, // Son kullanım tarihi
    totalAnalyses: 0, // Toplam analiz (interstitial için)

    // Premium için
    premiumExpiry: null, // Premium bitiş tarihi
  },

  // ═══════════════════════════════════════════════════════════════
  // BAŞLATMA
  // ═══════════════════════════════════════════════════════════════

  init() {
    console.log("[ORBIS] Monetizasyon sistemi başlatılıyor...");

    // State'i yükle
    this.loadState();

    // Günlük reset kontrolü
    this.checkDailyReset();

    // Native platform kontrolü
    if (typeof Capacitor !== "undefined" && Capacitor.isNativePlatform()) {
      this.state.isNative = true;
      console.log("[ORBIS] Native platform tespit edildi");
      this.initAdMob();

      // İlk kurulumda bildirim izni iste
      this.requestNotificationPermission();
    } else {
      console.log("[ORBIS] Web platform - reklamlar devre dışı");
    }

    // UI güncelle
    this.updateUI();

    console.log("[ORBIS] Durum:", this.getStatusSummary());

    // GA: Uygulama başlatma event'i
    this.trackEvent("app_start", {
      platform: this.state.isNative ? "native" : "web",
      is_premium: this.state.isPremium,
      credits: this.state.credits,
    });
  },

  // ═══════════════════════════════════════════════════════════════
  // GOOGLE ANALYTICS TRACKING
  // ═══════════════════════════════════════════════════════════════

  /**
   * Google Analytics Event Gönder
   * @param {string} eventName - Event adı
   * @param {object} params - Event parametreleri
   */
  trackEvent(eventName, params = {}) {
    try {
      if (typeof gtag === "function") {
        gtag("event", eventName, {
          ...params,
          timestamp: new Date().toISOString(),
          user_type: this.state.isPremium ? "premium" : "free",
        });
        console.log(`[GA] Event: ${eventName}`, params);
      }
    } catch (error) {
      console.error("[GA] Event tracking error:", error);
    }
  },

  /**
   * Sayfa görüntüleme (SPA için)
   * @param {string} pagePath - Sayfa yolu
   * @param {string} pageTitle - Sayfa başlığı
   */
  trackPageView(pagePath, pageTitle) {
    try {
      if (typeof gtag === "function") {
        gtag("event", "page_view", {
          page_path: pagePath,
          page_title: pageTitle,
        });
        console.log(`[GA] Page view: ${pagePath}`);
      }
    } catch (error) {
      console.error("[GA] Page view tracking error:", error);
    }
  },

  // ═══════════════════════════════════════════════════════════════
  // STATE YÖNETİMİ
  // ═══════════════════════════════════════════════════════════════

  loadState() {
    try {
      const saved = localStorage.getItem("orbis_monetization");
      if (saved) {
        const data = JSON.parse(saved);
        this.state = { ...this.state, ...data };
      }

      // İlk kurulum tarihi yoksa kaydet
      if (!this.state.installDate) {
        this.state.installDate = new Date().toISOString().split("T")[0];
        this.saveState();
      }
    } catch (e) {
      console.error("[ORBIS] State yükleme hatası:", e);
    }
  },

  saveState() {
    try {
      localStorage.setItem("orbis_monetization", JSON.stringify(this.state));
    } catch (e) {
      console.error("[ORBIS] State kaydetme hatası:", e);
    }
  },

  checkDailyReset() {
    const today = new Date().toISOString().split("T")[0];

    if (this.state.lastUsageDate !== today) {
      // Yeni gün - sayaçları sıfırla
      this.state.todayUsage = 0;
      this.state.todayAdsWatched = 0;
      this.state.lastUsageDate = today;
      this.saveState();
      console.log("[ORBIS] Günlük sayaçlar sıfırlandı");
    }
  },

  // ═══════════════════════════════════════════════════════════════
  // BİLDİRİM İZNİ
  // ═══════════════════════════════════════════════════════════════

  async requestNotificationPermission() {
    // Daha önce sorulmuş mu kontrol et
    const alreadyAsked = localStorage.getItem("orbis_notification_asked");
    if (alreadyAsked) {
      console.log("[ORBIS] Bildirim izni daha önce soruldu");
      return;
    }

    // 2 saniye bekle (uygulama açılsın)
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // Güzel bir modal göster
    this.showNotificationPermissionModal();
  },

  showNotificationPermissionModal() {
    // Modal HTML oluştur
    const modalHTML = `
      <div id="notification-permission-modal" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[200] flex items-center justify-center p-4">
        <div class="bg-gradient-to-br from-slate-900 to-slate-800 rounded-3xl p-6 w-full max-w-sm border border-white/10 shadow-2xl animate-fade-in">
          <div class="text-center mb-6">
            <div class="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <span class="material-icons-round text-4xl text-primary">notifications_active</span>
            </div>
            <h3 class="text-xl font-bold text-white mb-2">Bildirimleri Aç</h3>
            <p class="text-sm text-slate-400 leading-relaxed">
              Günlük burç yorumları, önemli transit geçişleri ve kişisel kozmik uyarılar için bildirimleri açın.
            </p>
          </div>
          
          <div class="space-y-3 mb-6">
            <div class="flex items-center gap-3 p-3 bg-white/5 rounded-xl">
              <span class="material-icons-round text-accent">wb_sunny</span>
              <span class="text-xs text-slate-300">Günlük burç yorumları</span>
            </div>
            <div class="flex items-center gap-3 p-3 bg-white/5 rounded-xl">
              <span class="material-icons-round text-yellow-400">stars</span>
              <span class="text-xs text-slate-300">Önemli transit geçişleri</span>
            </div>
            <div class="flex items-center gap-3 p-3 bg-white/5 rounded-xl">
              <span class="material-icons-round text-pink-400">favorite</span>
              <span class="text-xs text-slate-300">Kişisel kozmik uyarılar</span>
            </div>
          </div>
          
          <div class="space-y-2">
            <button onclick="OrbisBridge.acceptNotifications()" class="w-full py-4 bg-primary hover:bg-primary/90 text-white font-bold rounded-2xl transition-all active:scale-95">
              Bildirimleri Aç
            </button>
            <button onclick="OrbisBridge.declineNotifications()" class="w-full py-3 text-slate-400 hover:text-white text-sm transition-colors">
              Şimdi Değil
            </button>
          </div>
        </div>
      </div>
    `;

    // Modal'ı body'e ekle
    document.body.insertAdjacentHTML("beforeend", modalHTML);
  },

  async acceptNotifications() {
    // Modal'ı kapat
    document.getElementById("notification-permission-modal")?.remove();
    localStorage.setItem("orbis_notification_asked", "true");

    try {
      // Capacitor PushNotifications varsa kullan (Native Android/iOS)
      if (
        typeof Capacitor !== "undefined" &&
        Capacitor.Plugins.PushNotifications
      ) {
        const { PushNotifications } = Capacitor.Plugins;

        const result = await PushNotifications.requestPermissions();
        console.log("[ORBIS] Push permission result:", result);

        if (result.receive === "granted") {
          // Token alındığında listener
          PushNotifications.addListener("registration", async (token) => {
            console.log("[ORBIS] FCM Token:", token.value);

            // Token'ı backend'e kaydet ve topic'e subscribe et
            await this.registerFCMToken(token.value, "android");
          });

          // Hata listener
          PushNotifications.addListener("registrationError", (error) => {
            console.error("[ORBIS] FCM Registration error:", error);
          });

          // Bildirim geldiğinde (foreground)
          PushNotifications.addListener(
            "pushNotificationReceived",
            (notification) => {
              console.log("[ORBIS] Push received:", notification);
              // Foreground'da bildirim göster
              this.showInAppNotification(notification.title, notification.body);
            }
          );

          // Bildirime tıklandığında
          PushNotifications.addListener(
            "pushNotificationActionPerformed",
            (notification) => {
              console.log("[ORBIS] Push action:", notification);
            }
          );

          await PushNotifications.register();
          console.log("[ORBIS] Push notifications registered");
        }
      } else if ("Notification" in window && "serviceWorker" in navigator) {
        // Web Push fallback
        const permission = await Notification.requestPermission();
        console.log("[ORBIS] Web notification permission:", permission);

        if (permission === "granted") {
          // Firebase Web Push için messaging kullan
          await this.initWebPush();
        }
      }
    } catch (error) {
      console.error("[ORBIS] Notification permission error:", error);
    }
  },

  async registerFCMToken(token, platform) {
    try {
      // Backend'e token kaydet
      const response = await fetch("/api/fcm/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: token,
          platform: platform,
          topics: ["all_users"], // Varsayılan topic'lere abone ol
        }),
      });

      const data = await response.json();
      console.log("[ORBIS] FCM token registered:", data);

      // Local'e de kaydet
      localStorage.setItem("orbis_fcm_token", token);
    } catch (error) {
      console.error("[ORBIS] FCM token registration error:", error);
    }
  },

  async initWebPush() {
    try {
      // Firebase Web SDK varsa kullan
      if (typeof firebase !== "undefined" && firebase.messaging) {
        const messaging = firebase.messaging();
        const token = await messaging.getToken({
          vapidKey: "YOUR_VAPID_KEY", // Firebase Console'dan al
        });

        if (token) {
          await this.registerFCMToken(token, "web");
        }
      }
    } catch (error) {
      console.error("[ORBIS] Web push init error:", error);
    }
  },

  showInAppNotification(title, body) {
    // Foreground'da güzel bir in-app notification göster
    const notifHTML = `
      <div id="in-app-notif" class="fixed top-4 left-4 right-4 z-[300] animate-slide-down">
        <div class="bg-slate-800/95 backdrop-blur-xl rounded-2xl p-4 border border-white/10 shadow-2xl flex items-start gap-3">
          <div class="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center flex-shrink-0">
            <span class="material-icons-round text-primary">notifications</span>
          </div>
          <div class="flex-1 min-w-0">
            <div class="font-bold text-sm text-white">${title || "ORBIS"}</div>
            <p class="text-xs text-slate-400 mt-1 line-clamp-2">${
              body || ""
            }</p>
          </div>
          <button onclick="document.getElementById('in-app-notif')?.remove()" class="text-slate-500 hover:text-white">
            <span class="material-icons-round text-lg">close</span>
          </button>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML("beforeend", notifHTML);

    // 5 saniye sonra otomatik kapat
    setTimeout(() => {
      document.getElementById("in-app-notif")?.remove();
    }, 5000);
  },

  declineNotifications() {
    // Modal'ı kapat
    document.getElementById("notification-permission-modal")?.remove();
    localStorage.setItem("orbis_notification_asked", "true");
    console.log("[ORBIS] Bildirimler reddedildi");
  },

  // ═══════════════════════════════════════════════════════════════
  // DURUM SORGULAMA
  // ═══════════════════════════════════════════════════════════════

  isFirstDay() {
    const today = new Date().toISOString().split("T")[0];
    return this.state.installDate === today;
  },

  getDailyLimit() {
    if (this.state.isPremium) {
      return Infinity; // Premium için limit yok (kredi varsa)
    }
    return this.isFirstDay()
      ? this.CONFIG.FREE_FIRST_DAY_TOTAL
      : this.CONFIG.FREE_DAILY_LIMIT;
  },

  getRemainingToday() {
    if (this.state.isPremium) {
      return this.state.credits;
    }
    return Math.max(0, this.getDailyLimit() - this.state.todayUsage);
  },

  needsAd() {
    if (this.state.isPremium) return false;
    if (!this.isFirstDay()) return true; // İlk gün değilse her zaman reklam
    return this.state.todayUsage >= this.CONFIG.FREE_FIRST_DAY_NO_AD; // İlk 3'ten sonra reklam
  },

  canAnalyze() {
    if (this.state.isPremium) {
      return this.state.credits > 0;
    }
    return this.state.todayUsage < this.getDailyLimit();
  },

  getStatusSummary() {
    return {
      isPremium: this.state.isPremium,
      credits: this.state.credits,
      isFirstDay: this.isFirstDay(),
      todayUsage: this.state.todayUsage,
      remaining: this.getRemainingToday(),
      needsAd: this.needsAd(),
    };
  },

  // ═══════════════════════════════════════════════════════════════
  // ANALİZ İSTEĞİ
  // ═══════════════════════════════════════════════════════════════

  async requestAnalysis(onSuccess, onCancel) {
    console.log("[ORBIS] Analiz isteği başladı...");
    console.log("[ORBIS] onSuccess callback:", typeof onSuccess);
    console.log("[ORBIS] onCancel callback:", typeof onCancel);

    // Analiz yapılabilir mi kontrol et
    if (!this.canAnalyze()) {
      console.log("[ORBIS] Analiz yapılamaz - limit aşıldı");

      // GA: Limit aşıldı event'i
      this.trackEvent("analysis_limit_reached", {
        today_usage: this.state.todayUsage,
        daily_limit: this.getDailyLimit(),
      });

      this.showLimitReachedModal();
      if (onCancel) {
        console.log("[ORBIS] Calling onCancel...");
        onCancel();
      }
      return;
    }

    // Premium kullanıcı
    if (this.state.isPremium) {
      this.state.credits--;
      this.state.todayUsage++;
      this.state.totalAnalyses++;
      this.saveState();
      this.updateUI();

      // GA: Premium analiz event'i
      this.trackEvent("analysis_completed", {
        analysis_type: "premium",
        remaining_credits: this.state.credits,
        total_analyses: this.state.totalAnalyses,
      });

      console.log("[ORBIS] Premium analiz, kalan kredi:", this.state.credits);
      if (onSuccess) {
        console.log("[ORBIS] Calling onSuccess (premium)...");
        onSuccess();
      }
      return;
    }

    // Ücretsiz kullanıcı - reklam gerekiyor mu?
    if (this.needsAd()) {
      console.log("[ORBIS] Reklam gerekiyor...");
      // Reklam izletmemiz lazım
      const adWatched = await this.showRewardedAdFlow();

      if (adWatched) {
        this.state.todayUsage++;
        this.state.todayAdsWatched++;
        this.state.totalAnalyses++;
        this.saveState();
        this.updateUI();

        // Her 3 analizde interstitial göster
        this.showInterstitialAd();

        // GA: Reklamlı analiz event'i
        this.trackEvent("analysis_completed", {
          analysis_type: "with_ad",
          ads_watched_today: this.state.todayAdsWatched,
          total_analyses: this.state.totalAnalyses,
        });

        console.log(
          "[ORBIS] Reklamlı analiz, bugünkü kullanım:",
          this.state.todayUsage
        );
        if (onSuccess) {
          console.log("[ORBIS] Calling onSuccess (ad watched)...");
          onSuccess();
        }
      } else {
        // GA: Reklam izlenmedi event'i
        this.trackEvent("ad_skipped", {
          ad_type: "rewarded",
        });

        console.log("[ORBIS] Reklam izlenmedi");
        if (onCancel) {
          console.log("[ORBIS] Calling onCancel (ad not watched)...");
          onCancel();
        }
      }
    } else {
      // İlk gün, ilk 3 analiz - reklamsız
      this.state.todayUsage++;
      this.state.totalAnalyses++;
      this.saveState();
      this.updateUI();

      // GA: Ücretsiz analiz event'i
      this.trackEvent("analysis_completed", {
        analysis_type: "free_trial",
        today_usage: this.state.todayUsage,
        total_analyses: this.state.totalAnalyses,
      });

      console.log(
        "[ORBIS] Ücretsiz analiz (hoşgeldin), bugünkü kullanım:",
        this.state.todayUsage
      );

      if (onSuccess) {
        console.log("[ORBIS] Calling onSuccess (free)...");
        try {
          onSuccess();
          console.log("[ORBIS] onSuccess called successfully");
        } catch (err) {
          console.error("[ORBIS] onSuccess error:", err);
        }
      } else {
        console.error("[ORBIS] onSuccess is not defined!");
      }
    }
  },

  // ═══════════════════════════════════════════════════════════════
  // ADMOB
  // ═══════════════════════════════════════════════════════════════

  async initAdMob() {
    if (!this.state.isNative) return;

    try {
      const { AdMob } = Capacitor.Plugins;
      const adConfig = this.CONFIG.IS_TESTING
        ? this.CONFIG.ADMOB_TEST
        : this.CONFIG.ADMOB_PROD;

      await AdMob.initialize({
        initializeForTesting: this.CONFIG.IS_TESTING,
        testingDevices: [],
      });

      console.log("[ORBIS] AdMob başlatıldı");

      // Reklamları önceden yükle
      await this.loadRewardedAd();
      await this.loadInterstitialAd();

      // Premium değilse banner göster
      if (!this.state.isPremium) {
        this.showBanner();
      }
    } catch (error) {
      console.error("[ORBIS] AdMob başlatma hatası:", error);
    }
  },

  async showBanner() {
    if (!this.state.isNative || this.state.isPremium) return;

    try {
      const { AdMob } = Capacitor.Plugins;
      const adConfig = this.CONFIG.IS_TESTING
        ? this.CONFIG.ADMOB_TEST
        : this.CONFIG.ADMOB_PROD;

      await AdMob.showBanner({
        adId: adConfig.BANNER,
        adSize: "ADAPTIVE_BANNER",
        position: "BOTTOM_CENTER",
        margin: 0,
        isTesting: this.CONFIG.IS_TESTING,
      });

      // Banner için padding (banner 60px + bottom nav 80px = 140px)
      document.body.style.paddingBottom = "140px";

      // Bottom nav'ı yukarı kaydır
      const bottomNav = document.querySelector("nav.fixed.bottom-0");
      if (bottomNav) {
        bottomNav.style.bottom = "60px";
      }

      // GA: Banner gösterildi event'i
      this.trackEvent("ad_impression", {
        ad_type: "banner",
        ad_position: "bottom",
      });

      console.log("[ORBIS] Banner gösterildi");
    } catch (error) {
      console.error("[ORBIS] Banner hatası:", error);
    }
  },

  async hideBanner() {
    if (!this.state.isNative) return;

    try {
      const { AdMob } = Capacitor.Plugins;
      await AdMob.hideBanner();
      document.body.style.paddingBottom = "0";

      // Bottom nav'ı eski konumuna döndür
      const bottomNav = document.querySelector("nav.fixed.bottom-0");
      if (bottomNav) {
        bottomNav.style.bottom = "0";
      }
    } catch (error) {
      console.error("[ORBIS] Banner gizleme hatası:", error);
    }
  },

  // Interstitial (tam ekran) reklam
  async loadInterstitialAd() {
    if (!this.state.isNative) return;

    try {
      const { AdMob } = Capacitor.Plugins;
      const adConfig = this.CONFIG.IS_TESTING
        ? this.CONFIG.ADMOB_TEST
        : this.CONFIG.ADMOB_PROD;

      await AdMob.prepareInterstitial({
        adId: adConfig.INTERSTITIAL,
        isTesting: this.CONFIG.IS_TESTING,
      });

      console.log("[ORBIS] Interstitial yüklendi");
    } catch (error) {
      console.error("[ORBIS] Interstitial yükleme hatası:", error);
    }
  },

  async showInterstitialAd() {
    if (!this.state.isNative || this.state.isPremium) return;

    // Her X analizde bir göster
    if (this.state.totalAnalyses % this.CONFIG.INTERSTITIAL_INTERVAL !== 0) {
      return;
    }

    try {
      const { AdMob } = Capacitor.Plugins;
      await AdMob.showInterstitial();

      // GA: Interstitial gösterildi event'i
      this.trackEvent("ad_impression", {
        ad_type: "interstitial",
        total_analyses: this.state.totalAnalyses,
      });

      console.log("[ORBIS] Interstitial gösterildi");

      // Yeni interstitial yükle
      this.loadInterstitialAd();
    } catch (error) {
      console.error("[ORBIS] Interstitial gösterme hatası:", error);
    }
  },

  async loadRewardedAd() {
    if (!this.state.isNative) return;

    try {
      const { AdMob } = Capacitor.Plugins;
      const adConfig = this.CONFIG.IS_TESTING
        ? this.CONFIG.ADMOB_TEST
        : this.CONFIG.ADMOB_PROD;

      await AdMob.prepareRewardVideoAd({
        adId: adConfig.REWARDED,
        isTesting: this.CONFIG.IS_TESTING,
      });

      console.log("[ORBIS] Rewarded ad yüklendi");
    } catch (error) {
      console.error("[ORBIS] Rewarded ad yükleme hatası:", error);
    }
  },

  async showRewardedAdFlow() {
    // Önce dialog göster
    const userAccepted = await this.showAdConfirmDialog();
    if (!userAccepted) return false;

    // Native değilse (web test) direkt geç
    if (!this.state.isNative) {
      console.log("[ORBIS] Web platform - reklam simüle edildi");
      return true;
    }

    // Reklamı göster
    return await this.showRewardedAd();
  },

  showAdConfirmDialog() {
    return new Promise((resolve) => {
      const remaining = this.getRemainingToday();
      const message =
        `🎬 Analiz için kısa bir reklam izlemeniz gerekiyor.\n\n` +
        `📊 Bugün kalan hakkınız: ${remaining}\n\n` +
        `💎 Premium ile reklamsız kullanın!\n\n` +
        `Devam etmek istiyor musunuz?`;

      resolve(confirm(message));
    });
  },

  async showRewardedAd() {
    return new Promise(async (resolve) => {
      try {
        const { AdMob } = Capacitor.Plugins;

        const rewardListener = AdMob.addListener(
          "onRewardedVideoAdReward",
          () => {
            console.log("[ORBIS] Ödül kazanıldı!");

            // GA: Rewarded ad izlendi event'i
            this.trackEvent("ad_reward", {
              ad_type: "rewarded",
              reward_type: "analysis_credit",
            });

            rewardListener.remove();
            resolve(true);
          }
        );

        const dismissListener = AdMob.addListener(
          "onRewardedVideoAdDismissed",
          () => {
            dismissListener.remove();
            setTimeout(() => resolve(false), 100);
          }
        );

        // GA: Rewarded ad gösterildi event'i
        this.trackEvent("ad_impression", {
          ad_type: "rewarded",
        });

        await AdMob.showRewardVideoAd();

        // Yeni reklam yükle
        this.loadRewardedAd();
      } catch (error) {
        console.error("[ORBIS] Rewarded ad gösterme hatası:", error);
        resolve(false);
      }
    });
  },

  // ═══════════════════════════════════════════════════════════════
  // PREMIUM & KREDİ
  // ═══════════════════════════════════════════════════════════════

  showPremiumPackages() {
    let message = `💎 ORBIS PREMIUM PAKETLERİ\n\n`;

    this.CONFIG.PREMIUM_PACKAGES.forEach((pkg, i) => {
      const perMonth = (pkg.price / pkg.months).toFixed(0);
      const perCredit = (pkg.price / pkg.credits).toFixed(2);
      message += `${i + 1}. ${pkg.name}: ₺${pkg.price}\n`;
      message += `   → ${pkg.credits} kredi (₺${perCredit}/kredi)\n`;
      message += `   → ₺${perMonth}/ay\n\n`;
    });

    message += `Satın almak için numara girin (1-${this.CONFIG.PREMIUM_PACKAGES.length}):`;

    const choice = prompt(message);
    if (choice) {
      const index = parseInt(choice) - 1;
      if (index >= 0 && index < this.CONFIG.PREMIUM_PACKAGES.length) {
        this.purchasePremium(index);
      }
    }
  },

  async purchasePremium(packageIndex = 0) {
    const pkg = this.CONFIG.PREMIUM_PACKAGES[packageIndex];
    if (!pkg) return false;

    // TODO: Gerçek In-App Purchase entegrasyonu
    const confirmed = confirm(
      `💎 ORBIS Premium - ${pkg.name}\n\n` +
        `✅ Reklamsız deneyim\n` +
        `✅ ${pkg.credits} analiz kredisi\n` +
        `✅ ${pkg.months} ay geçerlilik\n` +
        `✅ Öncelikli destek\n\n` +
        `Fiyat: ₺${pkg.price}\n\n` +
        `Satın almak istiyor musunuz?`
    );

    if (confirmed) {
      // Test için aktif et
      this.state.isPremium = true;
      this.state.premiumPackageId = pkg.id;
      this.state.credits += pkg.credits;
      this.state.premiumExpiry = new Date(
        Date.now() + pkg.months * 30 * 24 * 60 * 60 * 1000
      ).toISOString();
      this.saveState();

      // Banner'ı gizle
      this.hideBanner();

      this.updateUI();

      // GA: Premium satın alma event'i
      this.trackEvent("purchase", {
        transaction_id: `premium_${Date.now()}`,
        value: pkg.price,
        currency: "TRY",
        items: [
          {
            item_id: pkg.id,
            item_name: `Premium ${pkg.name}`,
            category: "subscription",
            price: pkg.price,
            quantity: 1,
          },
        ],
      });

      alert(
        `🎉 Premium aktivasyonu başarılı!\n\n` +
          `📦 Paket: ${pkg.name}\n` +
          `🎫 ${pkg.credits} kredi hesabınıza eklendi.\n` +
          `📅 Geçerlilik: ${pkg.months} ay`
      );
      return true;
    }

    return false;
  },

  async purchaseCredits(packageIndex) {
    if (!this.state.isPremium) {
      alert("❌ Kredi satın almak için Premium üye olmanız gerekiyor.");
      this.showPremiumPackages();
      return false;
    }

    const pkg = this.CONFIG.CREDIT_PACKAGES[packageIndex];
    if (!pkg) return false;

    // TODO: Gerçek In-App Purchase entegrasyonu
    const confirmed = confirm(
      `🎫 Kredi Paketi\n\n` +
        `${pkg.credits} Kredi = ₺${pkg.price}\n` +
        `(Birim fiyat: ₺${(pkg.price / pkg.credits).toFixed(2)})\n\n` +
        `Satın almak istiyor musunuz?`
    );

    if (confirmed) {
      this.state.credits += pkg.credits;
      this.saveState();
      this.updateUI();

      // GA: Kredi satın alma event'i
      this.trackEvent("purchase", {
        transaction_id: `credits_${Date.now()}`,
        value: pkg.price,
        currency: "TRY",
        items: [
          {
            item_id: `credits_${pkg.credits}`,
            item_name: `${pkg.credits} Kredi Paketi`,
            category: "credits",
            price: pkg.price,
            quantity: 1,
          },
        ],
      });

      alert(
        `🎉 ${pkg.credits} kredi hesabınıza eklendi!\n\nToplam: ${this.state.credits} kredi`
      );
      return true;
    }

    return false;
  },

  showCreditPackages() {
    if (!this.state.isPremium) {
      this.showPremiumPromo();
      return;
    }

    let message = `🎫 KREDİ PAKETLERİ\n\nMevcut krediniz: ${this.state.credits}\n\n`;

    this.CONFIG.CREDIT_PACKAGES.forEach((pkg, i) => {
      const unitPrice = (pkg.price / pkg.credits).toFixed(2);
      message += `${i + 1}. ${pkg.credits} Kredi = ₺${
        pkg.price
      } (₺${unitPrice}/adet)\n`;
    });

    message += `\nSatın almak için numara girin (1-${this.CONFIG.CREDIT_PACKAGES.length}):`;

    const choice = prompt(message);
    if (choice) {
      const index = parseInt(choice) - 1;
      if (index >= 0 && index < this.CONFIG.CREDIT_PACKAGES.length) {
        this.purchaseCredits(index);
      }
    }
  },

  // ═══════════════════════════════════════════════════════════════
  // UI & MODALS
  // ═══════════════════════════════════════════════════════════════

  showLimitReachedModal() {
    if (this.state.isPremium) {
      // Premium ama kredi bitti
      const buyMore = confirm(
        `😔 Krediniz bitti!\n\n` +
          `Daha fazla analiz için kredi satın alın.\n\n` +
          `Kredi paketlerini görmek ister misiniz?`
      );

      if (buyMore) {
        this.showCreditPackages();
      }
    } else {
      // Ücretsiz kullanıcı limit doldu
      const goPremium = confirm(
        `⏰ Günlük limitiniz doldu!\n\n` +
          `Bugün ${this.state.todayUsage} analiz yaptınız.\n\n` +
          `💎 Premium ile sınırsız analiz yapın!\n` +
          `• 150 kredi dahil\n` +
          `• Reklamsız deneyim\n` +
          `• Sadece ₺${this.CONFIG.PREMIUM_MONTHLY_PRICE}/ay\n\n` +
          `Premium'a geçmek ister misiniz?`
      );

      if (goPremium) {
        this.purchasePremium();
      }
    }
  },

  showPremiumPromo() {
    const goPremium = confirm(
      `💎 ORBIS Premium\n\n` +
        `✅ ${this.CONFIG.PREMIUM_INCLUDED_CREDITS} analiz kredisi\n` +
        `✅ Reklamsız deneyim\n` +
        `✅ Kredi paketleri satın alabilme\n` +
        `✅ Öncelikli destek\n\n` +
        `Sadece ₺${this.CONFIG.PREMIUM_MONTHLY_PRICE}/ay\n\n` +
        `Premium'a geçmek ister misiniz?`
    );

    if (goPremium) {
      this.purchasePremium();
    }
  },

  updateUI() {
    // Status bar güncelle (varsa)
    const statusEl = document.getElementById("orbis-status");
    if (statusEl) {
      if (this.state.isPremium) {
        statusEl.innerHTML = `💎 Premium | ${this.state.credits} Kredi`;
      } else {
        const remaining = this.getRemainingToday();
        statusEl.innerHTML = `🆓 Ücretsiz | Bugün: ${remaining} hak`;
      }
    }

    // Premium badge (varsa)
    const premiumBadge = document.getElementById("premium-badge");
    if (premiumBadge) {
      premiumBadge.style.display = this.state.isPremium ? "flex" : "none";
    }
  },

  // ═══════════════════════════════════════════════════════════════
  // TEST & DEBUG
  // ═══════════════════════════════════════════════════════════════

  resetAll() {
    if (confirm("⚠️ Tüm veriler sıfırlanacak. Emin misiniz?")) {
      localStorage.removeItem("orbis_monetization");
      location.reload();
    }
  },

  /**
   * Firebase çıkış yapıldığında local state'e dön
   */
  resetToLocal() {
    console.log("[ORBIS] Firebase çıkış - local state'e dönülüyor");

    // Local storage'dan yükle
    this.loadState();

    // UI güncelle
    this.updateUI();

    // Premium değilse banner göster
    if (!this.state.isPremium && this.state.isNative) {
      this.showBanner();
    }
  },

  addTestCredits(amount = 10) {
    this.state.credits += amount;
    this.saveState();
    this.updateUI();
    console.log(
      `[ORBIS] Test: ${amount} kredi eklendi. Toplam: ${this.state.credits}`
    );
  },

  simulateNewDay() {
    this.state.lastUsageDate = "2000-01-01";
    this.checkDailyReset();
    console.log("[ORBIS] Test: Yeni gün simüle edildi");
  },
};

// Global erişim
window.OrbisBridge = OrbisBridge;

// Sayfa yüklendiğinde başlat
document.addEventListener("DOMContentLoaded", () => {
  OrbisBridge.init();
});
