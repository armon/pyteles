pyteles
=======

Pyteles provides a Python client library to interface with
the teles server.

Install
--------

Download and install from source:

    python setup.py install


Example
------

Using pyteles is very simple::

    from pyteles import TelesClient

    # Create a client to the local server, default port
    cl = TelesClient("localhost")

    # Get the "people" space
    pp = cl["people"]

    # List objects
    people = pp.list_objects()

    # Add jane
    pp.add("jane")
    pp.associate("jane", 40.123, -120.120)

    # Find the 5 nearest people, should include jane
    nearby = pp.query_nearest(40.123, -120.120, 5)
    assert "jane" in nearby

