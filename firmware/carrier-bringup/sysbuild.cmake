# Run the same board power policy before MCUboot's image validation and swap.
set(mcuboot_EXTRA_ZEPHYR_MODULES "${APP_DIR}/boot-guard" CACHE STRING
    "Board-specific MCUboot power gate")
