1. Click Wireless in top right
2. Hover over Advanced Options
3. Press Edit Connections
4. Choose wireless connection and press Settings cog
5. Click IPv4 Settings tab
6. Change method to Manual
7. Determine IP
```
ip a
```
8. Determine Netmask
```
ifconfig | grep -i mask
```
9. Determine gateway
```
ip route | grep default
```
10. Set DNS to 1.1.1.1
11. Reboot Pi