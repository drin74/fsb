package com.fsb.registry.network

import com.fsb.registry.FSBApplication
import com.fsb.registry.data.AuditLog
import com.fsb.registry.data.AuditPage
import com.fsb.registry.data.AuthResponse
import com.fsb.registry.data.Client
import com.fsb.registry.data.ClientBody
import com.fsb.registry.data.ClientEvent
import com.fsb.registry.data.ClientPage
import com.fsb.registry.data.Contact
import com.fsb.registry.data.ContactBody
import com.fsb.registry.data.EventBody
import com.fsb.registry.data.RefreshRequest
import com.fsb.registry.data.Source
import com.fsb.registry.data.SourcePage
import com.fsb.registry.data.Stats
import com.fsb.registry.data.User
import com.google.gson.annotations.SerializedName
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.HttpException
import retrofit2.Retrofit
import retrofit2.Response
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PATCH
import retrofit2.http.Path
import retrofit2.http.Query
import java.util.concurrent.TimeUnit

interface FsbApi {
    @POST("auth/login/")
    suspend fun login(@Body request: LoginRequest): AuthResponse

    @POST("auth/refresh/")
    suspend fun refresh(@Body request: RefreshRequest): AuthResponse

    @GET("stats/")
    suspend fun stats(): Stats

    @GET("clients/")
    suspend fun clients(
        @Query("page") page: Int,
        @Query("page_size") pageSize: Int,
        @Query("search") search: String?,
        @Query("status") status: String?,
        @Query("risk_level") riskLevel: String?,
    ): ClientPage<Client>

    @GET("clients/{clientId}/")
    suspend fun client(@Path("clientId") clientId: Int): Client

    @POST("clients/")
    suspend fun createClient(@Body body: ClientBody): Client

    @PATCH("clients/{clientId}/")
    suspend fun updateClient(@Path("clientId") clientId: Int, @Body body: ClientBody): Client

    @DELETE("clients/{clientId}/")
    suspend fun deleteClient(@Path("clientId") clientId: Int): Response<Unit>

    @POST("contacts/")
    suspend fun addContact(@Body body: ContactBody): Contact

    @POST("events/")
    suspend fun addEvent(@Body body: EventBody): ClientEvent

    @DELETE("contacts/{id}/")
    suspend fun deleteContact(@Path("id") id: Int): Response<Unit>

    @GET("sources/")
    suspend fun sources(@Query("page_size") pageSize: Int = 100): SourcePage

    @GET("audit/")
    suspend fun audit(
        @Query("page") page: Int,
        @Query("page_size") pageSize: Int,
        @Query("search") search: String?,
        @Query("action") action: String?,
    ): AuditPage
}

data class LoginRequest(
    @SerializedName("username") val username: String,
    @SerializedName("password") val password: String,
)

object FsbApiClient {

    private var retrofit: Retrofit? = null

    fun getClient(): FsbApi {
        if (retrofit == null) {
            val app = FSBApplication.instance
            val okHttp = OkHttpClient.Builder()
                .addInterceptor(HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BODY })
                .addInterceptor { chain ->
                    val token = app.getAccessToken()
                    val request = chain.request().newBuilder().apply {
                        if (!token.isNullOrBlank()) {
                            addHeader("Authorization", "Bearer $token")
                        }
                    }.build()
                    chain.proceed(request)
                }
                .connectTimeout(25, java.util.concurrent.TimeUnit.SECONDS)
                .readTimeout(40, java.util.concurrent.TimeUnit.SECONDS)
                .build()
            retrofit = Retrofit.Builder()
                .baseUrl("http://10.0.2.2:8010/api/")
                .client(okHttp)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
        }
        return retrofit!!.create(FsbApi::class.java)
    }

    private suspend fun <T> request(block: suspend FsbApi.() -> T): T {
        val api = getClient()
        return kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
            try {
                return@withContext api.block()
            } catch (e: HttpException) {
                val code = e.code()
                if (code == 401) {
                    val refreshed = refresh()
                    if (refreshed) {
                        @Suppress("UNCHECKED_CAST")
                        return@withContext api.block() as T
                    }
                }
                throw e
            }
        }
    }

    suspend fun refresh(): Boolean {
        val refreshToken = FSBApplication.instance.getRefreshToken() ?: return false
        if (refreshToken.isBlank()) return false
        val response = request {
            val tokenResponse = refresh(@Body RefreshRequest(refreshToken))
            FSBApplication.instance.saveTokens(tokenResponse.access ?: "", tokenResponse.refresh ?: refreshToken)
            true
        }
        return response
    }

    suspend fun login(username: String, password: String): AuthResponse {
        val auth = request {
            val tokenResponse = login(@Body LoginRequest(username, password))
            FSBApplication.instance.saveTokens(tokenResponse.access ?: "", tokenResponse.refresh ?: "")
            tokenResponse
        }
        return auth
    }

    suspend fun stats(): Stats = request { stats() }

    suspend fun clients(
        page: Int,
        search: String?,
        status: String?,
        riskLevel: String?,
    ): ClientPage<Client> = request {
        clients(
            page = page,
            pageSize = 20,
            search = search,
            status = status,
            riskLevel = riskLevel,
        )
    }

    suspend fun getClient(clientId: Int): Client = request { client(clientId) }

    suspend fun createClient(body: ClientBody): Client = request { createClient(body) }

    suspend fun updateClient(clientId: Int, body: ClientBody): Client = request { updateClient(clientId, body) }

    suspend fun deleteClient(clientId: Int): Boolean {
        val response = request { deleteClient(clientId) }
        return response.isSuccessful || response.code() == 204
    }

    suspend fun addContact(body: ContactBody): Contact = request { addContact(body) }

    suspend fun addEvent(body: EventBody): ClientEvent = request { addEvent(body) }

    suspend fun deleteContact(contactId: Int): Boolean {
        val response = request { deleteContact(contactId) }
        return response.isSuccessful || response.code() == 204
    }

    suspend fun sources(): List<Source> = request { sources(pageSize = 100) }.results.map { it }

    suspend fun audit(page: Int, search: String?, action: String?): AuditPage = request {
        audit(page = page, pageSize = 50, search = search, action = action)
    }
}
