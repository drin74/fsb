package com.fsb.registry

import android.app.Application
import android.content.Context
import android.content.SharedPreferences

class FSBApplication : Application() {

    companion object {
        lateinit var instance: FSBApplication
    }

    private val prefs: SharedPreferences by lazy {
        getSharedPreferences("fsb_registry_prefs", Context.MODE_PRIVATE)
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
    }

    fun saveTokens(access: String, refresh: String?) {
        prefs.edit().putString("access", access).putString("refresh", refresh).apply()
    }

    fun getAccessToken(): String? = prefs.getString("access", null)

    fun getRefreshToken(): String? = prefs.getString("refresh", null)

    fun clearTokens() {
        prefs.edit().clear().apply()
    }
}
