from pdf417 import encode, render_image, render_svg
import base64
from io import BytesIO


# Some data to encode
text = """<DD xmlns=\"http://www.sii.cl/SiiDte\"><RE>11111111-1</RE><TD>52</TD><F>97</F><FE>2020-12-16</FE><RR>83659400-2</RR><RSR>GenÃ©rico</RSR><MNT>44000</MNT><IT1>[PT003108] Nuez Con CÃ¡scara/ Inshell Wal</IT1><CAF version=\"1.0\"><DA><RE>76588454-3</RE><RS>DTEMITE LIMITADA</RS><TD>52</TD><RNG><D>1</D><H>50</H></RNG><FA>2016-07-06</FA><RSAPK><M>sH8h/4+7bUFGGxIk/4oAGZXNqORHHnUgkSlF7+EhF6fLtxUDZ5L7geHm48hX8AziucAGpZSDkE/IZCxvy+NYWw==</M><E>Aw==</E></RSAPK><IDK>100</IDK></DA><FRMA algoritmo=\"SHA1withRSA\">a8cGYqRIXwnFRTIaI8me3BVHCLWN0/8E5zSatOuc+DDevyy5aBxqk3PIEyVxtw/NzOqFkbCPvtvzIjAayt/GRg==</FRMA></CAF><TSTED>2021-01-04T09:31:48</TSTED></DD><FRMT algoritmo=\"SHA1withRSA\" xmlns=\"http://www.sii.cl/SiiDte\">pbyfs0Jcuv7P7XHLxWxAPfGfyDejHpSEe6lCzaXrVPS3OTY3xdB5JxhlvWaT4I55WyaTjO/1FMchrZ7bZN1m3w==</FRMT>"""


cols = 12
while True:
    try:
        if cols == 31:
            break
        # Convert to code words
        codes = encode(text, cols)

        # Generate barcode as image
        image = render_image(codes)  # Pillow Image object
        image.save("barcode.jpg")
        print(cols)
        break
    except:
        cols += 1


