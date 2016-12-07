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

The web application `openledger` is a simple Python/Django application which
passes through requests to partner APIs. API keys are stored outside of the
repo in environment variables or a local file. See `openledger/local.py.example` for
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

## Installation for development

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
postgres=# GRANT ALL PRIVILEGES ON DATABASE openledger to XXX;
GRANT
```

Per usual Django instructions, install the database tables:

```
python manage.py migrate
```

Open Ledger uses the database for caching at this time, so install those tables as well (migration don't install them automatically):

```
python manage.py createcachetable
```

## Instance configuration

### Elastic Beanstalk deployment

The application is already set up in EB. See the `open-ledger` Application and
`open-ledger-1` Environment in the EB console.

### EC2 Loader

Elastic Beanstalk spins up `t2.micro` web workers and a database host, but
at times it will be necessary to spin up purpose-built EC2 instances to perform
certain one-off tasks like these large loading jobs.

Fabric is set up to do a limited amount of management of these instances. You'll
need SSH keys that are registered with AWS:

```
fab launchloader
```

Will spin up a single instance of `INSTANCE_TYPE`, provision its packages, and
install the latest version of the code `from Github` (make sure local changes are pushed!)

The code will expect a number of environment variables to be set, including:

```
export OPEN_LEDGER_LOADER_AMI="XXX" # The AMI name
export OPEN_LEDGER_LOADER_KEY_NAME="XXX" # An SSH key name registered with Amazon
export OPEN_LEDGER_LOADER_SECURITY_GROUPS="default,open-ledger-loader"
export OPEN_LEDGER_REGION="us-west-1"
export OPEN_LEDGER_ACCOUNT="XXX"  # The AWS account for CC
export OPEN_LEDGER_ACCESS_KEY_ID="XXX" # Use an IAM that can reach these hosts, like 'cc-openledger'
export OPEN_LEDGER_SECRET_ACCESS_KEY="XXX"
```

...and most of the same Django-level configuration variables expected in `local.py.example`.
These values can be extracted from the Elastic Beanstalk config by using the AWS console.

## Open Images dataset

To include the Google-provided Open Images dataset from  https://github.com/openimages/dataset
you can either download the files locally (faster) or use the versions
on the CC S3 bucket (used by the AWS deployments)

1. Download the files linked as:

* Image URLs and metadata
* Human image-level annotations (validation set)

2. Run the database import script as a Django management command:

The script expects:

* Path to a data file (usually CSV)
* A 'source' label (the source of the dataset)
* An identifier of the object type (usual 'images' but potentially also 'tags' or files
that map images to tags.)

```
. venv/bin/activate

./manage.py loader /path/to/openimages/images_2016_08/validation/images.csv openimages images
./manage.py loader /path/to/openimages/dict.csv openimages tags
./manage.py loader /path/to/openimages/human_ann_2016_08/validation/labels.csv openimages image-tags
```

(This loads the smaller "validation" subject; the "train" files are the full 9 million set.)

This loader is invoked in production using the Fabric task, above:

```
fab launchloader --set datasource=openimages-small
```

See `fabfile.py` for complete documentation on loader tasks, including search engine indexing
and loading of other image sets.

## Development

### Python

Normal Django development applies:

* Run the app in development with `manage.py runserver`
* Handle database changes via `manage.py migrate`

JavaScript dependencies are managed with `npm` and built with `webpack`.
`Babel` is a dependency as the code is written in ES6+.

When JavaScript assets are changed, run webpack:

```
webpack
```

It is run automatically on deploy prior to a server-side call to `manage.py collectstatic`

## Testing

Install the testing dependencies:

```
pip install -r requirements-test.txt
```

Search tests require a local version of elasticsearch 2.x; install using your favorite
package manager.

```
./manage.py test
```
