package com.orbanforest.alaba

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.orbanforest.alaba.data.api.HealthApi
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject lateinit var healthApi: HealthApi

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    HealthScreen(healthApi)
                }
            }
        }
    }
}

@Composable
fun HealthScreen(api: HealthApi) {
    var result by remember { mutableStateOf("Calling /health...") }

    LaunchedEffect(Unit) {
        result = try {
            val resp = api.getHealth()
            "status=${resp.status}\nservice=${resp.service}\nchecks=${resp.checks}"
        } catch (e: Throwable) {
            "Error: ${e.javaClass.simpleName}: ${e.message}"
        }
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(text = "Alaba — backend ping", style = MaterialTheme.typography.headlineSmall)
        Text(text = result, modifier = Modifier.padding(top = 16.dp))
    }
}
