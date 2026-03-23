#pragma once

#include "esphome/core/component.h"
#include "esphome/core/automation.h"
#include "esphome/components/microphone/microphone.h"
#include <vector>

namespace esphome {
namespace beep_detector {

struct CalibrationResult {
  float frequency{0.0f};
  float amplitude{0.0f};
};

class BeepDetector : public Component {
 public:
  void setup() override;
  void loop() override;
  float get_setup_priority() const override { return setup_priority::AFTER_CONNECTION; }

  void set_microphone(microphone::Microphone *mic) { this->mic_ = mic; }
  void set_target_frequency(float freq) { this->target_frequency_ = freq; }
  void set_frequency_tolerance(float tol) { this->frequency_tolerance_ = tol; }
  void set_amplitude_min(float val) { this->amplitude_min_ = val; }
  void set_amplitude_max(float val) { this->amplitude_max_ = val; }
  void set_min_duration_ms(int val) { this->min_duration_ms_ = val; }
  void set_max_duration_ms(int val) { this->max_duration_ms_ = val; }
  void set_sample_rate(int val) { this->sample_rate_ = val; }
  void set_cooldown_ms(int val) { this->cooldown_ms_ = val; }

  void set_self_triggered(bool val) { this->self_triggered_ = val; }
  bool is_self_triggered() const { return this->self_triggered_; }

  void set_paused(bool val) { this->paused_ = val; }
  bool is_paused() const { return this->paused_; }

  void start_calibration();
  CalibrationResult finish_calibration();

  void add_on_beep_detected_callback(std::function<void()> callback) {
    this->beep_detected_callback_.add(std::move(callback));
  }

 protected:
  /// Compute Goertzel magnitude for a given frequency over the sample buffer.
  float goertzel_magnitude(const int16_t *samples, int num_samples, float frequency);

  /// Process a chunk of audio samples.
  void process_audio(const int16_t *data, int num_samples);

  microphone::Microphone *mic_{nullptr};

  // Configuration
  float target_frequency_{4000.0f};
  float frequency_tolerance_{200.0f};
  float amplitude_min_{500.0f};
  float amplitude_max_{5000.0f};
  int min_duration_ms_{50};
  int max_duration_ms_{500};
  int sample_rate_{16000};
  int cooldown_ms_{5000};

  // State
  bool self_triggered_{false};
  bool paused_{false};
  bool beep_active_{false};
  uint32_t beep_start_time_{0};
  uint32_t last_beep_time_{0};

  // Calibration
  bool calibrating_{false};
  float cal_peak_frequency_{0.0f};
  float cal_peak_amplitude_{0.0f};
  static constexpr int CAL_FREQ_START = 1000;
  static constexpr int CAL_FREQ_END = 8000;
  static constexpr int CAL_FREQ_STEP = 100;

  // Audio buffer
  std::vector<int16_t> audio_buffer_;
  static constexpr int CHUNK_SIZE = 256;

  CallbackManager<void()> beep_detected_callback_;
};

class BeepDetectedTrigger : public Trigger<> {
 public:
  explicit BeepDetectedTrigger(BeepDetector *parent) {
    parent->add_on_beep_detected_callback([this]() { this->trigger(); });
  }
};

}  // namespace beep_detector
}  // namespace esphome
