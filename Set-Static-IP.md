1. Click Wireless in top right
2. Hover over Advanced Options
3. Press Edit Connections
4. Choose wireless connection and press Settings cog
5. Click IPv4 Settings tab
6. Change method to Manual
7. Set IP to 192.168.1.100
8. Set Netmask to 255.255.255.0
9. **TO DETERMINE GATEWAY:** Run command:
```
ip route | grep default
```
10. Set DNS to 1.1.1.1
11. Reboot Pi