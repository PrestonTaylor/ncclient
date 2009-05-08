# Copyright 2009 Shikhar Bhushan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from threading import Event
from Queue import Queue

from ncclient.capabilities import Capabilities
from ncclient.glue import Subject

from hello import HelloHandler

import logging
logger = logging.getLogger('ncclient.transport.session')

class Session(Subject):
    
    "TODO: docstring"
    
    def __init__(self, capabilities):
        "Subclass constructor should call this"
        Subject.__init__(self)
        self.setName('session')
        self._q = Queue()
        self._client_capabilities = capabilities
        self._server_capabilities = None # yet
        self._id = None # session-id
        self._connected = False # to be set/cleared by subclass implementation
        logger.debug('%r created: client_capabilities=%r' %
                     (self, self._client_capabilities))
    
    def _post_connect(self):
        "Greeting stuff"
        init_event = Event()
        error = [None] # so that err_cb can bind error[0]. just how it is.
        # callbacks
        def ok_cb(id, capabilities):
            self._id = id
            self._server_capabilities = Capabilities(capabilities)
            init_event.set()
        def err_cb(err):
            error[0] = err
            init_event.set()
        listener = HelloHandler(ok_cb, err_cb)
        self.add_listener(listener)
        self.send(HelloHandler.build(self._client_capabilities))
        logger.debug('starting main loop')
        self.start()
        # we expect server's hello message
        init_event.wait()
        # received hello message or an error happened
        self.remove_listener(listener)
        if error[0]:
            raise error[0]
        logger.info('initialized: session-id=%s | server_capabilities=%s' %
                     (self._id, self._server_capabilities))
    
    def connect(self, *args, **kwds):
        "Subclass implements"
        raise NotImplementedError

    def run(self):
        "Subclass implements"
        raise NotImplementedError
    
    def send(self, message):
        "TODO: docstring"
        logger.debug('queueing %s' % message)
        self._q.put(message)
    
    ### Properties
    
    @property
    def client_capabilities(self):
        return self._client_capabilities
    
    @property
    def server_capabilities(self):
        return self._server_capabilities
    
    @property
    def connected(self):
        return self._connected
    
    @property
    def id(self):
        return self._id
    
    @property
    def can_pipeline(self):
        return True