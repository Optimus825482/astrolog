# Add project specific ProGuard rules here.
# You can control the set of applied configuration files using the
# proguardFiles setting in build.gradle.
#
# For more details, see
#   http://developer.android.com/guide/developing/tools/proguard.html

# ═══════════════════════════════════════════════════════════════════
# CAPACITOR - WebView ve Bridge koruması
# ═══════════════════════════════════════════════════════════════════
-keep class com.getcapacitor.** { *; }
-keep class com.orbisapp.astrology.** { *; }
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# ═══════════════════════════════════════════════════════════════════
# GOOGLE ADMOB - Reklam SDK koruması
# ═══════════════════════════════════════════════════════════════════
-keep class com.google.android.gms.ads.** { *; }
-keep class com.google.ads.** { *; }

# ═══════════════════════════════════════════════════════════════════
# GOOGLE AUTH - OAuth koruması
# ═══════════════════════════════════════════════════════════════════
-keep class com.google.android.gms.auth.** { *; }
-keep class com.codetrixstudio.capacitor.GoogleAuth.** { *; }

# ═══════════════════════════════════════════════════════════════════
# FIREBASE - Push notifications & Analytics
# ═══════════════════════════════════════════════════════════════════
-keep class com.google.firebase.** { *; }
-keep class com.google.android.gms.** { *; }

# ═══════════════════════════════════════════════════════════════════
# BILLING - In-App Purchase koruması
# ═══════════════════════════════════════════════════════════════════
-keep class com.android.vending.billing.** { *; }

# ═══════════════════════════════════════════════════════════════════
# DEBUGGING - Stack trace için satır numaralarını koru
# ═══════════════════════════════════════════════════════════════════
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile

# ═══════════════════════════════════════════════════════════════════
# GSON / JSON - Serialization koruması
# ═══════════════════════════════════════════════════════════════════
-keepattributes Signature
-keepattributes *Annotation*
-dontwarn sun.misc.**
-keep class * extends com.google.gson.TypeAdapter
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonSerializer
-keep class * implements com.google.gson.JsonDeserializer
