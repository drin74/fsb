package com.fsb.registry.ui

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.fsb.registry.FSBApplication
import com.fsb.registry.R
import com.fsb.registry.data.AuthResponse
import com.fsb.registry.network.FsbApiClient
import com.google.android.material.button.MaterialButton
import com.google.android.material.textfield.TextInputEditText
import kotlinx.coroutines.launch

class LoginActivity : AppCompatActivity() {
    private lateinit var etLogin: TextInputEditText
    private lateinit var etPassword: TextInputEditText
    private lateinit var btnLogin: MaterialButton
    private lateinit var tvError: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)
        etLogin = findViewById(R.id.etLogin)
        etPassword = findViewById(R.id.etPassword)
        btnLogin = findViewById(R.id.btnLogin)
        tvError = findViewById(R.id.tvError)
        btnLogin.setOnClickListener { performLogin() }
    }

    private fun performLogin() {
        val username = etLogin.text?.toString()?.trim() ?: ""
        val password = etPassword.text?.toString() ?: ""
        tvError.visibility = View.GONE
        if (username.isBlank() || password.isBlank()) {
            showError()
            return
        }
        lifecycleScope.launch {
            try {
                val auth: AuthResponse = FsbApiClient.login(username, password)
                FSBApplication.instance.saveTokens(auth.access ?: "", auth.refresh ?: "")
                startActivity(Intent(this@LoginActivity, MainActivity::class.java))
                finish()
            } catch (t: Throwable) {
                showError()
            }
        }
    }

    private fun showError() {
        tvError.text = "Неверный логин или пароль, или сервер недоступен."
        tvError.visibility = View.VISIBLE
    }
}
