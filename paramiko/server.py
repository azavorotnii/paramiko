#!/usr/bin/python

# Copyright (C) 2003-2004 Robey Pointer <robey@lag.net>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distrubuted in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

"""
L{ServerInterface} is an interface to override for server support.
"""

import threading
from common import *
import util
from transport import BaseTransport
from auth_transport import Transport

class ServerInterface (object):
    """
    This class defines an interface for controlling the behavior of paramiko
    in server mode.

    Methods on this class are called from paramiko's primary thread, so you
    shouldn't do too much work in them.  (Certainly nothing that blocks or
    sleeps.)
    """

    def check_channel_request(self, kind, chanid):
        """
        Determine if a channel request of a given type will be granted, and
        return C{OPEN_SUCCEEDED} or an error code.  This method is
        called in server mode when the client requests a channel, after
        authentication is complete.

        If you allow channel requests (and an ssh server that didn't would be
        useless), you should also override some of the channel request methods
        below, which are used to determine which services will be allowed on
        a given channel:
            - L{check_channel_pty_request}
            - L{check_channel_shell_request}
            - L{check_channel_subsystem_request}
            - L{check_channel_window_change_request}

        The C{chanid} parameter is a small number that uniquely identifies the
        channel within a L{Transport}.  A L{Channel} object is not created
        unless this method returns C{OPEN_SUCCEEDED} -- once a
        L{Channel} object is created, you can call L{Channel.get_id} to
        retrieve the channel ID.

        The return value should either be C{OPEN_SUCCEEDED} (or
        C{0}) to allow the channel request, or one of the following error
        codes to reject it:
            - C{OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED}
            - C{OPEN_FAILED_CONNECT_FAILED}
            - C{OPEN_FAILED_UNKNOWN_CHANNEL_TYPE}
            - C{OPEN_FAILED_RESOURCE_SHORTAGE}
        
        The default implementation always returns
        C{OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED}.

        @param kind: the kind of channel the client would like to open
        (usually C{"session"}).
        @type kind: str
        @param chanid: ID of the channel, required to create a new L{Channel}
        object.
        @type chanid: int
        @return: a success or failure code (listed above).
        @rtype: int
        """
        return OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username):
        """
        Return a list of authentication methods supported by the server.
        This list is sent to clients attempting to authenticate, to inform them
        of authentication methods that might be successful.

        The "list" is actually a string of comma-separated names of types of
        authentication.  Possible values are C{"password"}, C{"publickey"},
        and C{"none"}.

        The default implementation always returns C{"password"}.

        @param username: the username requesting authentication.
        @type username: str
        @return: a comma-separated list of authentication types
        @rtype: str
        """
        return 'password'

    def check_auth_none(self, username):
        """
        Determine if a client may open channels with no (further)
        authentication.

        Return L{AUTH_FAILED} if the client must authenticate, or
        L{AUTH_SUCCESSFUL} if it's okay for the client to not
        authenticate.

        The default implementation always returns L{AUTH_FAILED}.

        @param username: the username of the client.
        @type username: str
        @return: L{AUTH_FAILED} if the authentication fails;
        L{AUTH_SUCCESSFUL} if it succeeds.
        @rtype: int
        """
        return AUTH_FAILED

    def check_auth_password(self, username, password):
        """
        Determine if a given username and password supplied by the client is
        acceptable for use in authentication.

        Return L{AUTH_FAILED} if the password is not accepted,
        L{AUTH_SUCCESSFUL} if the password is accepted and completes
        the authentication, or L{AUTH_PARTIALLY_SUCCESSFUL} if your
        authentication is stateful, and this key is accepted for
        authentication, but more authentication is required.  (In this latter
        case, L{get_allowed_auths} will be called to report to the client what
        options it has for continuing the authentication.)

        The default implementation always returns L{AUTH_FAILED}.

        @param username: the username of the authenticating client.
        @type username: str
        @param password: the password given by the client.
        @type password: str
        @return: L{AUTH_FAILED} if the authentication fails;
        L{AUTH_SUCCESSFUL} if it succeeds;
        L{AUTH_PARTIALLY_SUCCESSFUL} if the password auth is
        successful, but authentication must continue.
        @rtype: int
        """
        return AUTH_FAILED

    def check_auth_publickey(self, username, key):
        """
        Determine if a given key supplied by the client is acceptable for use
        in authentication.  You should override this method in server mode to
        check the username and key and decide if you would accept a signature
        made using this key.

        Return L{AUTH_FAILED} if the key is not accepted,
        L{AUTH_SUCCESSFUL} if the key is accepted and completes the
        authentication, or L{AUTH_PARTIALLY_SUCCESSFUL} if your
        authentication is stateful, and this key is accepted for
        authentication, but more authentication is required.  (In this latter
        case, L{get_allowed_auths} will be called to report to the client what
        options it has for continuing the authentication.)

        The default implementation always returns L{AUTH_FAILED}.

        @param username: the username of the authenticating client.
        @type username: str
        @param key: the key object provided by the client.
        @type key: L{PKey <pkey.PKey>}
        @return: L{AUTH_FAILED} if the client can't authenticate
        with this key; L{AUTH_SUCCESSFUL} if it can;
        L{AUTH_PARTIALLY_SUCCESSFUL} if it can authenticate with
        this key but must continue with authentication.
        @rtype: int
        """
        return AUTH_FAILED


    ###  Channel requests


    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight,
                                  modes):
        """
        Determine if a pseudo-terminal of the given dimensions (usually
        requested for shell access) can be provided on the given channel.

        The default implementation always returns C{False}.

        @param channel: the L{Channel} the pty request arrived on.
        @type channel: L{Channel}
        @param term: type of terminal requested (for example, C{"vt100"}).
        @type term: str
        @param width: width of screen in characters.
        @type width: int
        @param height: height of screen in characters.
        @type height: int
        @param pixelwidth: width of screen in pixels, if known (may be C{0} if
        unknown).
        @type pixelwidth: int
        @param pixelheight: height of screen in pixels, if known (may be C{0}
        if unknown).
        @type pixelheight: int
        @return: C{True} if the psuedo-terminal has been allocated; C{False}
        otherwise.
        @rtype: boolean
        """
        return False

    def check_channel_shell_request(self, channel):
        """
        Determine if a shell will be provided to the client on the given
        channel.  If this method returns C{True}, the channel should be
        connected to the stdin/stdout of a shell (or something that acts like
        a shell).

        The default implementation always returns C{False}.

        @param channel: the L{Channel} the pty request arrived on.
        @type channel: L{Channel}
        @return: C{True} if this channel is now hooked up to a shell; C{False}
        if a shell can't or won't be provided.
        @rtype: boolean
        """
        return False

    def check_channel_subsystem_request(self, channel, name):
        """
        Determine if a requested subsystem will be provided to the client on
        the given channel.  If this method returns C{True}, all future I/O
        through this channel will be assumed to be connected to the requested
        subsystem.  An example of a subsystem is C{sftp}.

        The default implementation checks for a subsystem handler assigned via
        L{Transport.set_subsystem_handler <BaseTransport.set_subsystem_handler>}.
        If one has been set, the handler is invoked and this method returns
        C{True}.  Otherwise it returns C{False}.

        @note: Because the default implementation uses the L{Transport} to
        identify valid subsystems, you probably won't need to override this
        method.

        @param channel: the L{Channel} the pty request arrived on.
        @type channel: L{Channel}
        @param name: name of the requested subsystem.
        @type name: str
        @return: C{True} if this channel is now hooked up to the requested
        subsystem; C{False} if that subsystem can't or won't be provided.
        @rtype: boolean
        """
        handler_class, larg, kwarg = channel.get_transport()._get_subsystem_handler(name)
        if handler_class is None:
            return False
        handler = handler_class(channel, name, *larg, **kwarg)
        handler.start()
        return True

    def check_channel_window_change_request(self, channel, width, height, pixelwidth, pixelheight):
        """
        Determine if the pseudo-terminal on the given channel can be resized.
        This only makes sense if a pty was previously allocated on it.

        The default implementation always returns C{False}.

        @param channel: the L{Channel} the pty request arrived on.
        @type channel: L{Channel}
        @param width: width of screen in characters.
        @type width: int
        @param height: height of screen in characters.
        @type height: int
        @param pixelwidth: width of screen in pixels, if known (may be C{0} if
        unknown).
        @type pixelwidth: int
        @param pixelheight: height of screen in pixels, if known (may be C{0}
        if unknown).
        @type pixelheight: int
        @return: C{True} if the terminal was resized; C{False} if not.        
        """
        return False


class SubsystemHandler (threading.Thread):
    """
    Handler for a subsytem in server mode.  If you create a subclass of this
    class and pass it to
    L{Transport.set_subsystem_handler <BaseTransport.set_subsystem_handler>},
    an object of this
    class will be created for each request for this subsystem.  Each new object
    will be executed within its own new thread by calling L{start_subsystem}.
    When that method completes, the channel is closed.

    For example, if you made a subclass C{MP3Handler} and registered it as the
    handler for subsystem C{"mp3"}, then whenever a client has successfully
    authenticated and requests subsytem C{"mp3"}, an object of class
    C{MP3Handler} will be created, and L{start_subsystem} will be called on
    it from a new thread.

    @since: ivysaur
    """
    def __init__(self, channel, name):
        """
        Create a new handler for a channel.  This is used by L{ServerInterface}
        to start up a new handler when a channel requests this subsystem.  You
        don't need to override this method, but if you do, be sure to pass the
        C{channel} and C{name} parameters through to the original C{__init__}
        method here.

        @param channel: the channel associated with this subsystem request.
        @type channel: L{Channel}
        @param name: name of the requested subsystem.
        @type name: str
        """
        threading.Thread.__init__(self, target=self._run)
        self.__channel = channel
        self.__transport = channel.get_transport()
        self.__name = name

    def _run(self):
        try:
            self.__transport._log(DEBUG, 'Starting handler for subsystem %s' % self.__name)
            self.start_subsystem(self.__name, self.__transport, self.__channel)
        except Exception, e:
            self.__transport._log(ERROR, 'Exception in subsystem handler for "%s": %s' %
                                  (self.__name, str(e)))
            self.__transport._log(ERROR, util.tb_strings())
        try:
            self.finish_subsystem()
        except:
            pass

    def start_subsystem(self, name, transport, channel):
        """
        Process an ssh subsystem in server mode.  This method is called on a
        new object (and in a new thread) for each subsystem request.  It is
        assumed that all subsystem logic will take place here, and when the
        subsystem is finished, this method will return.  After this method
        returns, the channel is closed.

        The combination of C{transport} and C{channel} are unique; this handler
        corresponds to exactly one L{Channel} on one L{Transport}.

        @note: It is the responsibility of this method to exit if the
        underlying L{Transport} is closed.  This can be done by checking
        L{Transport.is_active <BaseTransport.is_active>} or noticing an EOF
        on the L{Channel}.
        If this method loops forever without checking for this case, your
        python interpreter may refuse to exit because this thread will still
        be running.

        @param name: name of the requested subsystem.
        @type name: str
        @param transport: the server-mode L{Transport}.
        @type transport: L{Transport}
        @param channel: the channel associated with this subsystem request.
        @type channel: L{Channel}
        """
        pass

    def finish_subsystem(self):
        """
        Perform any cleanup at the end of a subsystem.  The default
        implementation just closes the channel.

        @since: 1.1
        """
        self.__channel.close()