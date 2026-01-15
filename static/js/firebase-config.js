/**
 * ORBIS Firebase Configuration
 * Auth + Firestore for user data sync
 */

const OrbisFirebase = {
  // Firebase Config
  config: {
    apiKey: "AIzaSyD9QYFaOQVxEvt3ENEfgaqVyweHuRy-MBQ",
    authDomain: "orbis-ffa9e.firebaseapp.com",
    projectId: "orbis-ffa9e",
    storageBucket: "orbis-ffa9e.firebasestorage.app",
    messagingSenderId: "768649602152",
    appId: "1:768649602152:web:d1cd9f7deadcdfef1907dd",
    measurementId: "G-V3FBQWDN61",
  },

  // State
  app: null,
  auth: null,
  db: null,
  user: null,
  userDoc: null,
  unsubscribe: null,

  // ═══════════════════════════════════════════════════════════════
  // BAŞLATMA
  // ═══════════════════════════════════════════════════════════════

  async init() {
    try {
      // Firebase SDK yüklü mü kontrol et
      if (typeof firebase === "undefined") {
        console.error("[Firebase] SDK yüklenmemiş!");
        return false;
      }

      // Firebase'i başlat
      this.app = firebase.initializeApp(this.config);
      this.auth = firebase.auth();
      this.db = firebase.firestore();

      console.log("[Firebase] Başlatıldı");

      // ═══════════════════════════════════════════════════════════════
      // CAPACITOR GOOGLE AUTH INITIALIZATION (Native Platform)
      // ═══════════════════════════════════════════════════════════════
      await this.initCapacitorGoogleAuth();

      // Redirect sonrası result kontrolü (Web için)
      try {
        const result = await this.auth.getRedirectResult();
        if (result.user) {
          console.log("[Firebase] Redirect giriş başarılı:", result.user.email);
        }
      } catch (redirectError) {
        console.log(
          "[Firebase] Redirect result yok veya hata:",
          redirectError.code
        );
      }

      // Auth state listener
      this.auth.onAuthStateChanged((user) => {
        this.handleAuthStateChange(user);
      });

      return true;
    } catch (error) {
      console.error("[Firebase] Başlatma hatası:", error);
      return false;
    }
  },

  // Capacitor GoogleAuth Plugin Initialize
  async initCapacitorGoogleAuth() {
    try {
      const isNative =
        typeof Capacitor !== "undefined" && Capacitor.isNativePlatform();

      if (!isNative) {
        console.log("[GoogleAuth] Web platform - skip native init");
        return;
      }

      console.log("[GoogleAuth] Native platform detected - initializing...");

      // Plugin'i bul
      let GoogleAuth = null;

      if (Capacitor.Plugins && Capacitor.Plugins.GoogleAuth) {
        GoogleAuth = Capacitor.Plugins.GoogleAuth;
      } else if (window.Plugins && window.Plugins.GoogleAuth) {
        GoogleAuth = window.Plugins.GoogleAuth;
      }

      if (!GoogleAuth) {
        console.warn("[GoogleAuth] Plugin bulunamadı - sonra tekrar denenecek");
        return;
      }

      // Plugin'i initialize et
      await GoogleAuth.initialize({
        clientId:
          "768649602152-aous93aj0cnn8bjdsqvjo4t62ip2feci.apps.googleusercontent.com",
        scopes: ["profile", "email"],
        grantOfflineAccess: true,
      });

      console.log("[GoogleAuth] Plugin başarıyla initialize edildi!");
    } catch (error) {
      console.error("[GoogleAuth] Initialize hatası:", error);
      // Hatayı yutuyoruz çünkü bazı durumlarda (Android'de zaten init edilmişse) hata verebilir
    }
  },

  // ═══════════════════════════════════════════════════════════════
  // AUTH
  // ═══════════════════════════════════════════════════════════════

  async signInWithGoogle() {
    try {
      // Native platform kontrolü (Capacitor Android/iOS)
      const isNative =
        typeof Capacitor !== "undefined" && Capacitor.isNativePlatform();

      console.log("[Firebase] isNative:", isNative);

      if (isNative) {
        console.log(
          "[Firebase] Native platform - Capacitor Google Auth kullanılıyor..."
        );

        // Capacitor Google Auth plugin kontrolü
        let GoogleAuth = null;

        // Yeni Capacitor 5+ API
        if (
          typeof Capacitor !== "undefined" &&
          Capacitor.Plugins &&
          Capacitor.Plugins.GoogleAuth
        ) {
          GoogleAuth = Capacitor.Plugins.GoogleAuth;
        }

        // Alternatif: Global @codetrix-studio/capacitor-google-auth
        if (!GoogleAuth && window.Plugins && window.Plugins.GoogleAuth) {
          GoogleAuth = window.Plugins.GoogleAuth;
        }

        if (!GoogleAuth) {
          console.error("[Firebase] GoogleAuth plugin bulunamadı!");
          alert(
            "Google Auth eklentisi bulunamadı.\n\n" +
              "Lütfen uygulamayı yeniden yükleyin veya " +
              "destek@orbis.app adresine başvurun."
          );
          return null;
        }

        try {
          console.log("[Firebase] GoogleAuth.signIn() çağrılıyor...");

          // Native Google Sign-In
          const googleUser = await GoogleAuth.signIn();

          console.log(
            "[Firebase] Native Google Sign-In başarılı:",
            googleUser.email
          );
          console.log(
            "[Firebase] idToken mevcut:",
            !!googleUser.authentication?.idToken
          );

          if (!googleUser.authentication?.idToken) {
            throw new Error("idToken alınamadı!");
          }

          // Firebase credential oluştur
          const credential = firebase.auth.GoogleAuthProvider.credential(
            googleUser.authentication.idToken
          );

          // Firebase'e giriş yap
          const result = await this.auth.signInWithCredential(credential);
          console.log("[Firebase] Firebase giriş başarılı:", result.user.email);

          return result.user;
        } catch (nativeError) {
          console.error("[Firebase] Native Google Auth hatası:", nativeError);

          // Kullanıcı iptal etti mi?
          const errorMsg = nativeError.message || JSON.stringify(nativeError);

          if (
            errorMsg.includes("canceled") ||
            errorMsg.includes("cancelled") ||
            errorMsg.includes("12501") ||
            errorMsg.includes("user_cancelled")
          ) {
            console.log("[Firebase] Kullanıcı giriş işlemini iptal etti");
            return null;
          }

          // Gerçek hata - kullanıcıya bildir
          alert(
            "Google giriş hatası!\n\n" +
              "Hata: " +
              errorMsg +
              "\n\n" +
              "İpucu: İnternet bağlantınızı kontrol edin ve tekrar deneyin."
          );
          return null;
        }
      }

      // ═══════════════════════════════════════════════════════════════
      // WEB PLATFORM - Normal tarayıcı için
      // ═══════════════════════════════════════════════════════════════

      const provider = new firebase.auth.GoogleAuthProvider();
      provider.setCustomParameters({ prompt: "select_account" });

      try {
        const result = await this.auth.signInWithPopup(provider);
        console.log("[Firebase] Google ile giriş başarılı:", result.user.email);
        return result.user;
      } catch (popupError) {
        console.error(
          "[Firebase] Popup hatası:",
          popupError.code,
          popupError.message
        );

        if (
          popupError.code === "auth/popup-blocked" ||
          popupError.code === "auth/popup-closed-by-user"
        ) {
          console.log("[Firebase] Popup başarısız, redirect deneniyor...");
          await this.auth.signInWithRedirect(provider);
          return null;
        }
        throw popupError;
      }
    } catch (error) {
      console.error("[Firebase] Google giriş hatası:", error);
      alert("Giriş sırasında beklenmeyen bir hata oluştu: " + error.message);
      return null;
    }
  },

  async signOut() {
    try {
      // Firestore listener'ı kaldır
      if (this.unsubscribe) {
        this.unsubscribe();
        this.unsubscribe = null;
      }

      await this.auth.signOut();
      this.user = null;
      this.userDoc = null;

      console.log("[Firebase] Çıkış yapıldı");

      // UI güncelle
      this.updateAuthUI();

      // OrbisBridge'i sıfırla
      if (window.OrbisBridge) {
        window.OrbisBridge.resetToLocal();
      }

      return true;
    } catch (error) {
      console.error("[Firebase] Çıkış hatası:", error);
      return false;
    }
  },

  handleAuthStateChange(user) {
    this.user = user;

    if (user) {
      console.log("[Firebase] Kullanıcı giriş yaptı:", user.email);
      this.loadUserData();

      // Mobile app'e kullanıcı bilgisini gönder (reklam kontrolü için)
      if (
        window.OrbisApp &&
        typeof window.OrbisApp.onUserLogin === "function"
      ) {
        window.OrbisApp.onUserLogin(user);
      }
    } else {
      console.log("[Firebase] Kullanıcı çıkış yaptı");
      this.userDoc = null;

      // Mobile app'e çıkış bilgisini gönder
      if (
        window.OrbisApp &&
        typeof window.OrbisApp.onUserLogout === "function"
      ) {
        window.OrbisApp.onUserLogout();
      }
    }

    this.updateAuthUI();
  },

  // ═══════════════════════════════════════════════════════════════
  // FIRESTORE - KULLANICI VERİLERİ
  // ═══════════════════════════════════════════════════════════════

  async loadUserData() {
    if (!this.user) return null;

    try {
      const docRef = this.db.collection("users").doc(this.user.uid);

      // Realtime listener
      this.unsubscribe = docRef.onSnapshot((doc) => {
        if (doc.exists) {
          this.userDoc = doc.data();
          console.log("[Firebase] Kullanıcı verisi yüklendi:", this.userDoc);
        } else {
          // Yeni kullanıcı - varsayılan veri oluştur
          this.createNewUser();
        }

        // OrbisBridge'e sync et
        this.syncToOrbisBridge();
      });

      return this.userDoc;
    } catch (error) {
      console.error("[Firebase] Veri yükleme hatası:", error);
      return null;
    }
  },

  async createNewUser() {
    if (!this.user) return;

    const newUserData = {
      email: this.user.email,
      displayName: this.user.displayName,
      photoURL: this.user.photoURL,
      createdAt: firebase.firestore.FieldValue.serverTimestamp(),

      // Monetizasyon
      isPremium: false,
      premiumPackageId: null,
      premiumExpiry: null,
      credits: 0,

      // Kullanım istatistikleri
      totalAnalyses: 0,
      installDate: new Date().toISOString().split("T")[0],

      // Günlük kullanım (her gün sıfırlanır)
      dailyUsage: {
        date: new Date().toISOString().split("T")[0],
        count: 0,
        adsWatched: 0,
      },
    };

    try {
      await this.db.collection("users").doc(this.user.uid).set(newUserData);
      this.userDoc = newUserData;
      console.log("[Firebase] Yeni kullanıcı oluşturuldu");
    } catch (error) {
      console.error("[Firebase] Kullanıcı oluşturma hatası:", error);
    }
  },

  async updateUserData(updates) {
    if (!this.user) return false;

    try {
      await this.db
        .collection("users")
        .doc(this.user.uid)
        .update({
          ...updates,
          updatedAt: firebase.firestore.FieldValue.serverTimestamp(),
        });
      console.log("[Firebase] Kullanıcı verisi güncellendi");
      return true;
    } catch (error) {
      console.error("[Firebase] Güncelleme hatası:", error);
      return false;
    }
  },

  // ═══════════════════════════════════════════════════════════════
  // PREMIUM & KREDİ İŞLEMLERİ
  // ═══════════════════════════════════════════════════════════════

  async activatePremium(packageId, credits, months) {
    if (!this.user) {
      alert("Premium satın almak için giriş yapmalısınız.");
      return false;
    }

    const expiryDate = new Date();
    expiryDate.setMonth(expiryDate.getMonth() + months);

    const updates = {
      isPremium: true,
      premiumPackageId: packageId,
      premiumExpiry: expiryDate.toISOString(),
      credits: firebase.firestore.FieldValue.increment(credits),
    };

    const success = await this.updateUserData(updates);

    if (success) {
      // Satın alma kaydı
      await this.logPurchase("premium", packageId, credits);
    }

    return success;
  },

  async addCredits(amount, packagePrice) {
    if (!this.user) return false;

    const success = await this.updateUserData({
      credits: firebase.firestore.FieldValue.increment(amount),
    });

    if (success) {
      await this.logPurchase("credits", amount, packagePrice);
    }

    return success;
  },

  async useCredit() {
    if (!this.user || !this.userDoc) return false;
    if (this.userDoc.credits <= 0) return false;

    return await this.updateUserData({
      credits: firebase.firestore.FieldValue.increment(-1),
      totalAnalyses: firebase.firestore.FieldValue.increment(1),
    });
  },

  async updateDailyUsage() {
    if (!this.user) return;

    const today = new Date().toISOString().split("T")[0];

    // Günlük reset kontrolü
    if (this.userDoc?.dailyUsage?.date !== today) {
      await this.updateUserData({
        "dailyUsage.date": today,
        "dailyUsage.count": 1,
        "dailyUsage.adsWatched": 0,
      });
    } else {
      await this.updateUserData({
        "dailyUsage.count": firebase.firestore.FieldValue.increment(1),
      });
    }
  },

  async logPurchase(type, item, amount) {
    if (!this.user) return;

    try {
      await this.db.collection("purchases").add({
        userId: this.user.uid,
        type: type,
        item: item,
        amount: amount,
        timestamp: firebase.firestore.FieldValue.serverTimestamp(),
      });
    } catch (error) {
      console.error("[Firebase] Satın alma kaydı hatası:", error);
    }
  },

  // ═══════════════════════════════════════════════════════════════
  // SYNC
  // ═══════════════════════════════════════════════════════════════

  syncToOrbisBridge() {
    if (!window.OrbisBridge || !this.userDoc) return;

    // Firebase verilerini OrbisBridge'e aktar
    window.OrbisBridge.state.isPremium = this.userDoc.isPremium || false;
    window.OrbisBridge.state.credits = this.userDoc.credits || 0;
    window.OrbisBridge.state.premiumPackageId = this.userDoc.premiumPackageId;
    window.OrbisBridge.state.premiumExpiry = this.userDoc.premiumExpiry;
    window.OrbisBridge.state.totalAnalyses = this.userDoc.totalAnalyses || 0;

    // Günlük kullanım
    const today = new Date().toISOString().split("T")[0];
    if (this.userDoc.dailyUsage?.date === today) {
      window.OrbisBridge.state.todayUsage = this.userDoc.dailyUsage.count || 0;
      window.OrbisBridge.state.todayAdsWatched =
        this.userDoc.dailyUsage.adsWatched || 0;
    } else {
      window.OrbisBridge.state.todayUsage = 0;
      window.OrbisBridge.state.todayAdsWatched = 0;
    }

    window.OrbisBridge.updateUI();
    console.log("[Firebase] OrbisBridge sync tamamlandı");
  },

  // ═══════════════════════════════════════════════════════════════
  // UI
  // ═══════════════════════════════════════════════════════════════

  updateAuthUI() {
    const loginBtn = document.getElementById("login-btn");
    const userInfo = document.getElementById("user-info");
    const userAvatar = document.getElementById("user-avatar");
    const userName = document.getElementById("user-name");

    // Mobile elements
    const mobileProfileIcon = document.getElementById("mobile-profile-icon");
    const mobileAvatar = document.getElementById("mobile-avatar");

    if (this.user) {
      // Giriş yapılmış - Desktop
      if (loginBtn) loginBtn.style.display = "none";
      if (userInfo) {
        userInfo.style.display = "flex";
        userInfo.classList.remove("hidden");
      }
      if (userAvatar) userAvatar.src = this.user.photoURL || "";
      if (userName)
        userName.textContent = this.user.displayName || this.user.email;

      // Mobile
      if (mobileProfileIcon) mobileProfileIcon.classList.add("hidden");
      if (mobileAvatar) {
        mobileAvatar.src = this.user.photoURL || "";
        mobileAvatar.classList.remove("hidden");
      }
    } else {
      // Giriş yapılmamış - Desktop
      if (loginBtn) loginBtn.style.display = "flex";
      if (userInfo) {
        userInfo.style.display = "none";
        userInfo.classList.add("hidden");
      }

      // Mobile
      if (mobileProfileIcon) mobileProfileIcon.classList.remove("hidden");
      if (mobileAvatar) mobileAvatar.classList.add("hidden");
    }

    // Mobile auth modal güncelle (varsa)
    if (typeof updateMobileAuthView === "function") {
      updateMobileAuthView();
    }
  },

  // ═══════════════════════════════════════════════════════════════
  // HELPERS
  // ═══════════════════════════════════════════════════════════════

  isLoggedIn() {
    return !!this.user;
  },

  getCurrentUser() {
    return this.user;
  },

  getUserData() {
    return this.userDoc;
  },

  // ═══════════════════════════════════════════════════════════════
  // PUSH NOTIFICATIONS (FCM)
  // ═══════════════════════════════════════════════════════════════

  messaging: null,
  fcmToken: null,

  async initMessaging() {
    try {
      // Service Worker kontrolü
      if (!("serviceWorker" in navigator)) {
        console.log("[FCM] Service Worker desteklenmiyor");
        return false;
      }

      // Notification izni kontrolü
      if (!("Notification" in window)) {
        console.log("[FCM] Notification API desteklenmiyor");
        return false;
      }

      // Firebase Messaging Service Worker'ı register et
      const registration = await navigator.serviceWorker.register(
        "/firebase-messaging-sw.js",
        {
          scope: "/firebase-cloud-messaging-push-scope",
        }
      );

      // Service Worker'ın aktif olmasını bekle
      await navigator.serviceWorker.ready;
      console.log("[FCM] Service Worker registered:", registration.scope);

      this.messaging = firebase.messaging();

      // Foreground mesaj dinleyicisi
      this.messaging.onMessage((payload) => {
        console.log("[FCM] Foreground mesaj:", payload);
        this.showNotification(payload);
      });

      console.log("[FCM] Messaging başlatıldı");
      return true;
    } catch (error) {
      console.error("[FCM] Messaging başlatma hatası:", error);
      return false;
    }
  },

  async requestNotificationPermission() {
    try {
      const permission = await Notification.requestPermission();

      if (permission === "granted") {
        console.log("[FCM] Bildirim izni verildi");
        return await this.getFCMToken();
      } else {
        console.log("[FCM] Bildirim izni reddedildi");
        return null;
      }
    } catch (error) {
      console.error("[FCM] İzin hatası:", error);
      return null;
    }
  },

  async getFCMToken() {
    if (!this.messaging) {
      await this.initMessaging();
    }

    try {
      // VAPID key - Firebase Console > Project Settings > Cloud Messaging > Web Push certificates
      // Bu key'i Firebase Console'dan alman gerekiyor
      const vapidKey =
        "BDG800ijmQ1av11kHWR-ZnW_gVUKUYjKMH7oYqKnF-BsSb2K4ECB9PL0cQzpP90jehx5zwnR7WH46kYdlq6kUbE"; // TODO: Firebase Console'dan al

      const token = await this.messaging.getToken({ vapidKey });

      if (token) {
        this.fcmToken = token;
        console.log("[FCM] Token alındı:", token.substring(0, 20) + "...");

        // Token'ı backend'e kaydet
        await this.saveFCMToken(token);

        return token;
      }
    } catch (error) {
      console.error("[FCM] Token alma hatası:", error);
    }

    return null;
  },

  async saveFCMToken(token) {
    if (!this.user) return false;

    try {
      // Backend'e kaydet
      const response = await fetch("/api/push/register-token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userId: this.user.uid,
          token: token,
          platform: this.detectPlatform(),
        }),
      });

      const result = await response.json();
      console.log("[FCM] Token kaydedildi:", result);
      return result.success;
    } catch (error) {
      console.error("[FCM] Token kaydetme hatası:", error);
      return false;
    }
  },

  async subscribeToTopic(topic) {
    if (!this.fcmToken) return false;

    try {
      const response = await fetch("/api/push/subscribe-topic", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: this.fcmToken,
          topic: topic,
        }),
      });

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error("[FCM] Topic subscribe hatası:", error);
      return false;
    }
  },

  showNotification(payload) {
    // Foreground'da bildirim göster
    const { title, body, icon } = payload.notification || {};
    const data = payload.data || {};

    // Custom notification UI
    if (typeof showToast === "function") {
      showToast(title, body);
    } else {
      // Fallback: Browser notification
      if (Notification.permission === "granted") {
        new Notification(title, {
          body: body,
          icon:
            icon || "/static/all-icons/Android/mipmap-xxxhdpi/ic_launcher.png",
          data: data,
        });
      }
    }
  },

  detectPlatform() {
    const ua = navigator.userAgent;
    if (/android/i.test(ua)) return "android";
    if (/iPad|iPhone|iPod/.test(ua)) return "ios";
    return "web";
  },
};

// Global erişim
window.OrbisFirebase = OrbisFirebase;
