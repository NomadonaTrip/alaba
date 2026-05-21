package com.orbanforest.alaba.data.auth

import io.mockk.every
import io.mockk.mockk
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class AuthInterceptorTest {
    @Test
    fun `attaches Authorization header when token present`() {
        val server = MockWebServer().apply { start(); enqueue(MockResponse().setBody("ok")) }
        val tokenStore = mockk<TokenStore>()
        every { tokenStore.readJwt() } returns "my-jwt-123"
        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(tokenStore))
            .build()
        val request = Request.Builder().url(server.url("/")).build()
        client.newCall(request).execute().use { /* drop body */ }
        val sent = server.takeRequest()
        assertEquals("Bearer my-jwt-123", sent.getHeader("Authorization"))
        server.shutdown()
    }

    @Test
    fun `no header when token null`() {
        val server = MockWebServer().apply { start(); enqueue(MockResponse().setBody("ok")) }
        val tokenStore = mockk<TokenStore>()
        every { tokenStore.readJwt() } returns null
        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(tokenStore))
            .build()
        val request = Request.Builder().url(server.url("/")).build()
        client.newCall(request).execute().use { }
        val sent = server.takeRequest()
        assertNull(sent.getHeader("Authorization"))
        server.shutdown()
    }
}
