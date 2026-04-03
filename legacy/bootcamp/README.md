# Boot Camp Driver Staging

Place Apple Boot Camp driver packages under:

```
bootcamp/drivers/
```

Then stage them onto a Windows installer USB with:

```
phoenix-cli windows-installer-usb \
  --disk PhysicalDrive1 \
  --source D:\Win11 \
  --drivers bootcamp/drivers \
  --execute --force --token PHX-...
```

Drivers will be copied to:
```
sources/$OEM$/$1/Drivers
```
