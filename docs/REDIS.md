# Redis Usage / Structure

Redis is used whenever *fast*, *ephemeral* or *realtime* storage is required that should be shared across all servers, like:

 * Django Sessions
 * Rooms
 * Video Feed Authentication
 * Live notifications
 * Communication between frontend/backend

## Rooms

All active rooms (whether they're online or not) are kept in Redis until they're archived.
When they're archived they're removed from Redis. For every broadcasting performer there 
may be two rooms - one for public and one for private.

In order to get events about a room the person must supply a the room token and a room access token.


