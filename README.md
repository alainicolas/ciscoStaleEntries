# ciscoStaleEntries

Small script using pyats and genie to check for stale entries in SUP/SDK on n9k. VXLAN F&L static ingress-rep

# Running the script

Just run python staleentry.py
Don't forget to setup testbed.pl and list_ip.yaml

## IP addresses of the devices

`ip addresses` are listed in `./templates/list_ip.yaml`

You can add more ip addresses by adding a new line, starting with a `-` followed by an IP address.

## Testbed

`testbed` template is described in `./templates/testbed.tpl`

You need to modify connections parameters such as the login or the passwords.
Line 5 and 6 are mandatory device credentials.
Line 9 to 18 are for jumphost, with line 14 beeing the jumphost username and line 18 the jumphost ip address.
Just remove the proxy parameter line 33 and 34 if you dont need it
