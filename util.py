from PIL import Image
import colorsys
import numpy
import pytesseract
import re
import cv2
import easyocr


reader = easyocr.Reader(["en"])

def getDomColor(image):
    max_score = 0
    domColor = [0, 0, 0]
    for count, (r,g,b) in image.getcolors(image.size[0]*image.size[1]):
        (hue, sar,_) = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        y = min(abs(r*2104+g*4130+b*802+4096+131072 >> 13), 235)
        y = (y-16.0) / (235 - 16)
        if y > 0.9:
            continue
        if sar < 0.5:
            continue
        if hue > 60/360 and hue <= 180/360:
            domColor[1] += count
        elif hue > 180/360 and hue <= 300/360:
            domColor[2] += count
        else:
            domColor[0] += count
    domColor = numpy.array(domColor)
    return numpy.argmax(domColor)

def scanLineFillForFgo(npArray):
    color = 255
    npArray = npArray.astype(int)[5:-4, 5: -4]

    diffMatrix = numpy.diff(npArray)
    W2B = numpy.where(diffMatrix == -255)
    B2W = numpy.where(diffMatrix == 255)

    npArray[npArray == 0] = False
    npArray[npArray == 255] = True
    img = Image.fromarray(npArray.astype(bool)).convert("1")
    img.save("1.png")

    last = -1
    for a, b in zip(W2B[0], W2B[1]):
        if a != last:
            color = True
        last = a
        npArray[a, b + 1:] = color
        color = not color
    # if B2W[0].size > B2W[0].size:
    #     for i, j, k, l in zip(W2B[0], W2B[1], B2W[0][:-1], B2W[1][:-1]):
    #         npArray[k, l + 1:j + 1] = True
    #     npArray[B2W[0][-1], B2W[1][-1] + 1:] = True
    # else:
    #     for i, j, k, l in zip(W2B[0], W2B[1], B2W[0], B2W[1]):
    #         npArray[k, l + 1:j + 1] = True
    img = Image.fromarray(npArray.astype(bool)).convert("1")
    img.save("2.png")
    return img

def enHenceNum(img, name, detectLines: list=None):
    fillBg = True
    kernel = cv2.getStructuringElement(shape=cv2.MORPH_RECT, ksize=(2,2))
    # kernel2 = cv2.getStructuringElement(shape=cv2.MORPH_RECT, ksize=(1,2))
    img = cv2.erode(src=img, kernel=kernel, iterations=1)
    cv2.imwrite(f"./testImg/final/{name}_line.png", img)
    # img = cv2.dilate(src=img, kernel=kernel2, iterations=1)
    ret, labels = cv2.connectedComponents(img, connectivity=4)

    if fillBg:
        if detectLines is None:
            allLines = set(range(img.shape[0]))
            detectLines = []
            zoneNum = numpy.max(labels) + 1
            for i in range(zoneNum):
                lineIncludeZone = set(numpy.where(labels == i)[0])
                temp = allLines & lineIncludeZone
                if len(temp) > 0:
                    allLines = temp
                else:
                    detectLines.append(allLines.pop())
                    allLines = set(range(img.shape[0])) & lineIncludeZone
            detectLines.append(allLines.pop())

        for detectLine in detectLines:

            lastVisited = labels[detectLine][0]
            cv2.floodFill(img, mask=numpy.zeros((img.shape[0] + 2, img.shape[1] + 2), numpy.uint8), seedPoint=(0, detectLine),
                          newVal=0)
            visitedZone = {}
            visitedZone[labels[detectLine][0]] = True
            i = 0
            while lastVisited == labels[detectLine][0]:
                if i >= labels.shape[1]:
                    break
                lastVisited = labels[detectLine][i]
                i += 1
            if i >= labels.shape[1]:
                continue
            lineZone = labels[detectLine][i]
            lastVisited = -1
            fillColor = True
            for i, zone in enumerate(labels[detectLine].tolist()):
                if zone != lineZone and lastVisited == lineZone:
                    if zone in visitedZone:
                        fillColor = visitedZone[zone]
                    else:
                        fillColor = not fillColor
                if zone not in visitedZone and fillColor and zone != lineZone:
                    cv2.imwrite("before.png", img)
                    cv2.floodFill(img, mask=numpy.zeros((img.shape[0] + 2, img.shape[1] + 2), numpy.uint8), seedPoint=(i, detectLine),
                                  newVal=0)
                    cv2.imwrite("after.png", img)
                visitedZone[zone] = fillColor
                lastVisited = zone
    img = cv2.bitwise_not(img)
    return img

def getNum(image, threshold = 120, name=""):
    # gray = image.convert("L")
    # gray.save("gray.png")
    # gray2 = numpy.array(gray)
    # gray2[gray2 > 0] = 255

    # final = enHenceNum(gray2, name)
    # final = Image.fromarray(final).convert("1")
    # final.save(f"./testImg/final/{name}.png")

    result = list(reader.readtext(numpy.array(image)))
    result.sort(key=lambda x:x[2])
    if len(result) > 0:
        processed_result = re.sub(r"[^0-9oiIzOZgsSA%]", "", result[-1][1])
        processed_result = re.sub(r"[oO]", "0", processed_result)
        processed_result = re.sub(r"[A]", "4", processed_result)
        processed_result = re.sub(r"[sS]", "5", processed_result)
        processed_result = re.sub(r"[g]", "9", processed_result)
        processed_result = re.sub(r"[iI]", "1", processed_result)
        processed_result = re.sub(r"[zZ]", "2", processed_result)
    else:
        processed_result = ""
    try:
        if processed_result.endswith("%"):
            return float(processed_result[:-1]) / 100
        else:
            return 0.0
    except ValueError:
        return 0.0


if __name__ == '__main__':
    for i in range(20):
        img = Image.open(r"D:\PycharmProjects\AutoFGO\testImg\star\{}.png".format(i+1))
        print(f"{i+1}、", getNum(img, name=str(i+1)))
