import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import automation
from esphome.components import microphone
from esphome.const import CONF_ID, CONF_MICROPHONE_ID

DEPENDENCIES = ["microphone"]
CODEOWNERS = ["@nnuntanirund"]

CONF_TARGET_FREQUENCY = "target_frequency"
CONF_FREQUENCY_TOLERANCE = "frequency_tolerance"
CONF_AMPLITUDE_MIN = "amplitude_min"
CONF_AMPLITUDE_MAX = "amplitude_max"
CONF_MIN_DURATION_MS = "min_duration_ms"
CONF_MAX_DURATION_MS = "max_duration_ms"
CONF_SAMPLE_RATE = "sample_rate"
CONF_COOLDOWN_MS = "cooldown_ms"
CONF_ON_BEEP_DETECTED = "on_beep_detected"

beep_detector_ns = cg.esphome_ns.namespace("beep_detector")
BeepDetector = beep_detector_ns.class_("BeepDetector", cg.Component)
BeepDetectedTrigger = beep_detector_ns.class_(
    "BeepDetectedTrigger", automation.Trigger.template()
)

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(BeepDetector),
        cv.Required(CONF_MICROPHONE_ID): cv.use_id(microphone.Microphone),
        cv.Optional(CONF_TARGET_FREQUENCY, default=4000.0): cv.float_,
        cv.Optional(CONF_FREQUENCY_TOLERANCE, default=200.0): cv.float_,
        cv.Optional(CONF_AMPLITUDE_MIN, default=500.0): cv.float_,
        cv.Optional(CONF_AMPLITUDE_MAX, default=5000.0): cv.float_,
        cv.Optional(CONF_MIN_DURATION_MS, default=50): cv.int_range(min=10, max=5000),
        cv.Optional(CONF_MAX_DURATION_MS, default=500): cv.int_range(min=10, max=10000),
        cv.Optional(CONF_SAMPLE_RATE, default=16000): cv.int_,
        cv.Optional(CONF_COOLDOWN_MS, default=5000): cv.int_range(min=0, max=30000),
        cv.Optional(CONF_ON_BEEP_DETECTED): automation.validate_automation(
            {
                cv.GenerateID(): cv.declare_id(BeepDetectedTrigger),
            }
        ),
    }
).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    mic = await cg.get_variable(config[CONF_MICROPHONE_ID])
    cg.add(var.set_microphone(mic))

    cg.add(var.set_target_frequency(config[CONF_TARGET_FREQUENCY]))
    cg.add(var.set_frequency_tolerance(config[CONF_FREQUENCY_TOLERANCE]))
    cg.add(var.set_amplitude_min(config[CONF_AMPLITUDE_MIN]))
    cg.add(var.set_amplitude_max(config[CONF_AMPLITUDE_MAX]))
    cg.add(var.set_min_duration_ms(config[CONF_MIN_DURATION_MS]))
    cg.add(var.set_max_duration_ms(config[CONF_MAX_DURATION_MS]))
    cg.add(var.set_sample_rate(config[CONF_SAMPLE_RATE]))
    cg.add(var.set_cooldown_ms(config[CONF_COOLDOWN_MS]))

    for conf in config.get(CONF_ON_BEEP_DETECTED, []):
        trigger = cg.new_Pvariable(conf[CONF_ID], var)
        await automation.build_automation(trigger, [], conf)
