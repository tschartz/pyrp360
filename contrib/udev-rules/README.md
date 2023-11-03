udev rules for Linux permission setup for the device files
==========================================================

On a modern Linux distribution, you can install the following file as
`/etc/udev/rules.d/70-pyrp360.rules` so that the `/dev/ttyACM${N}`
device for the RP360 or RP360XP is accessible from a non-priviledged
user running pyrp360:

```
# Digitech RP360/RP360XP Guitar Multi-Effect Floor Processor with USB Streaming
ACTION=="add", SUBSYSTEM=="tty", ATTRS{idVendor}=="1210", ATTRS{idProduct}=="0032", TAG+="uaccess"
```

If you want to use another access methods than `TAG+="uaccess"`, you
can rewrite the above rule according rule.
