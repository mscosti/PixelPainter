
class bmpReader:

    def __init__(self, file_path, brightness = 1, expected_width = None):
        self.file_path = file_path
        self.BRIGHTNESS = brightness
        self.expected_width = expected_width

    def read_le(self, s, ignore):
        result = 0
        shift = 0
        for byte in bytearray(s):
            result += byte << shift
            shift += 8
        return result

    def color_correct(self, color):
        correct = int(pow((color * self.BRIGHTNESS) / 255, 2.7) * 255 + 0.5)
        return correct
    
    def read_rows(self):
        try:
            with open(self.file_path, "rb") as f:
                print("File opened")
                if f.read(2) != b'BM':  # check signature
                    raise Exception("Not BitMap file")

                bmpFileSize = self.read_le(f.read(4),'big')
                f.read(4)  # Read & ignore creator bytes

                bmpImageoffset = self.read_le(f.read(4),'big')  # Start of image data
                headerSize = self.read_le(f.read(4),'big')
                bmpWidth = self.read_le(f.read(4),'big')
                bmpHeight = self.read_le(f.read(4),'big')

                print("Size: %d\nImage offset: %d\nHeader size: %d" %
                    (bmpFileSize, bmpImageoffset, headerSize))
                print("Width: %d\nHeight: %d" % (bmpWidth, bmpHeight))

                if self.expected_width and bmpWidth != self.expected_width:
                    raise Exception("Width: %d not equal to expected width: %d" %(bmpWidth, self.expected_width))

                if self.read_le(f.read(2),'big') != 1:
                    raise Exception("Not singleplane")
                bmpDepth = self.read_le(f.read(2),'big')  # bits per pixel
                print("Bit depth: %d" % (bmpDepth))
                if bmpDepth != 24:
                    raise Exception("Not 24-bit")
                if self.read_le(f.read(2),'big') != 0:
                    raise Exception("Compressed file")

                print("Image OK!")

                rowSize = (bmpWidth * 3 + 3)  # 32-bit line boundary
                print(rowSize)

                databuf = bytearray(bmpWidth * bmpHeight * 3)
                f.seek(bmpImageoffset)
                idx=0
                for row in range(bmpHeight):  # For each scanline...
                    for col in range(bmpWidth):
                        b, g, r = bytearray(f.read(3))  # BMP files store RGB in BGR

                        databuf[idx] = r
                        databuf[idx+1] = g
                        databuf[idx+2] = b
                        idx += 3
                    f.read(3) # read off last 3 padding bytes
                return (bmpWidth, bmpHeight, databuf)
        except Exception as e:
            raise e
    