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
        ## img - image file
        ## psm/oem - int defining the mode of text extraction oem(0-3), psm(0-13)
        ## lang - string of language to extract (use pytesseract.get_languages() to get avaiilible languages)
        ## readFromTop/Left - bool of which region to read from 
        self.img =  img
        self.psm = psm
        self.oem = oem
        self.lang = lang
        self.readFromTop = True
        self.readFromLeft = False
    
    def getString(self):
        # Use OCR processing on images and return string of extracted text
        ## return - string of extracted text
        config = '--oem {} --psm {}'.format(self.oem, self.psm)
        return pytesseract.image_to_string(self.img, lang=self.lang, config=config)
    
    def getData(self):
        # Use OCR processing on images and return data of extracted text
        ## return - dict of data from extracted text
        config = '--oem {} --psm {}'.format(self.oem, self.psm)
        return pytesseract.image_to_data(self.img, lang=self.lang, config=config, output_type= pytesseract.Output.DICT)
    
    def getBox(self):
        ## Use OCR processing on images and return box of extracted letters
        ## return - string of all letters and their image cordinates
        config = '--oem {} --psm {}'.format(self.oem, self.psm)
        return pytesseract.image_to_boxes(self.img, lang=self.lang, config=config)
    
    def exportBoxes(self, fnfe = None):
        # Exports a copy of the image with all the text detection boxes displayed
        ## fnfe - list/tuple where list[0] = file name and list[1] = file extension for export
        ##      - if fnfn = None, will attempt to use the file name as a base for export name
        if fnfe == None: fn, fe = os.path.splitext(self.img.filename)
        else: fn, fe = fnfe
        
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

    def alignBoxes(self, wordList, tolerance=0.05):
        # Align the cordinates of the text boxes so they can be ordered properly by orderText()
        ## wordList - list of words and their location info : [left, top, area, text]
        ## tolerance - float of amount of tolerance (higher tolerance = more aligning)
        ## return -  list of words and their location info : [left, top, area, text]
        width, height = self.img.size
        vh = 1
        size = height
        if 'vert' in self.lang: 
            vh = 0 
            size = width

        original = sorted(wordList, key=lambda word: word[vh]) 
        copy = sorted(wordList, key=lambda word: word[vh]) 
        n = len(original)
        
        while True:
            for i in range(n):
                if i + 1 == n: continue
                cur = copy[i][vh]
                nxt = copy[i+1][vh]
                pChange = (nxt - cur)/size
                #print(copy[i][3], '->', copy[i+1][3], pChange )
                if abs(pChange) == 0: continue
                if abs(pChange) <= tolerance: copy[i+1][vh] = cur
            
            if copy == original: break
            else: original = copy
        
        #print(original)
        return original

    def orderText(self):
        # When using using certain psm (like 11 or 12) text extracted are unordered. Reorder the extracted text
        # ordering depends on 'readfrom' class variables
        ## return - list of ordered extracted text
        data = self.getData()
        wordList = []
        areaAlign, leftAlign, topAlign = 0, 0 ,0

        for i in range(len(data['text'])):
            if int(data['conf'][i]) < 90: continue
            text = data['text'][i]
            left = data['left'][i]
            top = data['top'][i]
            area = data['width'][i] * data['height'][i]
            if left > leftAlign:    leftAlign = left
            if top  > topAlign:     topAlign = top
            if area > areaAlign:    areaAlign = area
            
            wordList.append([left, top, area, text])
        
        areaAlign   = 10**len(str(areaAlign))
        leftAlign   = 10**len(str(leftAlign))
        topAlign    = 10**len(str(topAlign))
        
        wordList = self.alignBoxes(wordList)
        rank = []
        for w in wordList:
            left = w[0]
            top = w[1]
            area = w[2]
            if not self.readFromTop:  top = topAlign - top
            if not self.readFromLeft: left = leftAlign - left
            
            if 'vert' in self.lang: l = ((left * topAlign) + top) * areaAlign
            else: l = ((top * leftAlign) + left) * areaAlign
            
            l += area
            rank.append((l, w[3]))
        
        rank = [z[1] for z in sorted(rank, key=lambda word: word[0])]
        return rank

    def getImage(self):
        #return - image file
        return self.img

if __name__ == "__main__":
    #print(pytesseract.get_languages())
    path = os.path.join(sys.path[0], 'raw6.png')
    ePath = os.path.join(sys.path[0], 'crop')
    img = Image.open(path)
    cropped = cropper.getCrop(img, ePath)
    lang='jpn_vert'
    translator = google_translator()  
    n = 0
    for i in cropped:
        print('bubble', n)
        ocr = ocrCore(i, lang, 3,  12)
        s = ocr.getString().strip()
        
        l = ocr.orderText()
        combined = ''
        
        for x in l:
            if any(c.isalpha() for c in x):
                combined += x
        
        print(l)
        print(combined)
        t = translator.translate(combined,lang_tgt='en')
        print(combined, '->',t)
        
        ocr.exportBoxes((os.path.join(ePath, str(n)), '.jpg'))
        n += 1
        print()
