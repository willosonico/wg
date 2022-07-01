import numpy as np
import gi, redis, cv2

gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
gi.require_version('GstApp', '1.0')
gi.require_version('GstVideo', '1.0')

from threading import Thread

from gi.repository import Gst, GObject, GstApp, GstVideo

redis = redis.StrictRedis.from_url('redis://:lol2@3.17.36.27')

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
    caps = sample.get_caps()
    caps_format = sample.get_caps().get_structure(0)

    if isinstance(sample, Gst.Sample):
        gstbuffer = sample.get_buffer()

        source_w = caps_format.get_value('width')
        source_h = caps_format.get_value('height')
        # print(source_w, source_h)
        H, W, C = source_h, source_w, 3
        image_array = np.ndarray(
            (H, W, C),
            buffer=gstbuffer.extract_dup(0, gstbuffer.get_size()),
            dtype=np.uint8
        )

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        retval, buffer = cv2.imencode('.jpg', image_array, encode_param)
        img1_bytes = np.array(buffer).tostring()

        i += 1
        if i == 10:
            redisSend(redis, "img", img1_bytes)
            i = 0

        # wrk = Thread(target=redisSend, args=[redis, "img", img1_bytes])
        # wrk.start()

        return Gst.FlowReturn.OK

    return Gst.FlowReturn.ERROR

GObject.threads_init()
Gst.init(None)

pipelineString = "v4l2src device=/dev/video11 \
              ! videoconvert ! videorate \
              ! video/x-raw,format=BGR,framerate=30/1  \
              ! appsink name=sink emit-signals=true max-buffers=1 drop=true"

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
