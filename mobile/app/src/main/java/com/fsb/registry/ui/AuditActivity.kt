package com.fsb.registry.ui

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.fsb.registry.data.AuditLog
import com.fsb.registry.network.FsbApiClient
import com.fsb.registry.R
import kotlinx.coroutines.launch
import androidx.lifecycle.lifecycleScope

class AuditActivity : AppCompatActivity() {

    private lateinit var recycler: RecyclerView
    private lateinit var adapter: AuditAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_audit)

        recycler = findViewById(R.id.recycler)
        recycler.layoutManager = LinearLayoutManager(this)
        adapter = AuditAdapter { log ->
            val id = log.objectId?.toIntOrNull()
            if (id != null) {
                startActivity(Intent(this, ClientDetailActivity::class.java).putExtra(ClientDetailActivity.EXTRA_CLIENT_ID, id))
            }
        }
        recycler.adapter = adapter

        load()
    }

    private fun load() {
        lifecycleScope.launch {
            try {
                val page = FsbApiClient.audit(page = 1, search = null, action = null)
                adapter.submit(page.results)
            } catch (t: Throwable) {
            }
        }
    }
}
