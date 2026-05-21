package com.orbanforest.alaba.ui.auth

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.orbanforest.alaba.data.api.dto.ActiveDeviceSummary
import com.orbanforest.alaba.ui.components.DeviceCard

@Composable
fun DeviceCapReachedScreen(
    devices: List<ActiveDeviceSummary>,
    verifyTicket: String,
    phone: String,
    onSignedIn: () -> Unit,
    onCancel: () -> Unit,
    viewModel: DeviceCapReachedViewModel = hiltViewModel(),
) {
    LaunchedEffect(Unit) {
        viewModel.initialize(devices, verifyTicket, phone)
        viewModel.events.collect { event ->
            when (event) {
                DeviceCapEvent.SignedIn -> onSignedIn()
                DeviceCapEvent.Cancel -> onCancel()
            }
        }
    }
    val state by viewModel.state.collectAsStateWithLifecycle()
    val s = state ?: return

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp).verticalScroll(rememberScrollState()),
    ) {
        Spacer(Modifier.height(8.dp))
        TextButton(onClick = onCancel) { Text("← Back") }
        Spacer(Modifier.height(16.dp))
        Text("You're at your 2-device limit", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(8.dp))
        Text(
            "Pick a device to deactivate. You'll lose access to downloaded films on it. You can only deactivate one device every 90 days.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(24.dp))

        s.devices.forEach { dev ->
            DeviceCard(
                title = dev.displayName ?: dev.model ?: "Unknown device",
                subtitle = "Activated ${dev.activatedAt.take(10)}",
                selected = (dev.id == s.selectedDeviceId),
                onClick = { viewModel.selectDevice(dev.id) },
                modifier = Modifier.padding(bottom = 8.dp),
            )
        }

        if (s.errorMessage != null) {
            Spacer(Modifier.height(8.dp))
            Text(s.errorMessage, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
        }

        Spacer(Modifier.height(20.dp))
        Button(
            onClick = viewModel::confirm,
            modifier = Modifier.fillMaxWidth(),
            enabled = s.selectedDeviceId != null && !s.submitting,
            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error),
        ) {
            Text(if (s.submitting) "Deactivating..." else "Deactivate & continue")
        }
        Spacer(Modifier.height(8.dp))
        TextButton(onClick = viewModel::cancel, modifier = Modifier.fillMaxWidth()) {
            Text("Cancel")
        }
    }
}
