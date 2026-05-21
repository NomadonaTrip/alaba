package com.orbanforest.alaba.data.api.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class ErrorResponse(val detail: ErrorDetail)

@JsonClass(generateAdapter = true)
data class ErrorDetail(
    val error: String? = null,
    val reason: String? = null,
    @field:com.squareup.moshi.Json(name = "attempts_remaining") val attemptsRemaining: Int? = null,
    @field:com.squareup.moshi.Json(name = "unlock_at") val unlockAt: String? = null,
)
