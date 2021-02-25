try:
    from PIL import Image
except ImportError:
    import Image

import pytesseract, sys, os, cv2, cropper
import matplotlib.pyplot as plt
import matplotlib.patches as patches


pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

class ocrCore():
    def __init__(self, img, lang, oem=3, psm=12):
        self.img =  img
        self.psm = psm
        self.oem = oem
        self.lang = lang
    
    def getString(self):
        ## This function will handle the core OCR processing of images.
        ## We'll use Pillow's Image class to open the image and pytesseract to detect the string in the image
        config = '--oem {} --psm {}'.format(self.oem, self.psm)
        return pytesseract.image_to_string(self.img, lang=self.lang, config=config)
    
    def getData(self):
        config = '--oem {} --psm {}'.format(self.oem, self.psm)
        return pytesseract.image_to_data(self.img, lang=self.lang, config=config, output_type= pytesseract.Output.DICT)
    
    def getBox(self):
        config = '--oem {} --psm {}'.format(self.oem, self.psm)
        return pytesseract.image_to_boxes(self.img, lang=self.lang, config=config)
    
    def exportBoxes(self):
        fn, fe = os.path.splitext(self.img.filename)
        savePath = fn + '_' + str(self.oem) + '-' + str(self.psm) + fe        
        fig = plt.figure(frameon=False)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.imshow(self.img)
        ax.axis('off')
        data = self.getData()
        for i in range(len(data['text'])):
            #text = data['text'][i] 
            left = data['left'][i]
            top = data['top'][i]
            width = data['width'][i]
            height = data['height'][i]
            rect = patches.Rectangle((left, top), width, height, linewidth=1, edgecolor='r', facecolor='none')
            ax.add_patch(rect)
        
        plt.savefig(savePath, bbox_inches='tight', pad_inches=0.0, dpi=200)
    
    def getImage(self):
        return self.img

#print(pytesseract.get_languages())
path = os.path.join(sys.path[0], 'raw1.jpg')
ePath = os.path.join(sys.path[0], 'crop')
img = Image.open(path)
cropped = cropper.getCrop(img, ePath)
lang='jpn_vert'
for i in cropped:
    
    ocr = ocrCore(i, lang, 3, 12)
    s = ocr.getString().strip()
    if s != '':
        print(i)
        print(s)
    #x = ocr.getData()
    #print(x)
    #ocr.exportBoxes()
