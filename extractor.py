try:
    from PIL import Image
except ImportError:
    import Image

import pytesseract, sys, os

pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

class ocrCore():
    def __init__(self, imgPath, config, lang):
        self.img =  Image.open(imgPath)
        self.config = config
        self.lang = lang
    
    def getString(self, config=None, lang=None):
        ## This function will handle the core OCR processing of images.
        ## We'll use Pillow's Image class to open the image and pytesseract to detect the string in the image
        configTemp = self.config
        langTemp = self.lang
        if config != None: configTemp = config
        if lang != None: langTemp = lang
        return pytesseract.image_to_string(self.img, lang=langTemp, config=configTemp)
    
    def getData(self, config=None, lang=None):
        configTemp = self.config
        langTemp = self.lang
        if config != None: configTemp = config
        if lang != None: langTemp = lang
        return pytesseract.image_to_boxes(self.img, lang=langTemp, config=configTemp)
    
    def getBox(self, config=None, lang=None):
        configTemp = self.config
        langTemp = self.lang
        if config != None: configTemp = config
        if lang != None: langTemp = lang
        return pytesseract.image_to_boxes(self.img, lang=langTemp, config=configTemp)


print(pytesseract.get_languages())
path = os.path.join(sys.path[0], '5.jpg')
config = r'--oem 3 --psm 1'
lang='eng'
ocr = ocrCore(path, config, lang)
print(ocr.getString())
