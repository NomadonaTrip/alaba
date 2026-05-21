package com.orbanforest.alaba.data.auth

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DeviceIdStore @Inject constructor(@ApplicationContext context: Context) {
    private val prefs by lazy {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        EncryptedSharedPreferences.create(
            context, "alaba_device", masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    fun getOrCreate(): String {
        val existing = prefs.getString(KEY, null)
        if (existing != null) return existing
        val fresh = UUID.randomUUID().toString()
        prefs.edit().putString(KEY, fresh).apply()
        return fresh
    }

    private companion object {
        const val KEY = "device_id"
    }
}
