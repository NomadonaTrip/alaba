package com.orbanforest.alaba.data.api

import com.squareup.moshi.JsonClass
import retrofit2.http.GET

@JsonClass(generateAdapter = true)
data class HealthResponse(
    val status: String,
    val service: String,
    val checks: Map<String, String>
)

interface HealthApi {
    @GET("/health")
    suspend fun getHealth(): HealthResponse
}
