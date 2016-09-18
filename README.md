# mtconnect-dumper
Reads sample data from a typical `cppagent` and writes a series of timestamped XML files as read from the MTConnect agent.
Tries to get all data and repects the sequence numbering while doing it.

# Installation

## for development

Recommended way is using the `venv` module in in Python 3.4 (or later).
That version is used for development.
If you don't have tools ready to compile `lxml` from source, provide
a binary version from your distribution. The later switch `--system-site-packages`
gives the virtual environment access to it.
This is how it works:

``` 
$ python3 -V
Python 3.4.2
$ # Under Debian/Ubuntu/Raspbian, these are the useful system packages:
$ sudo apt-get install python3 python3-venv python3-lxml
$ python3 -m venv --system-site-packages venv
$ source venv/bin/activate
(venv) $ python3 -m pip install --editable .
```

## for production

Installing using `pip3` is recommended:

```
$ sudo python3 -m pip install .
$ which mtconnect_dumper
/usr/local/bin/mtconnect_dumper
```

## Running

```
(venv) $ sudo mkdir /var/lib/mtconnect_dumper && sudo chown $(whoami) /var/lib/mtconnect_dumper
(venv) $ mtconnect_dumper --url http://10.1.1.22:5000 --verbosity DEBUG /var/lib/mtconnect_dumper/
```

## Starting at system boot (systemd)

```
$ sudo cp mtconnect_dumper.service /etc/systemd/system/
$ sudo vim /etc/systemd/system/mtconnect_dumper.service # replace URL parameter!
$ sudo systemctl daemon-reload
$ sudo systemctl enable mtconnect_dumper.service
$ sudo systemctl start mtconnect_dumper.service
$ sudo systemctl status mtconnect_dumper.service -l
```

## Cleaning up

To avoid the XML files filling up all storage, consider using `lograted`:

```
$ sudo apt-get install -y logrotate
$ sudo cp mtconnect_dumper.logrotate /etc/logrotate.d/mtconnect_dumper
$ sudo /usr/sbin/logrotate -d /etc/logrotate.conf # mtconnect_dumper should be mentioned!
```
