import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.orbis.astrology",
  appName: "ORBIS",
  webDir: "www",

  // Server configuration - Production URL
  server: {
    url: "https://ast-kappa.vercel.app",
    androidScheme: "https",
    cleartext: false,
  },

  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      launchAutoHide: true,
      backgroundColor: "#151022",
      androidSplashResourceName: "splash",
      androidScaleType: "CENTER_CROP",
      showSpinner: false,
      splashFullScreen: true,
      splashImmersive: true,
    },
    StatusBar: {
      style: "DARK",
      backgroundColor: "#151022",
    },
    AdMob: {
      testingDevices: ["YOUR_DEVICE_ID"],
      initializeForTesting: true,
    },
    GoogleAuth: {
      scopes: ["profile", "email"],
      serverClientId:
        "768649602152-aous93aj0cnn8bjdsqvjo4t62ip2feci.apps.googleusercontent.com",
      forceCodeForRefreshToken: true,
    },
    PushNotifications: {
      presentationOptions: ["badge", "sound", "alert"],
    },
  },

  android: {
    allowMixedContent: true,
    backgroundColor: "#151022",
  },
};

export default config;
