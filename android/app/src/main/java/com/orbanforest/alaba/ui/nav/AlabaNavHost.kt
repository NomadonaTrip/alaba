package com.orbanforest.alaba.ui.nav

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.orbanforest.alaba.data.api.dto.ActiveDeviceSummary
import com.orbanforest.alaba.data.auth.TokenStore
import com.orbanforest.alaba.ui.auth.DeviceCapReachedScreen
import com.orbanforest.alaba.ui.auth.DeviceDeactivatedScreen
import com.orbanforest.alaba.ui.auth.OtpEntryScreen
import com.orbanforest.alaba.ui.auth.PhoneEntryScreen
import com.orbanforest.alaba.ui.home.SignedInPlaceholderScreen
import com.orbanforest.alaba.ui.settings.DevicesScreen
import com.orbanforest.alaba.ui.settings.SettingsScreen

// In-memory transient state for the device-cap flow. The 409 payload
// is too large to put into nav args; we hand it off via this holder.
object DeviceCapHandoff {
    var devices: List<ActiveDeviceSummary>? = null
    var verifyTicket: String? = null
    var phone: String? = null

    fun consume(): Triple<List<ActiveDeviceSummary>, String, String>? {
        val d = devices; val t = verifyTicket; val p = phone
        return if (d != null && t != null && p != null) {
            devices = null; verifyTicket = null; phone = null
            Triple(d, t, p)
        } else null
    }
}

@Composable
fun AlabaNavHost(
    navController: NavHostController,
    startDestination: String,
    tokenStore: TokenStore,
) {
    NavHost(navController = navController, startDestination = startDestination) {
        composable("phone_entry") {
            PhoneEntryScreen(
                onCodeSent = { phone ->
                    navController.navigate("otp_entry/${phone.removePrefix("+").trim()}")
                }
            )
        }
        composable(
            "otp_entry/{phoneE164}",
            arguments = listOf(navArgument("phoneE164") { type = NavType.StringType }),
        ) { backStack ->
            val phone = "+" + (backStack.arguments?.getString("phoneE164") ?: "")
            OtpEntryScreen(
                phone = phone,
                onSignedIn = {
                    navController.navigate("signed_in") {
                        popUpTo("phone_entry") { inclusive = true }
                    }
                },
                onDeviceCapReached = { devices, ticket, phoneArg ->
                    DeviceCapHandoff.devices = devices
                    DeviceCapHandoff.verifyTicket = ticket
                    DeviceCapHandoff.phone = phoneArg
                    navController.navigate("device_cap_reached")
                },
                onBack = { navController.popBackStack() },
            )
        }
        composable("device_cap_reached") {
            val handoff = remember { DeviceCapHandoff.consume() }
            if (handoff == null) {
                LaunchedEffect(Unit) { navController.popBackStack() }
            } else {
                val (devices, ticket, phone) = handoff
                DeviceCapReachedScreen(
                    devices = devices,
                    verifyTicket = ticket,
                    phone = phone,
                    onSignedIn = {
                        navController.navigate("signed_in") {
                            popUpTo("phone_entry") { inclusive = true }
                        }
                    },
                    onCancel = { navController.popBackStack("phone_entry", inclusive = false) },
                )
            }
        }
        composable("device_deactivated") {
            DeviceDeactivatedScreen(onSignInAgain = {
                navController.navigate("phone_entry") { popUpTo(0) }
            })
        }
        composable("signed_in") {
            SignedInPlaceholderScreen(onManageDevices = { navController.navigate("settings") })
        }
        composable("settings") {
            SettingsScreen(
                onDevices = { navController.navigate("devices") },
                onLogout = {
                    tokenStore.clear()
                    navController.navigate("phone_entry") { popUpTo(0) }
                },
            )
        }
        composable("devices") {
            DevicesScreen(
                currentUserDeviceId = tokenStore.readUserDeviceId(),
                onBack = { navController.popBackStack() },
            )
        }
    }
}
