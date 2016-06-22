import subprocess
import os
import sys
from metakernel import MetaKernel
#from metakernel import pexpect
import pexpect
from py4j.java_gateway import JavaGateway

class TextOutput(object):
    """Wrapper for text output whose repr is the text itself.
       This avoids `repr(output)` adding quotation marks around already-rendered text.
    """
    def __init__(self, output):
        self.output = output

    def __repr__(self):
        return self.output

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
        self.comm_manager.register_target('foreachrdd',
                handle_comm_opened)
        self._start_eclairjs_server()

    def _start_eclairjs_server(self):
        args = "{} --class org.eclairjs.nashorn.EclairJSGatewayServer --name EclairJSShell {}".format(self._SPARK_COMMAND, self._ECLAIRJS_LOCATION)

        self.gateway_proc = pexpect.spawnu(args)
        self.gateway_proc.expect("Gateway Server Started")
        """
        self.gateway_proc = subprocess.Popen([
                self._SPARK_COMMAND,
                "--class",
                "org.eclairjs.nashorn.EclairJSGatewayServer",
                "--name", 
                "EclairJSShell",
                self._ECLAIRJS_LOCATION
                ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
        """
        self._gateway = JavaGateway()

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
            retval = self._gateway.entry_point.eval(code.rstrip())
            self.gateway_proc.expect("eclairjs_done_execute")
            txt = self.gateway_proc.before
            if txt and txt.strip():
                self.Print(txt.strip())
            
        except Py4JError as e:
            if not silent:
                self.Error(e.cause)

        if not retval:
            return
        else:
            return TextOutput(retval)

