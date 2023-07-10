Changelog
=========

Pre-1.0 Releases
----------------

Before version 1.0, everything is experimental and can change at any time.

Version 0.5.5
~~~~~~~~~~~~~

Disregard field type when injecting

Version 0.5.4
~~~~~~~~~~~~~

Don't serialize injected fields

Version 0.5.3
~~~~~~~~~~~~~

Minor bug fixes

Version 0.5.2
~~~~~~~~~~~~~

Added missing support:

- Support for :code:`UnionType` (#52)
- Support for :code:`Literal` (#18)

Version 0.5.1
~~~~~~~~~~~~~

Released for CI/CD reasons but no code change.

Version 0.5.0
~~~~~~~~~~~~~

Modernization and feature

- Updated dependencies
- Support for more general types (:code:`Sequence` and :code:`Mapping`)
- Context injection into fitted objects

Version 0.4.2
~~~~~~~~~~~~~

Added a :code:`on_response` hook to the API client.

Version 0.4.1
~~~~~~~~~~~~~

Support for HTTP DELETE

Version 0.4.0
~~~~~~~~~~~~~

Mostly bug fixes.

- Move to httpx 0.22+
- Python 3.9 compatibility

Version 0.3.0
~~~~~~~~~~~~~

Focus on usability and correctness.

- Improved error reporting (#14)
- Simpler dependencies (#15)
- HTTPX update (#23)

Version 0.2.0
~~~~~~~~~~~~~

Better mapping back and forth between JSON and models.

- Custom data source for fields (#21)
- Serialization utilities (#22)

Version 0.1.1
~~~~~~~~~~~~~

Integrating contributions

- Support for enums (#8)

Version 0.1.0
~~~~~~~~~~~~~

First working version!
