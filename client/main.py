import numpy as np
import gi, redis, cv2
import os

gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
gi.require_version('GstApp', '1.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gst, GObject, GstApp, GstVideo

redis = redis.StrictRedis.from_url(os.environ['REDIS_URL'])


def redisSend(redis, key, value):
    try:
        print('sending to redis', redis.set(key, value))
    except Exception as e:
        print(str(e))


def on_message(bus: Gst.Bus, message: Gst.Message, loop: GObject.MainLoop):
    mtype = message.type
    """
        Gstreamer Message Types and how to parse
        https://lazka.github.io/pgi-docs/Gst-1.0/flags.html#Gst.MessageType
    """

    if mtype == Gst.MessageType.EOS:
        print('restarting stream')
    elif mtype == Gst.MessageType.STATE_CHANGED:
        pass
    elif mtype == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(err, debug)
    elif mtype == Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        print(err, debug)

    return True

i = 0
def on_buffer(appsink: GstApp.AppSink, data) -> Gst.FlowReturn:
    global i

    sample = appsink.pull_sample()

    if isinstance(sample, Gst.Sample):
        buf = sample.get_buffer()

        i += 1
        if i == int(os.environ['SEND_FRAME_INTERVAL']):
            buffer = buf.extract_dup(0, buf.get_size())
            redisSend(redis, "img", buffer)
            i = 0

        return Gst.FlowReturn.OK

    return Gst.FlowReturn.ERROR


GObject.threads_init()
Gst.init(None)

pipelineString = "v4l2src device={usb_device} \
              ! identity sync=true ! timeoverlay ! jpegenc \
              ! appsink name=sink emit-signals=true max-buffers=1 drop=true".format(usb_device=os.environ['USB_DEVICE'])

GObject.threads_init()
Gst.init(None)

pipeline = Gst.parse_launch(pipelineString)

appsink = pipeline.get_by_name("sink")
appsink.set_property("max-buffers", 20)  # prevent the app to consume huge part of memory
appsink.set_property('emit-signals', True)  # tell sink to emit signals
appsink.set_property('sync', False)  # no sync to make decoding as fast as possible

appsink.connect('new-sample', on_buffer, None)

bus = pipeline.get_bus()

bus.add_signal_watch()

pipeline.set_state(Gst.State.PLAYING)

loop = GObject.MainLoop()

bus.connect("message", on_message, loop)

print("starting gstreamer loop")

loop.run()

print("end of gstreamer loop")
