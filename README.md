# Open Ledger prototype

This is an in-progress prototype for a consolidated "front-door" to the
Commons of visual imagery. The project has two near-term goals:

* Seek to understand the requirements for building out a fully-realized "ledger"
 of all known Commons works across multiple content providers.
* Provide a visually engaging prototype of what that front-door could be for
end users seeking to find licensable materials, and to understand how their
works have been re-used.

It is _not_ the goal of this project to:

* Produce "web-scale" code or implementations
* Replace or compete with content providers or partners. We seek to make
their works more visible, but defer to them for the hard work of generating,
promoting, and disseminating content.

Ancillary benefits of this project may include:

* A better understanding of the kinds of tooling we could provide to partners
that would allow them (or more often, their users) to integrate Commons-licensed
works into a larger whole. For example, APIs provided by Creative Commons that
surface CC-licensed images for inclusion in original writing.
* Early surfacing of the challenges inherent in integrating partners' metadata
into a coherent whole.
* Research into the feasibility of uniquely fingerprinting visual works
across multiple providers to identify and measure re-use -- there will be many
technical and privacy challenges here, and we seek to identify those early.

## Components

### Web app prototype

The web application `openledger` is a simple Python/Flask application which
passes through requests to partner APIs. API keys are stored outside of the
repo in `openledger/instance/config`. See `openledger/config.example` for
a snapshot of the current expected values.

This prototype is expected to grow to include works drawn directly from the
CommonsDB (see below), as well as direct API links to partners.

### CommonsDB

This is the backing store for the overall Open Ledger project: our own
collection of metadata about known CC (and later, PD) works, collected in
partnership with content providers and in methods consistent with their
terms of service. (We intend to store only metadata, not actual content
assets.)

The CommonsDB would be a point-in-time snapshot of the Commons _right now_,
as we know it. However, it would be possible to roll back to previous
snapshots (at least theoretically) using the Ledger, below.

### The Ledger

This is the idea of a transactional record of all changes to CC works:
items _enter_ the record, changes to metadata are recorded, and new
instances of that work appear on known partners. Right now this is purely
theoretical.

## Installation

* Python 3

```
pip install -r requirements
```

* JavaScript

Ensure that npm is installed. On Ubuntu, you will probably need:

```
ln -s /usr/bin/nodejs /usr/bin/node
```

Then:

```
npm install
```

* postgresql

Install header files and other dependencies. On Ubuntu:

```
sudo apt install libpq-dev python3-dev postgresql-client-common postgresql-contrib
```

Database setup should be similar to:
```
$ sudo -u postgres psql

postgres=# CREATE USER XXX WITH PASSWORD 'XXX';
CREATE ROLE
postgres=# create database openledger;
CREATE DATABASE
postgres=# GRANT ALL PRIVILEGES ON DATABASE "openledger" to XXX;
GRANT
```

## Instance configuration

Flask uses the `instance/config.py` file per-host to specify environment variables. For this application, most of these are going to be API keys or database configuration.

A sample is included in `config.py.example`. Copy that into `instance/config.py` and update the values for your host.

## Open Images dataset

To include the Google-provided Open Images dataset from  https://github.com/openimages/dataset

1. Download the files linked as:

* Image URLs and metadata
* Human image-level annotations (validation set)

(as of 11 Oct 16 we aren't yet including the machine annotations)

2. Run the database import script:

```
. venv/bin/activate
python database_import.py /path/to/images_2016_08/train/images.csv
python database_import.py /path/to/images_2016_08/validation/images.csv
```

(This loads 9 million image records; be patient!)

## Development

JavaScript dependencies are managed with `npm` and built with `webpack`.
`Babel` is a dependency as the code is written in ES6+.

When JavaScript assets are changed, run webpack:

```
webpack
```

It is run automatically on deploy.

## Testing

### Webapp

Run pytest from the root of the project as:

```
python -m pytest openledger
```
