import json
from hwtypes import BitVector, Bit
import os


class WaveForm(dict):
    def __init__(self, fields, clock_name=""):
        if clock_name:
            self[clock_name] = []
        self.clock_name = clock_name
        for field in fields:
            self[field] = []

    def step(self, obj):
        self[self.clock_name].append(True)
        for field in self:
            if field == self.clock_name:
                continue
            self[field].append(getattr(obj, field))
        # self[self.clock_name].append(1)
        # for field in self:
        #     if field == self.clock_name:
        #         continue
        #     self[field].append(getattr(obj, field))

    def get_last_non_dot(self, wave):
        for i in reversed(range(len(wave))):
            if wave[i] != ".":
                return wave[i]
        raise Exception(f"Could not get last non dot of \"{wave}\"")

    def to_wavejson(self):
        top = {"signal": []}
        for field, value in self.items():
            wave = ""
            data = []
            for v in value:
                if field == self.clock_name:
                    if not wave:
                        wave += "p"
                    else:
                        wave += "."
                elif isinstance(v, int) and v in [0, 1] or isinstance(v, Bit):
                    if isinstance(v, Bit):
                        v = int(bool(v))
                    if not wave or str(v) != self.get_last_non_dot(wave):
                        wave += str(v)
                    else:
                        wave += "."
                elif isinstance(v, BitVector):
                    str_val = str(hex(v.as_uint()))
                    if not wave or data[-1] != str_val:
                        wave += "="
                        data.append(str_val)
                    else:
                        wave += "."
                else:
                    raise NotImplementedError(v, type(v))
            signal = {"name": field, "wave": wave}
            if data:
                signal["data"] = data
            top["signal"].append(signal)
        return json.dumps(top, indent=4)

    def render_html(self):
        json_str = self.to_wavejson()
        return f"""\
<html>
    <header>
        <script src="http://wavedrom.com/skins/default.js" type="text/javascript"></script>
        <script src="http://wavedrom.com/wavedrom.min.js" type="text/javascript"></script>
    </header>
    <body onload="WaveDrom.ProcessAll()">
        <center>
            <script type="WaveDrom">
{json_str}
            </script>
        <center>
    </body>
</html>
"""

    def render_ipynb(self, image_name):
        import requests
        r = requests.post(f"http://wavedrom.craftware.info/rest/generate_link", data=self.to_wavejson())  # noqa
        import urllib.request as req
        image_file = f"images/{image_name}.png"
        req.urlretrieve(r.text, image_file)
        from IPython.display import Image
        return Image(filename=image_file)

    def render(self, filenaem="waveform.html"):
        with open("waveform.html", "w") as f:
            f.write(self.render_html())
        os.system("open waveform.html")
