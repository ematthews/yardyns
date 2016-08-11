yardyns
=======

Yet Another Route 53 Dynamic DNS Updater (YAR! DNS)

This Python script will allow you to update a specific 'A' record in Amazon Route 53 to either a specified IP address on the command line or the public facing IP of the host.

_This will only work when there is an EXISTING 'A' record defined in a Route 53 zone/domain AND the record contains one and only one value._

Installation
------------
(Tested on Fedora 20 with Python 2.7.5)

* Ensure the following modules are installed:
    * boto: Used to interface with Amazon AWS. `pip install boto`

* Copy the configuration sample to a new file. `cp config.ini.sample config.ini`

* Update the values in config.ini to their appropriate values

* Execute the command using `python yardns.py -c config.ini`


