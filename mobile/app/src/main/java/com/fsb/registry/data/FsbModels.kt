package com.fsb.registry.data

import com.google.gson.annotations.SerializedName

data class LoginRequest(
    @SerializedName("username") val username: String,
    @SerializedName("password") val password: String,
)

data class RefreshRequest(
    @SerializedName("refresh") val refresh: String,
)

data class AuthResponse(
    @SerializedName("access") val access: String?,
    @SerializedName("refresh") val refresh: String?,
    @SerializedName("user") val user: User? = null,
)

data class User(
    @SerializedName("id") val id: Int,
    @SerializedName("username") val username: String,
    @SerializedName("full_name") val fullName: String?,
    @SerializedName("display_name") val displayName: String?,
    @SerializedName("email") val email: String?,
    @SerializedName("phone") val phone: String?,
    @SerializedName("department") val department: String?,
    @SerializedName("position") val position: String?,
    @SerializedName("role") val role: Int?,
    @SerializedName("role_name") val roleName: String?,
    @SerializedName("role_code") val roleCode: String?,
    @SerializedName("is_active") val isActive: Boolean,
    @SerializedName("is_superuser") val isSuperuser: Boolean,
    @SerializedName("date_joined") val dateJoined: String?,
    @SerializedName("last_login") val lastLogin: String?,
)

data class Source(
    @SerializedName("id") val id: Int,
    @SerializedName("name") val name: String,
    @SerializedName("kind") val kind: String,
    @SerializedName("kind_display") val kindDisplay: String?,
    @SerializedName("url") val url: String?,
    @SerializedName("description") val description: String?,
    @SerializedName("is_active") val isActive: Boolean,
    @SerializedName("clients_count") val clientsCount: Int?,
    @SerializedName("created_at") val createdAt: String?,
)

data class SourcePage(
    @SerializedName("count") val count: Int,
    @SerializedName("next") val next: String?,
    @SerializedName("previous") val previous: String?,
    @SerializedName("results") val results: List<Source>,
)

data class Contact(
    @SerializedName("id") val id: Int,
    @SerializedName("client") val client: Int?,
    @SerializedName("kind") val kind: String,
    @SerializedName("kind_display") val kindDisplay: String?,
    @SerializedName("value") val value: String,
    @SerializedName("comment") val comment: String?,
    @SerializedName("is_primary") val isPrimary: Boolean,
    @SerializedName("created_at") val createdAt: String?,
)

data class ContactBody(
    @SerializedName("client") val client: Int,
    @SerializedName("kind") val kind: String,
    @SerializedName("value") val value: String,
    @SerializedName("comment") val comment: String? = null,
    @SerializedName("is_primary") val isPrimary: Boolean = false,
)

data class ClientData(
    @SerializedName("id") val id: Int,
    @SerializedName("client") val client: Int?,
    @SerializedName("category") val category: String,
    @SerializedName("category_display") val categoryDisplay: String?,
    @SerializedName("key") val key: String,
    @SerializedName("value") val value: String,
    @SerializedName("source") val source: Int?,
    @SerializedName("source_name") val sourceName: String?,
    @SerializedName("verified") val verified: Boolean,
    @SerializedName("created_at") val createdAt: String?,
)

data class EventBody(
    @SerializedName("client") val client: Int,
    @SerializedName("event_type") val eventType: String,
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String? = null,
)

data class ClientEvent(
    @SerializedName("id") val id: Int,
    @SerializedName("client") val client: Int?,
    @SerializedName("event_type") val eventType: String,
    @SerializedName("event_type_display") val eventTypeDisplay: String?,
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String?,
    @SerializedName("source") val source: Int?,
    @SerializedName("source_name") val sourceName: String?,
    @SerializedName("occurred_at") val occurredAt: String?,
    @SerializedName("created_by") val createdBy: Int?,
    @SerializedName("created_by_name") val createdByName: String?,
    @SerializedName("created_at") val createdAt: String?,
)

data class ClientDocument(
    @SerializedName("id") val id: Int,
    @SerializedName("client") val client: Int?,
    @SerializedName("title") val title: String,
    @SerializedName("doc_type") val docType: String?,
    @SerializedName("file") val file: String?,
    @SerializedName("file_url") val fileUrl: String?,
    @SerializedName("uploaded_by_name") val uploadedByName: String?,
    @SerializedName("uploaded_at") val uploadedAt: String?,
)

data class Consent(
    @SerializedName("id") val id: Int,
    @SerializedName("client") val client: Int?,
    @SerializedName("consent_type") val consentType: String,
    @SerializedName("granted") val granted: Boolean,
    @SerializedName("valid_until") val validUntil: String?,
    @SerializedName("comment") val comment: String?,
    @SerializedName("created_at") val createdAt: String?,
)

data class Client(
    @SerializedName("id") val id: Int,
    @SerializedName("last_name") val lastName: String?,
    @SerializedName("first_name") val firstName: String?,
    @SerializedName("middle_name") val middleName: String?,
    @SerializedName("full_name") val fullName: String?,
    @SerializedName("birth_date") val birthDate: String?,
    @SerializedName("age") val age: Int?,
    @SerializedName("gender") val gender: String?,
    @SerializedName("gender_display") val genderDisplay: String?,
    @SerializedName("citizenship") val citizenship: String?,
    @SerializedName("inn") val inn: String?,
    @SerializedName("snils") val snils: String?,
    @SerializedName("passport_series") val passportSeries: String?,
    @SerializedName("passport_number") val passportNumber: String?,
    @SerializedName("passport_issued_by") val passportIssuedBy: String?,
    @SerializedName("passport_issue_date") val passportIssueDate: String?,
    @SerializedName("address_registration") val addressRegistration: String?,
    @SerializedName("address_actual") val addressActual: String?,
    @SerializedName("phone") val phone: String?,
    @SerializedName("email") val email: String?,
    @SerializedName("status") val status: String,
    @SerializedName("risk_level") val riskLevel: String,
    @SerializedName("tags") val tags: String?,
    @SerializedName("notes") val notes: String?,
    @SerializedName("photo") val photo: String?,
    @SerializedName("source") val sourceId: Int?,
    @SerializedName("source_name") val sourceName: String?,
    @SerializedName("created_by") val createdBy: Int?,
    @SerializedName("created_by_name") val createdByName: String?,
    @SerializedName("created_at") val createdAt: String?,
    @SerializedName("updated_at") val updatedAt: String?,
    @SerializedName("contacts") val contacts: List<Contact>? = null,
    @SerializedName("data_items") val dataItems: List<ClientData>? = null,
    @SerializedName("events") val events: List<ClientEvent>? = null,
    @SerializedName("documents") val documents: List<ClientDocument>? = null,
    @SerializedName("consents") val consents: List<Consent>? = null,
)

data class ClientBody(
    @SerializedName("last_name") val lastName: String?,
    @SerializedName("first_name") val firstName: String?,
    @SerializedName("middle_name") val middleName: String?,
    @SerializedName("birth_date") val birthDate: String?,
    @SerializedName("gender") val gender: String?,
    @SerializedName("citizenship") val citizenship: String?,
    @SerializedName("inn") val inn: String?,
    @SerializedName("snils") val snils: String?,
    @SerializedName("passport_series") val passportSeries: String?,
    @SerializedName("passport_number") val passportNumber: String?,
    @SerializedName("passport_issued_by") val passportIssuedBy: String?,
    @SerializedName("passport_issue_date") val passportIssueDate: String?,
    @SerializedName("phone") val phone: String?,
    @SerializedName("email") val email: String?,
    @SerializedName("status") val status: String,
    @SerializedName("risk_level") val riskLevel: String,
    @SerializedName("source") val sourceId: Int?,
    @SerializedName("tags") val tags: String?,
    @SerializedName("notes") val notes: String?,
)

data class Stats(
    @SerializedName("total") val total: Int,
    @SerializedName("new_week") val newWeek: Int,
    @SerializedName("checking") val checking: Int,
    @SerializedName("high_risk") val highRisk: Int,
    @SerializedName("by_status") val byStatus: List<StatusCount>? = null,
    @SerializedName("by_risk") val byRisk: List<RiskCount>? = null,
    @SerializedName("sources") val sources: List<Source>? = null,
)

data class StatusCount(
    @SerializedName("status") val status: String,
    @SerializedName("count") val count: Int,
)

data class RiskCount(
    @SerializedName("risk_level") val riskLevel: String,
    @SerializedName("count") val count: Int,
)

data class AuditLog(
    @SerializedName("id") val id: Int,
    @SerializedName("user") val userId: Int?,
    @SerializedName("user_name") val userName: String?,
    @SerializedName("action") val action: String,
    @SerializedName("action_display") val actionDisplay: String?,
    @SerializedName("model_name") val modelName: String?,
    @SerializedName("object_id") val objectId: String?,
    @SerializedName("object_repr") val objectRepr: String?,
    @SerializedName("details") val details: Map<String, Any?>?,
    @SerializedName("ip") val ip: String?,
    @SerializedName("created_at") val createdAt: String?,
)

data class AuditPage(
    @SerializedName("count") val count: Int,
    @SerializedName("next") val next: String?,
    @SerializedName("previous") val previous: String?,
    @SerializedName("results") val results: List<AuditLog>,
)

data class ClientPage<T>(
    @SerializedName("count") val count: Int,
    @SerializedName("next") val next: String?,
    @SerializedName("previous") val previous: String?,
    @SerializedName("results") val results: List<T>,
)
