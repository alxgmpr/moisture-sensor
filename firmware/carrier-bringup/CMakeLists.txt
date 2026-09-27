cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

# Production builds must opt in with a real signing key. The normal developer
# build intentionally keeps the SDK key so local builds remain reproducible,
# but this gate prevents that key from being used with the production profile.
if(DEFINED ENV{SENSOR_PRODUCTION_BUILD})
  if(NOT DEFINED CONFIG_MCUBOOT_SIGNATURE_KEY_FILE OR
     CONFIG_MCUBOOT_SIGNATURE_KEY_FILE STREQUAL "" OR
     CONFIG_MCUBOOT_SIGNATURE_KEY_FILE MATCHES "root-(rsa(-[0-9]+)?|ec(-p[0-9]+)?|ed25519)\\.pem$")
    message(FATAL_ERROR
      "SENSOR_PRODUCTION_BUILD requires CONFIG_MCUBOOT_SIGNATURE_KEY_FILE "
      "pointing to a protected non-SDK signing key")
  endif()
endif()

project(board_sensor)
target_sources(app PRIVATE src/main.c src/carrier.c src/bthome.c src/config.c src/config_service.c)
