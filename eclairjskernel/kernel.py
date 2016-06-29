import os
import signal
import sys
import time
import io
import json

from os import O_NONBLOCK, read
from fcntl import fcntl, F_GETFL, F_SETFL
from  subprocess import Popen, PIPE
from metakernel import MetaKernel
from py4j.java_gateway import JavaGateway, CallbackServerParameters, java_import
from py4j.protocol import Py4JError

class TextOutput(object):
    """Wrapper for text output whose repr is the text itself.
       This avoids `repr(output)` adding quotation marks around already-rendered text.
    """
    def __init__(self, output):
        self.output = output

    def __repr__(self):
        return self.output

class ForeachRDDListener(object):

    def __init__(self, kernel):
        self.kernel = kernel

    def call(self, comm_id, msg):
        m = None
        if isinstance(msg, str):
            try:
                m = json.loads(msg)
            except ValueError as e:
                m = TextOutput(msg)
        else:
            self.kernel.log.error("not string")
            m = msg

        self.kernel.comm_manager.get_comm(comm_id).send(m)
        return None

    class Java:
        implements = ['org.apache.spark.api.java.function.Function2']


class EclairJSKernel(MetaKernel):
    implementation = 'eclairjs_kernel'
    implementation_version = 0.1
    langauge = "javascript"
    language_version = "1.8"
    banner = "eclairjs"
    language_info = {'name': 'javascript',
                     'mimetype': 'application/javascript',
                     'file_extension': '.js'}

    _SPARK_COMMAND = '{}/bin/spark-submit'.format(os.environ['SPARK_HOME'])
    _ECLAIRJS_LOCATION = os.environ['ECLAIRJS_NASHORN_HOME']


    def __init__(self, **kwargs):
        super(EclairJSKernel, self).__init__(**kwargs)
        self.comm_manager.register_target('foreachrdd', self.comm_opened)
        self._start_eclairjs_server()

    def sig_handler(signum, frame):
        self.gateway_proc.terminate()

    def do_shutdown(self, restart):
        super(EclairJSKernel, self).do_shutdown(restart)
        self.gateway_proc.terminate()

    def _start_eclairjs_server(self):
        args = [
            self._SPARK_COMMAND,
            "--class",
            "org.eclairjs.nashorn.EclairJSGatewayServer",
            "--name",
            "EclairJSShell",
            self._ECLAIRJS_LOCATION
        ]

        self.gateway_proc = Popen(args, stderr=PIPE, stdout=PIPE)
        time.sleep(1.5)
        self.gateway = JavaGateway(
                start_callback_server=True,
                callback_server_parameters=CallbackServerParameters())

        flags = fcntl(self.gateway_proc.stdout, F_GETFL) # get current p.stdout flags
        fcntl(self.gateway_proc.stdout, F_SETFL, flags | O_NONBLOCK)

        flags = fcntl(self.gateway_proc.stderr, F_GETFL) # get current p.stdout flags
        fcntl(self.gateway_proc.stderr, F_SETFL, flags | O_NONBLOCK)

        signal.signal(signal.SIGTERM, self.sig_handler)
        signal.signal(signal.SIGINT, self.sig_handler)
        signal.signal(signal.SIGHUP, self.sig_handler)


    def comm_opened(self, comm, msg):
        self.log.error("comm opened " + comm.comm_id)
        cb = ForeachRDDListener(self)
        self.gateway.entry_point.registerCallback(cb)

    def Error(self, output):
        if not output:
            return
        
        super(EclairJSKernel, self).Error(output)
        """
        lines = [s.strip() for s in output.splitlines()]
        for l in lines:
            super(EclairJSKernel, self).Error(l.strip())
            try:
                l = l.decode('utf-8')
                level = l.split(' ')[2]
                if level == 'INFO':
                    self.log.info(l)
                elif level == 'WARN':
                    self.log.warn(l)
                elif level == 'ERROR':
                    self.log.error(l)
                elif level == 'FATAL':
                    self.log.fatal(l)
                else:
                    super(EclairJSKernel, self).Error(l)
            except:
                super(EclairJSKernel, self).Error(l)
        """


    def handle_output(self, fd, fn):
        stringIO = io.StringIO()
        while True:
            try:
                b = read(fd.fileno(), 1024)
                if b:
                    stringIO.write(b.decode('utf-8'))
            except OSError:
                break

        s = stringIO.getvalue()
        if s:
            fn(s.strip())

        stringIO.close()

    def do_execute_direct(self, code, silent=False):
        """
        :param code:
            The code to be executed.
        :param silent:
            Whether to display output.
        :return:
            Return value, or None

        MetaKernel code handler.
        """
        if not code.strip():
            return None

        retval = None
        try:
            retval = self.gateway.entry_point.eval(code.rstrip())
            self.handle_output(self.gateway_proc.stdout, self.Print)
            self.handle_output(self.gateway_proc.stderr, self.Error)
        except Py4JError as e:
            if not silent:
                self.Error(e.cause)

        if retval is None:
            return
        elif isinstance(retval, str):
            return TextOutput(retval)
        else:
            return retval
