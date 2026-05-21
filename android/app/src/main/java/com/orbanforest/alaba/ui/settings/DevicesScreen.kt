package com.orbanforest.alaba.ui.settings

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.orbanforest.alaba.data.auth.TokenStore
import com.orbanforest.alaba.ui.components.ConfirmBottomSheet
import com.orbanforest.alaba.ui.components.ThisDevicePill

@Composable
fun DevicesScreen(
    currentUserDeviceId: String?,
    onBack: () -> Unit,
    viewModel: DevicesViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Column(modifier = Modifier.fillMaxSize().padding(24.dp).verticalScroll(rememberScrollState())) {
        TextButton(onClick = onBack) { Text("← Settings") }
        Spacer(Modifier.height(8.dp))
        Text("Devices", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(6.dp))
        Text(
            "You're using ${state.activeCount} of ${state.cap} device slots.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        if (state.cooldownUnlockAt != null) {
            Spacer(Modifier.height(16.dp))
            Surface(
                color = MaterialTheme.colorScheme.tertiaryContainer.copy(alpha = 0.3f),
                shape = MaterialTheme.shapes.small,
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text("Cooldown active", style = MaterialTheme.typography.labelMedium)
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "You can deactivate another device after ${state.cooldownUnlockAt!!.take(10)}.",
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        state.devices.filter { it.deactivatedAt == null }.forEach { d ->
            DeviceRow(
                title = d.displayName ?: d.model ?: "Unknown",
                subtitle = "Added ${d.activatedAt.take(10)}",
                isCurrent = d.isCurrent,
                cooldownActive = state.cooldownUnlockAt != null,
                onDeactivate = { viewModel.askConfirmDeactivate(d.id) },
            )
            Spacer(Modifier.height(8.dp))
        }

        if (state.devices.any { it.deactivatedAt != null }) {
            Spacer(Modifier.height(16.dp))
            Text("DEACTIVATED", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(8.dp))
            state.devices.filter { it.deactivatedAt != null }.forEach { d ->
                DeviceRow(
                    title = d.displayName ?: d.model ?: "Unknown",
                    subtitle = "Deactivated ${d.deactivatedAt?.take(10)}",
                    isCurrent = false,
                    cooldownActive = true,  // can't deactivate an already-deactivated device
                    onDeactivate = null,
                )
                Spacer(Modifier.height(8.dp))
            }
        }

        if (state.error != null) {
            Spacer(Modifier.height(8.dp))
            Text(state.error!!, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
        }
    }

    val confirmId = state.confirmDeactivateId
    if (confirmId != null) {
        val dev = state.devices.find { it.id == confirmId } ?: return
        val isCurrent = dev.id == currentUserDeviceId
        ConfirmBottomSheet(
            title = if (isCurrent) "Deactivate this device?" else "Deactivate ${dev.displayName ?: "device"}?",
            body = if (isCurrent)
                "You'll be signed out and lose access to all downloaded films on this phone. You can re-authorize this device in 90 days."
            else
                "Films downloaded on that device will continue to play offline but it can't connect to Alaba anymore. You can reactivate it in 90 days.",
            confirmLabel = if (isCurrent) "Deactivate and sign out" else "Deactivate",
            destructive = isCurrent,
            onConfirm = { viewModel.confirmDeactivate(currentUserDeviceId) },
            onDismiss = viewModel::cancelConfirm,
        )
    }
}

@Composable
private fun DeviceRow(
    title: String,
    subtitle: String,
    isCurrent: Boolean,
    cooldownActive: Boolean,
    onDeactivate: (() -> Unit)?,
) {
    OutlinedCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                Text(title, style = MaterialTheme.typography.bodyLarge)
                if (isCurrent) {
                    Spacer(Modifier.width(8.dp))
                    ThisDevicePill()
                }
            }
            Spacer(Modifier.height(2.dp))
            Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            if (onDeactivate != null) {
                Spacer(Modifier.height(12.dp))
                OutlinedButton(
                    onClick = onDeactivate,
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !cooldownActive,
                ) {
                    Text(if (cooldownActive) "Deactivate (locked)" else "Deactivate")
                }
            }
        }
    }
}
