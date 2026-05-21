package com.orbanforest.alaba.data.api.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class OtpRequestBody(val phone: String)
