zephyr_library()
zephyr_library_sources_ifdef(CONFIG_SENSOR_BOOT_GUARD guard.c ../src/carrier.c)
zephyr_library_include_directories(../src)
