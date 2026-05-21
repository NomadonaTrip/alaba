package com.orbanforest.alaba

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.Surface
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.compose.foundation.layout.fillMaxSize
import androidx.navigation.compose.rememberNavController
import com.orbanforest.alaba.data.auth.AuthEvent
import com.orbanforest.alaba.data.auth.AuthEventBus
import com.orbanforest.alaba.data.auth.TokenStore
import com.orbanforest.alaba.ui.nav.AlabaNavHost
import com.orbanforest.alaba.ui.theme.AlabaTheme
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    @Inject lateinit var authEventBus: AuthEventBus
    @Inject lateinit var tokenStore: TokenStore

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AlabaTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    val navController = rememberNavController()
                    val startDestination = if (tokenStore.hasJwt()) "signed_in" else "phone_entry"

                    LaunchedEffect(Unit) {
                        authEventBus.events.collect { event ->
                            when (event) {
                                AuthEvent.DeviceDeactivated -> {
                                    tokenStore.clear()
                                    navController.navigate("device_deactivated") { popUpTo(0) }
                                }
                                AuthEvent.TokenExpired -> {
                                    tokenStore.clear()
                                    navController.navigate("phone_entry") { popUpTo(0) }
                                }
                            }
                        }
                    }

                    AlabaNavHost(navController, startDestination, tokenStore)
                }
            }
        }
    }
}
