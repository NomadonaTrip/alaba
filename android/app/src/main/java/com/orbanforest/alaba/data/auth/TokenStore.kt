package com.orbanforest.alaba.data.auth

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TokenStore @Inject constructor(@ApplicationContext context: Context) {
    private val prefs by lazy {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        EncryptedSharedPreferences.create(
            context, "alaba_auth", masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    fun saveJwt(jwt: String, userDeviceId: String) {
        prefs.edit()
            .putString(KEY_JWT, jwt)
            .putString(KEY_USER_DEVICE_ID, userDeviceId)
            .apply()
    }

    fun readJwt(): String? = prefs.getString(KEY_JWT, null)
    fun readUserDeviceId(): String? = prefs.getString(KEY_USER_DEVICE_ID, null)
    fun hasJwt(): Boolean = readJwt() != null

    fun clear() {
        prefs.edit().remove(KEY_JWT).remove(KEY_USER_DEVICE_ID).apply()
    }

    private companion object {
        const val KEY_JWT = "jwt"
        const val KEY_USER_DEVICE_ID = "user_device_id"
    }
}
