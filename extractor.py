try:
    from PIL import Image
except ImportError:
    import Image

import pytesseract, sys, os, cv2, cropper
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from google_trans_new import google_translator 


pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

class ocrCore():
    def __init__(self, img, lang, oem=3, psm=12):
        self.img =  img
        self.psm = psm
        self.oem = oem
        self.lang = lang
        self.readFromTop = True
        self.readFromLeft = False
    
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
    
    def exportBoxes(self, fnfe = None):
        if fnfe == None:
            fn, fe = os.path.splitext(self.img.filename)
        else:
            fn, fe = fnfe
        savePath = fn + '_' + str(self.oem) + '-' + str(self.psm) + fe        
        fig = plt.figure(frameon=False)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.imshow(self.img)
        ax.axis('off')
        data = self.getData()
        for i in range(len(data['text'])):
            left = data['left'][i]
            top = data['top'][i]
            width = data['width'][i]
            height = data['height'][i]
            rect = patches.Rectangle((left, top), width, height, linewidth=1, edgecolor='r', facecolor='none')
            ax.add_patch(rect)
        
        plt.savefig(savePath, bbox_inches='tight', pad_inches=0.0, dpi=200)
    
    def alignBoxes(self, wordList, tolerance=0.01):
        return 0

    def orderText(self):
        data = self.getData()
        wordList = []
        maxArea = 0
        maxLeft = 0
        maxTop = 0
        
        for i in range(len(data['text'])):
            text = data['text'][i]
            if len(text) == 0: continue
            left = data['left'][i]
            top = data['top'][i]
            area = data['width'][i] * data['height'][i]
            if left > maxLeft: maxLeft = left
            if top > maxTop: maxTop = top
            if area > maxArea: maxArea = area
            

            wordList.append([left, top, area, text])
        
        maxArea = 10**len(str(maxArea))
        maxTop = 10**len(str(maxTop))
        maxLeft = 10**len(str(maxLeft))

        #print(wordList)

        rank = []
        for w in wordList:
            left = w[0]
            top = w[1]
            area = w[2]
            if not self.readFromTop: top = maxTop - top
            if not self.readFromLeft: left = maxLeft - left
            
            if 'vert' in self.lang:
                l = ((top * maxLeft) + left) * maxArea
            else:
                l = ((left * maxTop) + top) * maxArea
                
            
            l += area
            rank.append((l, w[3]))
        
        r = [z[1] for z in sorted(rank, key=lambda word: word[0])]
        #print(sorted(rank, key=lambda word: word[0]))
        #print(r)
        return r

    def getImage(self):
        return self.img

#print(pytesseract.get_languages())
path = os.path.join(sys.path[0], 'raw8.png')
ePath = os.path.join(sys.path[0], 'crop')
img = Image.open(path)
cropped = cropper.getCrop(img, ePath)
lang='jpn_vert'
translator = google_translator()  
n = 0
for i in cropped:
    print('bubble', n)
    ocr = ocrCore(i, lang, 3, 12)
    s = ocr.getString().strip()
    
    
    l = ocr.orderText()
    '''
    print(l)
    for x in l:
        t = translator.translate(x,lang_tgt='en')
        if any(c.isalpha() for c in x):
            print(x, '->', t)
    '''
    '''
    if s != '':
        for x in s.split('\n'):
            t = translator.translate(x,lang_tgt='en')
            if any(c.isalpha() for c in x):
                print(x, '->', t)
        #print(s)
    '''
    #x = ocr.getData()
    #print(x)
    #ocr.exportBoxes((os.path.join(ePath, str(n)), '.jpg'))
    n += 1
    print()
