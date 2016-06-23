import subprocess
import os
import sys
from metakernel import MetaKernel
import pexpect
from py4j.java_gateway import JavaGateway, CallbackServerParameters, java_import
#from py4j.clientserver import ClientServer, JavaParameters, PythonParameters

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

    def __init__(self, comm):
        self.comm = comm

    def on_rdd(self, msg):
        self.comm.send(msg)
        return None

    class Java:
        implements = ['org.eclairjs.nashorn.IForeachRDD']


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

    class Java:
        implements = ['org.eclairjs.nashorn.IForeachRDD']


    def __init__(self, **kwargs):
        super(EclairJSKernel, self).__init__(**kwargs)
        self.comm_manager.register_target('foreachrdd', self.comm_opened)
        self._start_eclairjs_server()

    def on_rdd(self, id, msg):
        self.log.error("got it " + id)
        self.comm_manager.get_comm(id).send(msg)

    def _start_eclairjs_server(self):
        #args = "{} --class org.eclairjs.nashorn.EclairJSGatewayServer --name EclairJSShell {}".format(self._SPARK_COMMAND, self._ECLAIRJS_LOCATION)
        args = "{} --class org.eclairjs.nashorn.EclairJSGatewayServer --name EclairJSShell --conf spark.driver.userClassPathFirst=true {}".format(self._SPARK_COMMAND, self._ECLAIRJS_LOCATION)

        self.log.error(args)
        self.gateway_proc = pexpect.spawnu(args)
        self.gateway_proc.expect("Gateway Server Started")
        self.gateway = JavaGateway(
                start_callback_server=True,
                callback_server_parameters=CallbackServerParameters(),
                python_server_entry_point=self)
        """
        try:
            clazz = self.gateway.jvm.java.lang.Thread.currentThread().getContextClassLoader().loadClass("org.eclairjs.nashorn.IForeachRDD")
            if clazz:
                self.log.error("clazz = " + clazz.getName())
            else:
                self.log.error("class not found")
        except Py4JError as e:
            self.log.error(e.cause)
        """
        #self.gateway = ClientServer(
        #        java_parameters=JavaParameters(),
        #        python_parameters=PythonParameters())

    def comm_opened(self, comm, msg):
        self.log.error("comm opened " + comm.comm_id)
        #listener = ForeachRDDListener(comm)
        #self.gateway.entry_point.registerForeachRDD(comm.comm_id,listener)
        pass

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
            #self.log.error("here")
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

