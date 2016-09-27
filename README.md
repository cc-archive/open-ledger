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

## Testing

### Webapp

Run pytest from the root of the project as:

```
python -m pytest openledger
```
