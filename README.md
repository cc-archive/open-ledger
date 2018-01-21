# Creative Commons Search prototype

<a href="https://travis-ci.org/creativecommons/open-ledger"><img src="https://travis-ci.org/creativecommons/open-ledger.svg?branch=master" alt="build-status" /></a>

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

## Installation for development

### Docker

The easiest way to run the application is through [Docker Compose](https://docs.docker.com/compose/overview/). Install Docker, then run:

```
docker-compose up
```

If everything works, this should produce some help output:

```
docker-compose exec web python3 manage.py
```

### Elasticsearch

Create the elasticsearch index named `openledger`. You can change its name in `settings/openledger.py`.

```
curl -XPUT 'localhost:9200/openledger?pretty' -H 'Content-Type: application/json' -d
{
    "settings" : {
        "index" : {
            "number_of_shards" : 3,
            "number_of_replicas" : 2
        }
    }
}
'
```

### JavaScript

Ensure that `npm` is installed. On Ubuntu, you will probably need:

```
ln -s /usr/bin/nodejs /usr/bin/node
```

Then:

```
npm install
```

### postgresql

Create the database:

```
docker-compose exec db createdb -U postgres openledger
```

## Testing a development installation

Ensure all services are actually running: postgres, elasticsearch and that the `openledger` database has been created.

Build the JavaScript:

```
webpack
```

(If you installed it and it's not found, then check `node_modules/bin`)

Create some local configuration data by copying the example file:

```
cp openledger/local.py.example openledger/local.py
```

Specifically, change the following settings right away:

```
# Make this a long random string
SECRET_KEY = 'CHANGEME'

# Get these from the AWS config for your account
AWS_ACCESS_KEY_ID = 'CHANGEME'
AWS_SECRET_ACCESS_KEY = 'CHANGEME'

# Use the password you assigned when you created the local database user:
DATABASES = {
    'default': {
        'PASSWORD': 'CHANGEME',
        ...
      }
    }
```

Now the app should be able to talk to the database. Try this with:

```
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createcachetable
```

This should create the database tables. Everything should work locally, though you won't have any content yet.

## Testing

Verify that the test suite runs:

```
docker-compose exec python manage.py test
```

All tests should always pass. Tests assume that both Postgres and Elasticsearch are running locally.

Tests are set up to run automatically on master commits by Travis CI. When getting started with the app, it's still a good idea to run tests locally to avoid unnecessary pushes to master.

## Deployment

### Elastic Beanstalk deployment

Install the EC2 keypair associated with the Elastic Beanstalk instance (this will be shared privately among technical staff).

Install the AWS CLI tools: https://aws.amazon.com/cli/

In the openledger directory, run:

```
eb init
```

When you are ready to deploy, *run the tests first*.

If tests pass, *commit your changes locally to git*.

Then *deploy to staging*:

```
eb deploy open-ledger-2
```

Verify that your changes worked as expected on staging by *clicking the thing you changed*.

If that works out, deploy to production:

```
eb deploy open-ledger-1
```

Don't forget to push your changes upstream!

### EC2 Data Loader

At times it will be necessary to spin up purpose-built EC2 instances to perform
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
