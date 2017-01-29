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

# Known issues
* Rocket.Chat requires MongoDB v2.6.0+ in order to run, rendering this inoperable with charm store's MongoDB
* No support for Mongo Replica Set as of yet. Couldn't get it working in testing, possible due to above limitation.
