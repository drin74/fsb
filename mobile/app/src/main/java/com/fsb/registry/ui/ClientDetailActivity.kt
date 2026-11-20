package com.fsb.registry.ui

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.EditText
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.widget.Toolbar
import androidx.lifecycle.lifecycleScope
import com.fsb.registry.data.Client
import com.fsb.registry.data.ClientBody
import com.fsb.registry.data.ClientEvent
import com.fsb.registry.data.ClientData
import com.fsb.registry.data.Contact
import com.fsb.registry.data.Consent
import com.fsb.registry.data.EventBody
import com.fsb.registry.data.ContactBody
import com.fsb.registry.network.FsbApiClient
import com.fsb.registry.R
import kotlinx.coroutines.launch

class ClientDetailActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_CLIENT_ID = "clientId"
    }

    private var clientId: Int = -1
    private lateinit var toolbar: Toolbar
    private lateinit var tvFullName: TextView
    private lateinit var tvStatus: TextView
    private lateinit var tvRisk: TextView
    private lateinit var tvMeta: TextView
    private lateinit var tvContacts: TextView
    private lateinit var tvEvents: TextView
    private lateinit var tvData: TextView

    private lateinit var btnBack: Button
    private lateinit var btnEdit: Button
    private lateinit var btnArchive: Button
    private lateinit var btnAddContact: Button
    private lateinit var btnAddEvent: Button

    private lateinit var client: Client

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_client_detail)

        clientId = intent?.getIntExtra(EXTRA_CLIENT_ID, -1) ?: -1
        toolbar = findViewById(R.id.toolbar)
        setSupportActionBar(toolbar)
        toolbar.title = getString(R.string.client_archive_title)

        tvFullName = findViewById(R.id.tvFullName)
        tvStatus = findViewById(R.id.tvStatus)
        tvRisk = findViewById(R.id.tvRisk)
        tvMeta = findViewById(R.id.tvMeta)
        tvContacts = findViewById(R.id.tvContacts)
        tvEvents = findViewById(R.id.tvEvents)
        tvData = findViewById(R.id.tvData)

        btnBack = findViewById(R.id.btnBack)
        btnBack.setOnClickListener { finish() }

        btnEdit = findViewById(R.id.btnEdit)
        btnArchive = findViewById(R.id.btnArchive)
        btnAddContact = findViewById(R.id.btnAddContact)
        btnAddEvent = findViewById(R.id.btnAddEvent)

        btnEdit.setOnClickListener {
            startActivity(
                Intent(this, ClientFormActivity::class.java).putExtra("mode", "update").putExtra("clientId", clientId),
            )
        }

        btnArchive.setOnClickListener { confirmArchive() }
        btnAddContact.setOnClickListener { showAddContactDialog() }
        btnAddEvent.setOnClickListener { showAddEventDialog() }

        loadClient()
    }

    private fun loadClient() {
        lifecycleScope.launch {
            try {
                client = FsbApiClient.getClient(clientId)
                render(client)
            } catch (t: Throwable) {
                Toast.makeText(this@ClientDetailActivity, "Не удалось загрузить карточку.", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun render(client: Client) {
        tvFullName.text = client.fullName ?: "${client.lastName ?: ""} ${client.firstName ?: ""}".trim()
        tvStatus.text = "Статус: ${client.status.replace('_', ' ')}"
        tvRisk.text = "Риск: ${client.riskLevel.replace('_', ' ')}"
        val parts = mutableListOf<String>()
        client.age?.let { parts.add("${it} лет") }
        client.birthDate?.let { parts.add(it) }
        client.citizenship?.let { parts.add(it) }
        parts.add(client.sourceName ?: "Ручной ввод")
        tvMeta.text = parts.filter { it.isNotBlank() }.joinToString(" · ")
        tvContacts.text = formatList(client.contacts)
        tvEvents.text = formatList(client.events)
        tvData.text = formatList(client.dataItems)
    }

    private fun formatList(items: List<*>?): String {
        if (items.isNullOrEmpty()) return "Сведений нет."
        val lines = items.mapNotNull { item ->
            return@mapNotNull when (item) {
                is Contact -> "${item.kindDisplay ?: item.kind}: ${item.value}"
                is ClientEvent -> "${item.title} (${item.occurredAt ?: ""})"
                is ClientData -> "${item.key}: ${item.value}"
                is Consent -> "Согласие: ${item.granted}"
                else -> null
            }
        }
        return lines.joinToString("\n") { "• $it" }
    }

    private fun confirmArchive() {
        AlertDialog.Builder(this)
            .setTitle("Архивация")
            .setMessage("Переместить запись в архив?")
            .setPositiveButton("В архив") { _, _ ->
                lifecycleScope.launch {
                    try {
                        FsbApiClient.deleteClient(clientId)
                        finish()
                    } catch (t: Throwable) {
                        Toast.makeText(this@ClientDetailActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
                    }
                }
            }
            .setNegativeButton("Отмена", null)
            .show()
    }

    private fun showAddContactDialog() {
        val dialogView = layoutInflater.inflate(R.layout.dialog_contact, null)
        val spKind = dialogView.findViewById<Spinner>(R.id.spKind)
        val etValue = dialogView.findViewById<EditText>(R.id.etValue)
        val kinds = arrayOf("phone", "email", "telegram", "whatsapp", "other")
        spKind.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, kinds)
            .also { it.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item) }
        AlertDialog.Builder(this)
            .setTitle("Добавить контакт")
            .setView(dialogView)
            .setPositiveButton("Сохранить") { _, _ ->
                val value = etValue.text?.toString()?.trim() ?: ""
                if (value.isBlank()) return@setPositiveButton
                lifecycleScope.launch {
                    try {
                        FsbApiClient.addContact(ContactBody(clientId, "phone", value, null, false))
                        loadClient()
                    } catch (t: Throwable) {
                        Toast.makeText(this@ClientDetailActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
                    }
                }
            }
            .setNegativeButton("Отмена", null)
            .show()
    }

    private fun showAddEventDialog() {
        val dialogView = layoutInflater.inflate(R.layout.dialog_event, null)
        val spType = dialogView.findViewById<Spinner>(R.id.spEventType)
        val etTitle = dialogView.findViewById<EditText>(R.id.etEventTitle)
        AlertDialog.Builder(this)
            .setTitle("Добавить событие")
            .setView(dialogView)
            .setPositiveButton("Сохранить") { _, _ ->
                val title = etTitle.text?.toString()?.trim() ?: ""
                if (title.isBlank()) return@setPositiveButton
                lifecycleScope.launch {
                    try {
                        FsbApiClient.addEvent(EventBody(clientId, "note", title, "Событие добавлено из мобильного клиента"))
                        loadClient()
                    } catch (t: Throwable) {
                        Toast.makeText(this@ClientDetailActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
                    }
                }
            }
            .setNegativeButton("Отмена", null)
            .show()
    }
}
