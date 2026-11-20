package com.fsb.registry.ui

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.fsb.registry.data.Client
import com.fsb.registry.data.ClientBody
import com.fsb.registry.network.FsbApiClient
import com.fsb.registry.R
import kotlinx.coroutines.launch

class ClientFormActivity : AppCompatActivity() {

    private var clientId: Int = -1
    private var modeCreate = false

    private lateinit var etLastName: EditText
    private lateinit var etFirstName: EditText
    private lateinit var etMiddleName: EditText
    private lateinit var etBirthDate: EditText
    private lateinit var etGender: EditText
    private lateinit var etCitizenship: EditText
    private lateinit var etInn: EditText
    private lateinit var etSnils: EditText
    private lateinit var etPassportSeries: EditText
    private lateinit var etPassportNumber: EditText
    private lateinit var etPassportIssuedBy: EditText
    private lateinit var etPassportIssueDate: EditText
    private lateinit var etPhone: EditText
    private lateinit var etEmail: EditText
    private lateinit var etAddressRegistration: EditText
    private lateinit var etAddressActual: EditText
    private lateinit var etStatus: EditText
    private lateinit var etRiskLevel: EditText
    private lateinit var etSource: EditText
    private lateinit var etTags: EditText
    private lateinit var etNotes: EditText
    private lateinit var btnSave: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_client_form)

        val mode = getIntent()?.getStringExtra("mode")
        modeCreate = mode == "create"
        clientId = getIntent()?.getIntExtra("clientId", -1) ?: -1

        etLastName = findViewById(R.id.etLastName)
        etFirstName = findViewById(R.id.etFirstName)
        etMiddleName = findViewById(R.id.etMiddleName)
        etBirthDate = findViewById(R.id.etBirthDate)
        etGender = findViewById(R.id.etGender)
        etCitizenship = findViewById(R.id.etCitizenship)
        etInn = findViewById(R.id.etInn)
        etSnils = findViewById(R.id.etSnils)
        etPassportSeries = findViewById(R.id.etPassportSeries)
        etPassportNumber = findViewById(R.id.etPassportNumber)
        etPassportIssuedBy = findViewById(R.id.etPassportIssuedBy)
        etPassportIssueDate = findViewById(R.id.etPassportIssueDate)
        etPhone = findViewById(R.id.etPhone)
        etEmail = findViewById(R.id.etEmail)
        etAddressRegistration = findViewById(R.id.etAddressRegistration)
        etAddressActual = findViewById(R.id.etAddressActual)
        etStatus = findViewById(R.id.etStatus)
        etRiskLevel = findViewById(R.id.etRiskLevel)
        etSource = findViewById(R.id.etSource)
        etTags = findViewById(R.id.etTags)
        etNotes = findViewById(R.id.etNotes)
        btnSave = findViewById(R.id.btnSave)

        btnSave.setOnClickListener { save() }

        if (!modeCreate && clientId != -1) {
            loadClient()
        }
    }

    private fun loadClient() {
        lifecycleScope.launch {
            try {
                val client = FsbApiClient.getClient(clientId)
                populate(client)
            } catch (t: Throwable) {
                Toast.makeText(this@ClientFormActivity, "Не удалось загрузить запись: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun populate(client: Client) {
        etLastName.setText(client.lastName ?: "")
        etFirstName.setText(client.firstName ?: "")
        etMiddleName.setText(client.middleName ?: "")
        etBirthDate.setText(client.birthDate ?: "")
        etGender.setText(client.genderDisplay ?: client.gender ?: "")
        etCitizenship.setText(client.citizenship ?: "")
        etInn.setText(client.inn ?: "")
        etSnils.setText(client.snils ?: "")
        etPassportSeries.setText(client.passportSeries ?: "")
        etPassportNumber.setText(client.passportNumber ?: "")
        etPassportIssuedBy.setText(client.passportIssuedBy ?: "")
        etPassportIssueDate.setText(client.passportIssueDate ?: "")
        etPhone.setText(client.phone ?: "")
        etEmail.setText(client.email ?: "")
        etAddressRegistration.setText(client.addressRegistration ?: "")
        etAddressActual.setText(client.addressActual ?: "")
        etStatus.setText(client.status.replace('_', ' ') ?: "")
        etRiskLevel.setText(client.riskLevel.replace('_', ' ') ?: "")
        etSource.setText(client.sourceName ?: "")
        etTags.setText(client.tags ?: "")
        etNotes.setText(client.notes ?: "")
    }

    private fun save() {
        lifecycleScope.launch {
            try {
                val body = ClientBody(
                    lastName = strOrNull(etLastName),
                    firstName = strOrNull(etFirstName),
                    middleName = strOrNull(etMiddleName),
                    birthDate = normalizeDate(strOrNull(etBirthDate)),
                    gender = strOrNull(etGender),
                    citizenship = strOrNull(etCitizenship),
                    inn = strOrNull(etInn),
                    snils = strOrNull(etSnils),
                    passportSeries = strOrNull(etPassportSeries),
                    passportNumber = strOrNull(etPassportNumber),
                    passportIssuedBy = strOrNull(etPassportIssuedBy),
                    passportIssueDate = normalizeDate(strOrNull(etPassportIssueDate)),
                    phone = strOrNull(etPhone),
                    email = strOrNull(etEmail),
                    status = strOrNull(etStatus) ?: "active",
                    riskLevel = strOrNull(etRiskLevel) ?: "low",
                    sourceId = resolveSourceId(strOrNull(etSource)),
                    tags = strOrNull(etTags),
                    notes = strOrNull(etNotes) ?: "",
                )

                if (body.lastName.isNullOrBlank() || body.firstName.isNullOrBlank()) {
                    Toast.makeText(this@ClientFormActivity, "Заполните фамилию и имя.", Toast.LENGTH_SHORT).show()
                    return@launch
                }

                if (modeCreate) {
                    val created = FsbApiClient.createClient(body)
                    startActivity(
                        android.content.Intent(this@ClientFormActivity, ClientDetailActivity::class.java)
                            .putExtra(ClientDetailActivity.EXTRA_CLIENT_ID, created.id),
                    )
                    finish()
                } else {
                    FsbApiClient.updateClient(clientId, body)
                    finish()
                }
            } catch (t: Throwable) {
                Toast.makeText(this@ClientFormActivity, "Ошибка сохранения: ${t.message}", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun strOrNull(edit: EditText): String? = edit.text?.toString()?.trim()?.takeIf { it.isNotEmpty() }

    private suspend fun resolveSourceId(name: String?): Int? {
        if (name.isNullOrBlank()) return null
        return try {
            val sources = FsbApiClient.sources()
            sources.firstOrNull { it.name.equals(name.trim(), ignoreCase = true) }?.id
        } catch (t: Throwable) {
            null
        }
    }

    private fun normalizeDate(value: String?): String? {
        if (value.isNullOrBlank()) return null
        val trimmed = value.trim()
        return if ('.' in trimmed) {
            val parts = trimmed.split(".")
            if (parts.size == 3) {
                val d = parts[0]
                val m = parts[1]
                val y = parts[2]
                String.format("%04d-%02d-%02d", y.toIntOrNull() ?: 1970, m.toIntOrNull() ?: 1, d.toIntOrNull() ?: 1)
            } else {
                trimmed
            }
        } else {
            trimmed
        }
    }
}
