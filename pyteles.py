"""
This module implements a client for the Teles server.
"""
__all__ = ["TelesError", "TelesConnection", "TelesClient", "TelesSpace"]
__version__ = "0.1.0"
import logging
import socket
import errno


class TelesError(Exception):
    "Root of exceptions from the client library"
    pass


class TelesConnection(object):
    "Provides a convenient interface to server connections"
    def __init__(self, server, timeout, attempts=3):
        """
        Creates a new Teles Connection.

        :Parameters:
            - server: Provided as a string, either as "host" or "host:port" or "host:port:udpport".
                      Uses the default port of 2856 if none is provided for tcp.
            - timeout: The socket timeout to use.
            - attempts (optional): Maximum retry attempts on errors. Defaults to 3.
        """
        # Parse the host/port
        parts = server.split(":", 1)
        if len(parts) == 2:
            host, port = parts[0], int(parts[1])
        else:
            host, port = parts[0], 2856

        self.server = (host, port)
        self.timeout = timeout
        self.sock = None
        self.fh = None
        self.attempts = attempts
        self.logger = logging.getLogger("pyteles.TelesConnection.%s.%d" % self.server)

    def _create_socket(self):
        "Creates a new socket, tries to connect to the server"
        # Connect the socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        s.connect(self.server)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.fh = None
        return s

    def send(self, cmd):
        "Sends a command with out the newline to the server"
        if self.sock is None:
            self.sock = self._create_socket()
        sent = False
        for attempt in xrange(self.attempts):
            try:
                self.sock.sendall(cmd + "\n")
                sent = True
                break
            except socket.error, e:
                self.logger.exception("Failed to send command to teles server! Attempt: %d" % attempt)
                if e[0] in (errno.ECONNRESET, errno.ECONNREFUSED, errno.EAGAIN, errno.EHOSTUNREACH, errno.EPIPE):
                    self.sock = self._create_socket()
                else:
                    raise

        if not sent:
            self.logger.critical("Failed to send command to teles server after %d attempts!" % self.attempts)
            raise EnvironmentError("Cannot contact teles server!")

    def read(self):
        "Returns a single line from the file"
        if self.sock is None:
            self.sock = self._create_socket()
        if not self.fh:
            self.fh = self.sock.makefile()
        read = self.fh.readline().rstrip("\r\n")
        return read

    def readblock(self, start="START", end="END"):
        """
        Reads a response block from the server. The servers
        responses are between `start` and `end` which can be
        optionally provided. Returns an array of the lines within
        the block.
        """
        lines = []
        first = self.read()
        if first != start:
            raise TelesError("Did not get block start (%s)! Got '%s'!" % (start, first))
        while True:
            line = self.read()
            if line == end:
                break
            lines.append(line)
        return lines

    def send_and_receive(self, cmd):
        """
        Convenience wrapper around `send` and `read`. Sends a command,
        and reads the response, performing a retry if necessary.
        """
        done = False
        for attempt in xrange(self.attempts):
            try:
                self.send(cmd)
                return self.read()
            except socket.error, e:
                self.logger.exception("Failed to send command to teles server! Attempt: %d" % attempt)
                if e[0] in (errno.ECONNRESET, errno.ECONNREFUSED, errno.EAGAIN, errno.EHOSTUNREACH, errno.EPIPE):
                    self.sock = self._create_socket()
                else:
                    raise

        if not done:
            self.logger.critical("Failed to send command to teles server after %d attempts!" % self.attempts)
            raise EnvironmentError("Cannot contact teles server!")


class TelesClient(object):
    "Provides a client abstraction around the teles interface."
    def __init__(self, server="localhost", timeout=10):
        """
        Creates a new Teles client.

        :Parameters:
            - server : Provided as string in the "host" or "host:port" format. Defaults to localhost.
            - timeout: (Optional) A socket timeout to use, defaults to 10 seconds.
        """
        self.conn = TelesConnection(server, timeout)

    def __getitem__(self, name):
        "Gets a TelesSpace object based on the name."
        return TelesSpace(self.conn, name)

    def create_space(self, name):
        """
        Creates a new space on the Teles server and returns a TelesSpace
        to interface with it. This will return a TelesSpace object attached
        to the space if it already exists.

        :Parameters:
            - name : The name of the new space
        """
        cmd = "create space %s" % name
        resp = self.conn.send_and_receive(cmd)
        if resp == "Done":
            return TelesSpace(self.conn, name)
        raise TelesError("Got response: %s" % resp)

    def delete_space(self, name):
        cmd = "delete space %s" % name
        resp = self.conn.send_and_receive(cmd)
        if resp == "Done":
            return True
        if resp == "Space does not exist":
            return False
        raise TelesError("Got response: %s" % resp)

    def list_spaces(self):
        """
        Lists all the available spaces
        Returns a list of space's.
        """
        self.conn.send("list spaces")
        resp = self.conn.readblock()
        return resp



class TelesSpace(object):
    "Provides an interface to a single Teles space"
    def __init__(self, conn, name):
        """
        Creates a new TelesSpace object.

        :Parameters:
            - conn : The connection to use
            - name : The name of the space
        """
        self.conn = conn
        self.name = name
        self.prefix = "in %s " % self.name

    def _send(self, cmd):
        "Sends the command along with the exection prefix"
        return self.conn.send(self.prefix+cmd)

    def _send_recv(self, cmd):
        "Sends and receives with prefix"
        return self.conn.send_and_receive(self.prefix+cmd)

    def add(self, name):
        "Adds a new object"
        resp = self._send_recv("add object %s" % name)
        if resp == "Done":
            return True
        raise TelesError("Got response: %s" % resp)

    def delete(self, name):
        "Deletes an object"
        resp = self._send_recv("delete object %s" % name)
        if resp == "Done":
            return True
        if resp == "Object does not exist":
            return False
        raise TelesError("Got response: %s" % resp)

    def associate(self, name, lat, lng):
        "Associates an object with a lat/lng"
        resp = self._send_recv("associate point %f %f with %s" % (lat, lng, name))
        if resp == "Done":
            return True
        if resp == "Object does not exist":
            return False
        raise TelesError("Got response: %s" % resp)

    def disassociate(self, name, gid):
        "Disassociates an object with a GID"
        resp = self._send_recv("disassociate %s with %s" % (gid, name))
        if resp == "Done":
            return True
        if resp == "Object does not exist":
            return False
        if resp == "GID not associated":
            return False
        raise TelesError("Got response: %s" % resp)

    def list_objects(self):
        "List all objects in the space"
        self._send("list objects")
        return self.conn.readblock()

    def list_associations(self, name):
        "List object associations"
        self._send("list associations with %s" % name)
        associations = self.conn.readblock()
        results = []
        for line in associations:
            gid_s, lat_s, lng_s = line.split(" ")
            r = (gid_s[4:], (float(lat_s[4:]), float(lng_s[4:])))
            results.append(r)
        return dict(results)

    def query_within(self, min_lat, max_lat, min_lng, max_lng):
        "Queries within a bounding box"
        if min_lat > max_lat or min_lng > max_lng:
            raise TelesError("Minimum lat/lng must be less than maximum lat/lng!")
        self._send("query within %f %f %f %f" % (min_lat, max_lat, min_lng, max_lng))
        return self.conn.readblock()

    def query_around(self, lat, lng, distance, unit="mi"):
        "Queries around a point"
        if unit not in ("m", "km", "mi", "y", "ft"):
            raise TelesError("Bad unit provided!")
        if distance <= 0:
            raise TelesError("Bad distance provided!")
        self._send("query around %f %f for %f%s" % (lat, lng, distance, unit))
        return self.conn.readblock()

    def query_nearest(self, lat, lng, num):
        "Queries for nearest points around a lat/lng"
        if num <= 0:
            raise TelesError("Bad num provided!")
        self._send("query nearest %d to %f %f" % (num, lat, lng))
        return self.conn.readblock()

