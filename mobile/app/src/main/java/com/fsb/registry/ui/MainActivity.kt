package com.fsb.registry.ui

import android.content.Intent
import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.KeyEvent
import android.view.View
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.fsb.registry.data.Client
import com.fsb.registry.network.FsbApiClient
import com.fsb.registry.R
import com.google.android.material.floatingactionbutton.FloatingActionButton
import androidx.appcompat.widget.Toolbar
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private lateinit var toolbar: Toolbar
    private lateinit var recycler: RecyclerView
    private lateinit var emptyState: TextView
    private lateinit var fab: FloatingActionButton
    private lateinit var searchInput: EditText
    private lateinit var adapter: ClientAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        toolbar = findViewById(R.id.toolbar)
        setSupportActionBar(toolbar)
        toolbar.title = getString(R.string.main_title)
        toolbar.inflateMenu(R.menu.toolbar)
        toolbar.setOnMenuItemClickListener { menuItem ->
            if (menuItem.itemId == R.id.action_logout) {
                logout()
                return@setOnMenuItemClickListener true
            }
            false
        }

        recycler = findViewById(R.id.recycler)
        recycler.layoutManager = LinearLayoutManager(this)
        adapter = ClientAdapter { client -> openClient(client.id) }
        recycler.adapter = adapter

        emptyState = findViewById(R.id.emptyState)
        fab = findViewById(R.id.fabAdd)
        fab.setOnClickListener { startActivity(Intent(this, ClientFormActivity::class.java)) }

        searchInput = findViewById(R.id.searchInput)
        searchInput.addTextChangedListener(object : TextWatcher {
            private var handler: android.os.Handler? = null
            private val runnable = object : Runnable {
                override fun run() { loadClients() }
            }
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: Editable?) {
                handler?.removeCallbacks(runnable)
                handler = android.os.Handler(android.os.Looper.getMainLooper())
                handler?.postDelayed(runnable, 450)
            }
        })
        searchInput.setOnEditorActionListener { v, actionId, event ->
            if (actionId == android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH || event?.keyCode == android.view.KeyEvent.KEYCODE_ENTER) {
                loadClients()
                return@setOnEditorActionListener true
            }
            false
        }

        loadClients()
    }

    override fun onResume() {
        super.onResume()
        loadClients()
    }

    private fun loadClients() {
        lifecycleScope.launch {
            try {
                val page = FsbApiClient.clients(
                    page = 1,
                    search = searchInput.text?.toString()?.trim()?.takeIf { it.isNotBlank() },
                    status = null,
                    riskLevel = null,
                )
                adapter.submit(page.results)
                emptyState.visibility = if (page.results.isEmpty()) View.VISIBLE else View.GONE
            } catch (t: Throwable) {

            }
        }
    }

    private fun openClient(clientId: Int) {
        startActivity(Intent(this, ClientDetailActivity::class.java).putExtra(ClientDetailActivity.EXTRA_CLIENT_ID, clientId))
    }

    private fun logout() {
        com.fsb.registry.FSBApplication.instance.clearTokens()
        startActivity(Intent(this, LoginActivity::class.java))
        finishAffinity()
    }
}
