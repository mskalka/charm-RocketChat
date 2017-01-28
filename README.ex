# Overview
Deploys Rocket.Chat server with existing MongoDB instance


# Usage
```
juju deploy mongodb
juju deploy rocketchat
juju add-relation mongodb rocketchat
```
Optional configuration:
* host_url: Point to a domain you own
* port: Use a port other than 3000
