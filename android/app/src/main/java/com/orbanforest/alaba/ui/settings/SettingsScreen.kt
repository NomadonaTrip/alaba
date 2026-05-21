package com.orbanforest.alaba.ui.settings

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.orbanforest.alaba.ui.home.SignedInPlaceholderViewModel

@Composable
fun SettingsScreen(
    onDevices: () -> Unit,
    onLogout: () -> Unit,
    viewModel: SignedInPlaceholderViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Column(modifier = Modifier.fillMaxSize()) {
        Spacer(Modifier.height(16.dp))
        Text("Settings", style = MaterialTheme.typography.headlineSmall, modifier = Modifier.padding(horizontal = 20.dp))
        HorizontalDivider(modifier = Modifier.padding(top = 16.dp))

        Column(modifier = Modifier.padding(horizontal = 20.dp, vertical = 18.dp)) {
            Text("ACCOUNT", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(8.dp))
            Text(state.phone ?: "—", style = MaterialTheme.typography.bodyLarge)
        }
        HorizontalDivider()

        SettingsRow(label = "Devices", subtitle = "Manage authorized devices", onClick = onDevices)
        HorizontalDivider()
        SettingsRow(label = "Terms and Conditions", subtitle = null, onClick = null)
        HorizontalDivider()
        SettingsRow(label = "Privacy Policy", subtitle = null, onClick = null)

        Spacer(Modifier.height(32.dp))
        OutlinedButton(
            onClick = onLogout,
            modifier = Modifier.fillMaxWidth().padding(horizontal = 20.dp),
            colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.error),
        ) { Text("Log out") }
    }
}

@Composable
private fun SettingsRow(label: String, subtitle: String?, onClick: (() -> Unit)?) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier)
            .padding(horizontal = 20.dp, vertical = 16.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(label, style = MaterialTheme.typography.bodyLarge)
            if (subtitle != null) {
                Spacer(Modifier.height(2.dp))
                Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
        if (onClick != null) Text("›", color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}
