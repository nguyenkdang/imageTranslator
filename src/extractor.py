try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    import Image

import pytesseract, sys, os, cropper
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from google_trans_new import google_translator 
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

class ocrPanel():
    def __init__(self, img, lang, oem=3, psm=12):
        # img - image file
        # psm/oem - int defining the mode of text extraction oem(0-3), psm(0-13)
        # lang - string of language to extract (use pytesseract.get_languages() to get avaiilible languages)
        # readFromTop/Left - bool of which region to read from 
        self.img = img
        self.psm = psm
        self.oem = oem
        self.config = '--oem {} --psm {}'.format(self.oem, self.psm)
        self.lang = lang
        self.readFromTop = True
        self.readFromLeft = False
        self.data = pytesseract.image_to_data(self.img, lang=self.lang, config=self.config, output_type= pytesseract.Output.DICT)
    
    def getString(self):
        ## Use OCR processing on images and return string of extracted text
        # return - string of extracted text
        s = ''
        n = 0
        for i in range(len(self.data['text'])):
            if self.data['block_num'][i] != n:
                s += '\n'
                n += 1
            s += self.data['text'][i]
        return s
    
    def getData(self):
        ## Use OCR processing on images and return data of extracted text
        # return - dict of data from extracted text
        return self.data
    
    def getBox(self):
        ## Use OCR processing on images and return box of extracted letters
        # return - string of all letters and their image cordinates
        return pytesseract.image_to_boxes(self.img, lang=self.lang, config=self.config)
    
    def exportBoxes(self, conf= 90, exportPath = None):
        ## Exports a copy of the image with all the text detection boxes displayed
        # conf - int confidence level to consider extracted text usable
        # exportPath - String with custom export file path. If exportPath = None, will attempt to use the file name as a base for export name
        if exportPath == None: fn, fe = os.path.splitext(self.img.filename)
        else: fn, fe = os.path.splitext(exportPath)
        
        savePath = fn + '_' + str(self.oem) + '-' + str(self.psm) + fe        
        fig = plt.figure(frameon=False)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.imshow(self.img)
        ax.axis('off')
        data = self.data
        
        for i in range(len(data['text'])):
            if int(data['conf'][i]) < conf: continue 
            left = data['left'][i]
            top = data['top'][i]
            width = data['width'][i]
            height = data['height'][i]
            rect = patches.Rectangle((left, top), width, height, linewidth=1, edgecolor='r', facecolor='none')
            ax.add_patch(rect)
        
        plt.savefig(savePath, bbox_inches='tight', pad_inches=0.0, dpi=200)

    def alignBoxes(self, wordList, tolerance=0.33):     
        ## if text detection boxes are closed together align them according to reading style 
        # wordList - list of [left, top, width, height, word] representing text detection box
        # tolerance - percent of median box's dimension (width or height) that can be considered alignable
        # return - list of [left, top, width, height, word] representing text detection box
        base = 3 #height
        start = 1 #top
        if 'vert' in self.lang:
            base  = 2 #width
            start = 0 #left
        mPos = int(len(wordList)/2)
        if mPos == 0: return wordList
        median = [x[base] for x in sorted(wordList, key=lambda word: word[base])][mPos]
        medianTolerance = median * tolerance
        
        sortAlign = sorted(wordList, key=lambda word: word[start])
        SACopy = sortAlign
        
        while True:
            for i in range(len(sortAlign)):
                if i + 1 == len(sortAlign): continue 
                
                cur = SACopy[i][start]
                nxt = SACopy[i+1][start]
                if 'vert' in self.lang:
                    cur += SACopy[i+1][base]
                    nxt += SACopy[i+1][base]

                if nxt - cur == 0: continue
                if abs(nxt - cur) <= medianTolerance: SACopy[i+1][start] = SACopy[i][start]
            
            if SACopy == sortAlign: break
            else: sortAlign = SACopy
        
        return sortAlign
    
    def orderText(self, conf= 90):
        ## When using using certain psm (like 11 or 12) text extracted are unordered. Reorder the extracted text ordering depends on 'readfrom' class variables
        # return - list of ordered extracted text
        data = self.data
        wordList = []
        areaMax, leftMax, topMax = 0, 0, 0

        for i in range(len(data['text'])):
            if int(data['conf'][i]) < conf: continue 
            left, top, width, height = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            info = [left, top, width, height, data['text'][i]]

            if left > leftMax:          leftMax = left
            if top  > topMax:           topMax = top
            if width*height > areaMax:  areaMax = width*height
            
            wordList.append(info)
        
        areaMax   = 10**len(str(areaMax))
        leftMax   = 10**len(str(leftMax))
        topMax    = 10**len(str(topMax))
        
        wordList = self.alignBoxes(wordList)
        rank = []
        for i in range(len(wordList)):
            left = wordList[i][0]
            top  = wordList[i][1]
            area = wordList[i][2] * wordList[i][3]
            if not self.readFromTop:  top = topMax - top
            if not self.readFromLeft: left = leftMax - left
            
            if 'vert' in self.lang: l = ((left * topMax) + top)  * areaMax
            else:                   l = ((top * leftMax) + left) * areaMax
            
            l += area
            rank.append((l, wordList[i][4]))

        rank = [z[1] for z in sorted(rank, key=lambda word: word[0])]
        
        return rank

    def getBoxSize(self, conf=90):
        data = self.getData()
        minLeft   = float('inf')
        minTop    = float('inf')
        maxRight  = float('-inf')
        maxBottom = float('-inf')
        for i in range(len(data['text'])):
            if int(data['conf'][i]) >= conf:
                if data['left'][i] < minLeft: minLeft = data['left'][i] 
                if data['top'][i] < minTop: minTop = data['top'][i]
                if data['left'][i] + data['width'][i] > maxRight: maxRight = data['left'][i] + data['width'][i]
                if data['top'][i]  + data['height'][i] > maxBottom: maxBottom = data['top'][i]  + data['height'][i]
        if minLeft == float('inf'): return None
        return [minLeft, minTop, maxRight-minLeft, maxBottom-minTop]

    def getImage(self):
        #return - image file
        return self.img


class ocrPage(ocrPanel):
    def __init__(self, img, lang, oem=3, psm=12, exportCrop = False):
        exportPath = None
        if exportCrop:
            fn, fe = os.path.splitext(img.filename)
            #Create directory with same filename
            dirName = fn.split('\\')[-1]
            exportPath = os.path.join(os.path.dirname(fn), dirName ) 
            if not os.path.isdir(exportPath): 
                os.makedirs(exportPath) 
        
        self.imgMulti = cropper.getCrop(img, exportPath)
        self.panelMulti = [ocrPanel(image, lang, oem, psm) for image in self.imgMulti['image']]
        super().__init__(img, lang, oem, psm)
    
    def getDatas(self):
        # Get extracted text data of all cropped images
        ## return - list of all data from cropped images
        return [p.getData() for p in self.panelMulti]
    
    def getStrings(self):
        # Get extracted text of all cropped images
        ## return - list of all string from cropped images
        return [p.getString() for p in self.panelMulti]
    
    def getBoxes(self):
        # Get extracted text box information of all cropped images
        ## return - list of all box information from cropped images
        return [p.getBox() for p in self.panelMulti]
    
    def getBoxSizes(self, conf=90):
        return [p.getBoxSize(conf) for p in self.panelMulti]

    def exportAllBoxes(self, conf = 90):
        # Exports copies of the cropped images with all their text detection boxes displayed
        ## conf - int confidence level to consider extracted text usable

        fn, fe = os.path.splitext(self.img.filename)
        #Create directory with same filename
        dirName = fn.split('\\')[-1]
        exportPath = os.path.join(os.path.dirname(fn), dirName ) 
        if not os.path.isdir(exportPath): 
            os.makedirs(exportPath)

        for i in range(len(self.panelMulti)):
            name = os.path.join(exportPath, 'Box{}{}'.format(i,fe))
            self.panelMulti[i].exportBoxes(conf, name)
        print(fn, fe)
        
        return 0
    
    def orderAllText(self, conf=90):
        # Order text by where the cropped image is placed on the page and the reading
        # information. Order is done by page and then by panel.
        ## conf - int confidence level to consider extracted text usable
        ## return - list of extracted text by reading order

        leftMax = 10 ** len(str(max(self.imgMulti['left'])))
        topMax = 10 ** len(str(max(self.imgMulti['top'])))
        rank = []
        for i in range(len(self.imgMulti['image'])):
            left = self.imgMulti['left'][i]
            top = self.imgMulti['top'][i]
            if not self.readFromTop:  top = topMax - top
            if not self.readFromLeft: left = leftMax - left
            l = (top * leftMax) + left
            rank.append((l, i))

        allOrdered = []
        rank = [z[1] for z in sorted(rank, key=lambda word: word[0])]
        for i in rank:
            ordered = self.panelMulti[i].orderText(conf)
            if len(ordered) != 0: allOrdered.append(ordered)
        
        return allOrdered
    
    def splitter(self, text, n):
        if text == '': return []
        sectioned = text.split(' ')
        textBox = [sectioned[0]]
        i = 0
        curLineSize = 0
        for t in sectioned[1:]:
            tsize = len(t)
            if curLineSize + 1 + tsize <= int(len(text)/n):
                textBox[i] += ' ' + t
                curLineSize += 1 + tsize
            else:
                textBox.append(t)
                curLineSize = tsize
                i += 1
                
        return textBox        

    def cover(self, img, conf = 90):
        datas = self.getDatas()
        draw = ImageDraw.Draw(self.img)
        fontPath = "arial.ttf"
        toCrop = []
        
        for i in range(len(datas)):
            useful = False
            for c in datas[i]['conf']:
                if int(c) >= conf: useful = True
            if useful: toCrop.append(i)

        text = 'I will be the King of the pirates and candy'
        boxSizes = self.getBoxSizes(conf)
        for i in toCrop:
            l_off, t_off,width,height = boxSizes[i]
            #width, height = self.imgMulti['image'][i].size ##CHANGE
            left = l_off + self.imgMulti['left'][i]
            top = t_off + self.imgMulti['top'][i]
            x = translateList(self.panelMulti[i].orderText())
            text = x[1].strip()
            ratio = width/height

            #Find correct splitting amount
            prevRatio = float('inf')
            splitted = self.splitter(text, 1)
            split_base = text.split(' ')
            testFont = ImageFont.truetype(fontPath, size=12)
            n = 1
            while True:
                splitted_fo = self.splitter(text, n)
                wList = [testFont.getsize(x)[0] for x in splitted_fo]
                totH  = sum([testFont.getsize(x)[1] for x in splitted_fo])   
                maxW  = max(wList)
                maxWi = wList.index(maxW) 
                if (abs((maxW/totH) - ratio) > abs(prevRatio - ratio)) or (splitted == split_base and n != 1): break
                splitted  = splitted_fo
                prevRatio = maxW/totH
                prevMaxWi = maxWi
                n += 1

            #Find correct font size
            textSize = 1
            while True:
                foFont = ImageFont.truetype(fontPath, size=textSize)
                if (prevRatio >= ratio and foFont.getsize(splitted[prevMaxWi])[0] >= width) or +\
                   (prevRatio < ratio and foFont.getsize(splitted[prevMaxWi])[1] * (len(splitted)) >= height): break 
                font = foFont
                textSize+=1
            
            #Draw on image
            draw.rectangle((left, top, left + width, top + height), fill='white')
            topOffset = 0
            for x in splitted:
                draw.text((left, top + topOffset), x, fill='black', font=font)
                topOffset +=  foFont.getsize(x)[1]
        
        img.save(os.path.join(sys.path[0], '../output/translated.png'))


def translateList(textList, lang='en'):
    translator = google_translator()  
    combinedText = ''
    for t in textList:
        #if any(c.isalpha() for c in t):
        combinedText += t
        
    return (combinedText, translator.translate(combinedText,lang_tgt='en'))