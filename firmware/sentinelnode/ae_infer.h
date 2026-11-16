// Plain-C inference for the int8-weight autoencoder in ae_model.h.
// Mirrors sentinelnode/autoencoder.py (QuantAE._forward / error / health). No TFLite runtime needed.
#pragma once
#include <stdint.h>

// x: raw features in the order voltage_v, current_ma, temp_hot_c, temp_amb_c, vibration_g, ripple_mv
static float ae_error(const float x[AE_N_IN]) {
  float z[AE_N_IN], a[AE_MAX_W], b[AE_MAX_W];
  for (int i = 0; i < AE_N_IN; i++) { z[i] = (x[i] - AE_MEAN[i]) / AE_STD[i]; a[i] = z[i]; }
  for (int k = 0; k < AE_N_LAYERS; k++) {
    const int nin = AE_DIMS[k], nout = AE_DIMS[k + 1];
    for (int j = 0; j < nout; j++) {
      float acc = 0.0f;
      for (int i = 0; i < nin; i++) acc += a[i] * (float)AE_W[k][i * nout + j];
      acc = acc * AE_S[k] + AE_B[k][j];
      b[j] = (k < AE_N_LAYERS - 1 && acc < 0.0f) ? 0.0f : acc;   // ReLU on hidden layers
    }
    for (int j = 0; j < nout; j++) a[j] = b[j];
  }
  float e = 0.0f;
  for (int i = 0; i < AE_N_IN; i++) { float d = a[i] - z[i]; e += d * d; }
  return e / AE_N_IN;
}

// 0-100; 50 at the threshold, 0 at 3x the threshold or worse (same as QuantAE.health).
static int ae_health(float err) {
  float t = AE_THRESHOLD, h;
  h = (err <= t) ? 100.0f - 50.0f * err / t : 50.0f - 25.0f * (err - t) / t;
  if (h < 0) h = 0; if (h > 100) h = 100;
  return (int)(h + 0.5f);
}
