// Neoclo Typhoon Ambient Edition: experimental parameter remapping layer.
// This file is compiled as part of SuperParasites, not a standalone firmware.
#ifndef NEOCLO_TYPHOON_AMBIENT_MODES_H_
#define NEOCLO_TYPHOON_AMBIENT_MODES_H_
#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include "supercell/dsp/parameters.h"

namespace clouds {
class AmbientModes {
 public:
  AmbientModes() { Init(); }
  void Init() {
    last_mode_ = 255; random_state_ = 0x2ac015e5u;
    random_timer_ = drift_ = target_drift_ = 0.0f;
    slow_phase_ = flutter_phase_ = auto_capture_timer_ = 0.0f;
  }
  // Native SuperParasites slots:
  // 0 Clouds, 1 Endless, 2 Tape, 3 Spectral Drift, 4 Shimmer,
  // 5 Harmonic Drone, 6 Dissolve, 7 Spectral Ghost.
  void Apply(uint8_t mode, Parameters* p, size_t block_size) {
    if (!p || mode >= 8 || mode == 0) return;
    if (mode != last_mode_) {
      last_mode_ = mode;
      random_timer_ = auto_capture_timer_ = drift_ = target_drift_ = 0.0f;
    }
    const float dt = static_cast<float>(block_size) / 32000.0f;
    random_timer_ -= dt;
    if (random_timer_ <= 0.0f) {
      random_timer_ = 3.5f + 8.0f * Random01();
      target_drift_ = 2.0f * Random01() - 1.0f;
    }
    drift_ += Clamp(dt * 0.23f) * (target_drift_ - drift_);
    slow_phase_ = Wrap01(slow_phase_ + dt * 0.13f);
    flutter_phase_ = Wrap01(flutter_phase_ + dt * 5.2f);
    const float slow = Triangle(slow_phase_);
    const float flutter = Triangle(flutter_phase_);
    switch (mode) {
      case 1: {  // ENDLESS: adapting existing WSOLA stretch; not a new Endless DSP.
        const float travel = p->position;
        p->position = Clamp(0.09f + 0.84f * travel +
                           (0.008f + 0.028f * p->density) * drift_);
        p->size = Clamp(0.38f + 0.61f * p->size);
        p->density = Clamp(0.28f + 0.59f * p->density);
        p->texture = Clamp(0.30f + 0.42f * p->texture);
        p->feedback = Clamp(0.08f + 0.68f * p->feedback);
        p->reverb = Clamp(0.30f + 0.65f * p->reverb);
        p->pitch = ClampPitch(p->pitch + 0.06f * slow);
        break;
      }
      case 2: {  // TAPE MEMORY: looping delay with flutter.
        const float age = p->texture;
        p->pitch = ClampPitch(p->pitch +
                              age * (0.28f * slow + 0.045f * flutter));
        p->texture = Clamp(0.16f + 0.49f * age);
        p->feedback = Clamp(0.08f + 0.79f * p->feedback);
        p->reverb = Clamp(0.12f + 0.72f * p->reverb);
        p->density = Clamp(0.09f + 0.52f * p->density);
        break;
      }
      case 3: {  // SPECTRAL DRIFT: original spectral engine with slow movement.
        const float motion = p->density;
        p->position = Clamp(p->position + 0.05f * motion * drift_);
        p->size = Clamp(0.38f + 0.60f * p->size);
        p->density = Clamp(0.07f + 0.47f * motion);
        p->texture = Clamp(0.22f + 0.57f * p->texture);
        p->pitch = ClampPitch(p->pitch + 0.16f * motion * slow);
        p->reverb = Clamp(0.28f + 0.67f * p->reverb);
        break;
      }
      case 4: {  // SHIMMER CATHEDRAL: Oliverb with longer decay and slow mod.
        p->position = Clamp(0.03f + 0.60f * p->position);
        p->size = Clamp(0.52f + 0.47f * p->size);
        p->density = Clamp(0.62f + 0.36f * p->density);
        p->texture = Clamp(0.18f + 0.66f * p->texture);
        p->feedback = Clamp(0.015f + 0.24f * p->feedback);
        p->reverb = Clamp(0.02f + 0.45f * p->reverb);
        p->pitch = ClampPitch(p->pitch * 0.5f + 0.08f * drift_);
        break;
      }
      case 5: {  // HARMONIC DRONE: original resonator with gentler settings.
        p->position = Clamp(0.12f + 0.75f * p->position);
        p->density = Clamp(0.45f + 0.39f * p->density);
        p->texture = Clamp(0.25f + 0.50f * p->texture);
        p->feedback = Clamp(0.20f + 0.55f * p->feedback);
        p->reverb = Clamp(0.15f + 0.72f * p->reverb);
        p->pitch = ClampPitch(p->pitch + 0.12f * drift_);
        break;
      }
      case 6: {  // DISSOLVE DELAY: automatic slice capture.
        const float motion = p->density;
        const float spacing = 1.5f + (1.0f - p->size) * 4.5f;
        if (!p->freeze) {
          auto_capture_timer_ += dt;
          if (auto_capture_timer_ >= spacing) {
            auto_capture_timer_ = 0.0f;
            p->capture = true;
          }
        }
        p->kammerl.probability = Clamp(0.32f + 0.61f * motion);
        p->kammerl.clock_divider = Clamp(0.08f + 0.12f * p->size);
        p->kammerl.slice_selection = Clamp(p->position + 0.08f * drift_);
        p->kammerl.slice_modulation = Clamp(0.12f + 0.35f * p->texture);
        p->kammerl.size_modulation = Clamp(0.10f + 0.22f * p->size);
        p->kammerl.pitch_mode = Clamp(0.01f + 0.18f * p->texture);
        p->reverb = Clamp(0.19f + 0.44f * p->reverb);
        break;
      }
      case 7: {  // SPECTRAL GHOST: spectral cloud with milder modulation.
        const float motion = p->density;
        p->position = Clamp(p->position + 0.018f * motion * drift_);
        p->density = Clamp(0.08f + 0.65f * motion);
        p->texture = Clamp(0.12f + 0.65f * p->texture);
        p->size = Clamp(0.37f + 0.58f * p->size);
        p->pitch = ClampPitch(p->pitch + 0.10f * motion * slow);
        p->reverb = Clamp(0.22f + 0.70f * p->reverb);
        p->kammerl.pitch_mode = Clamp(0.09f * p->feedback);
        break;
      }
    }
  }
 private:
  static float Clamp(float x) {
    return x < 0.0f ? 0.0f : x > 1.0f ? 1.0f : x;
  }
  static float ClampPitch(float x) {
    return x < -48.0f ? -48.0f : x > 48.0f ? 48.0f : x;
  }
  static float Wrap01(float x) { return x >= 1.0f ? x - 1.0f : x; }
  static float Triangle(float p) { return 1.0f - 4.0f * fabsf(p - 0.5f); }
  float Random01() {
    random_state_ ^= random_state_ << 13;
    random_state_ ^= random_state_ >> 17;
    random_state_ ^= random_state_ << 5;
    return static_cast<float>(random_state_ & 0x00ffffffu) / 16777215.0f;
  }
  uint8_t last_mode_;
  uint32_t random_state_;
  float random_timer_, drift_, target_drift_, slow_phase_, flutter_phase_, auto_capture_timer_;
};
}  // namespace clouds
#endif
